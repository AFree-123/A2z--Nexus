"""
Phase 15 — End-to-end integration tests.

These tests run against the full app stack (in-process, isolated DB).
They simulate a realistic developer workflow end-to-end:
  1. Create a project
  2. Send chat messages with various intents
  3. Trigger agent endpoints directly
  4. Verify notifications are created
  5. Verify analytics reflect the activity
  6. Verify reminders work
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.engine import Base, get_db
from main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        import database.models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def client():
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


USER = "e2e-developer"


# ---------------------------------------------------------------------------
# E2E Workflow 1: Developer asks a general technical question
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_e2e_information_query(client: AsyncClient):
    """User asks a technical question — Information Agent should respond."""
    resp = await client.post("/api/chat", json={
        "message": "What is the difference between REST and GraphQL?",
        "user_id": USER,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["content"]) > 20
    assert "session_id" in data
    assert "agents_used" in data
    # Information agent should be used
    assert "information" in data["agents_used"]


@pytest.mark.asyncio
async def test_e2e_reminder_detection(client: AsyncClient):
    """User mentions a deadline — Reminder Agent should detect it."""
    resp = await client.post("/api/chat", json={
        "message": "My project submission is next Friday.",
        "user_id": USER,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["content"]) > 10
    assert "reminder" in data["agents_used"]


# ---------------------------------------------------------------------------
# E2E Workflow 2: Full project creation and agent pipeline
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_e2e_create_project(client: AsyncClient):
    """Create a project and retrieve it."""
    resp = await client.post("/api/projects", json={
        "name": "Hackathon App",
        "description": "A2Z Nexus demo project",
        "technology": "FastAPI + React",
        "repository_path": ".",
        "user_id": USER,
        "deadline": "2024-12-06",
    })
    assert resp.status_code == 201
    p = resp.json()
    assert p["name"] == "Hackathon App"
    assert p["deadline"] == "2024-12-06"

    # Retrieve it
    get_resp = await client.get(f"/api/projects/{p['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == p["id"]


@pytest.mark.asyncio
async def test_e2e_project_analysis_pipeline(client: AsyncClient):
    """Create project → analyze → get recommendations → check submission."""
    # 1. Create project
    p = (await client.post("/api/projects", json={
        "name": "E2E Pipeline Project",
        "description": "Full pipeline test",
        "technology": "Python",
        "repository_path": ".",
        "user_id": USER,
    })).json()
    pid = p["id"]

    # 2. Analyze
    analyze_resp = await client.post("/api/analyze", json={"project_id": pid, "user_id": USER})
    assert analyze_resp.status_code == 200
    analysis = analyze_resp.json()
    assert "languages" in analysis or "error" in analysis

    # 3. Recommendations
    rec_resp = await client.post("/api/recommendations", json={"project_id": pid, "user_id": USER})
    assert rec_resp.status_code == 200
    recs = rec_resp.json()
    assert "recommendations" in recs or "error" in recs

    # 4. Submission check
    sub_resp = await client.post("/api/submission/check", json={"project_id": pid, "user_id": USER})
    assert sub_resp.status_code == 200
    sub = sub_resp.json()
    assert "readiness_percentage" in sub or "error" in sub

    # 5. Notifications should have been created
    notif_resp = await client.get(f"/api/notifications?user_id={USER}")
    assert notif_resp.status_code == 200
    notifications = notif_resp.json()
    assert len(notifications) >= 1

    # 6. Analytics should reflect the project
    analytics_resp = await client.get(f"/api/analytics?user_id={USER}")
    assert analytics_resp.status_code == 200
    analytics = analytics_resp.json()
    assert analytics["total_projects"] >= 1


# ---------------------------------------------------------------------------
# E2E Workflow 3: Chat with project context
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_e2e_chat_with_project_context(client: AsyncClient):
    """Create a project, then ask in chat with project context."""
    p = (await client.post("/api/projects", json={
        "name": "Context Project",
        "technology": "React",
        "user_id": USER,
    })).json()

    # Chat with project context
    resp = await client.post("/api/chat", json={
        "message": "Analyze my project",
        "project_id": p["id"],
        "user_id": USER,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["content"]) > 10
    # Should use code_analysis or orchestrator
    assert len(data["agents_used"]) >= 1


@pytest.mark.asyncio
async def test_e2e_multi_turn_conversation(client: AsyncClient):
    """Simulate a multi-turn conversation."""
    # First message
    r1 = await client.post("/api/chat", json={
        "message": "What is a Python decorator?",
        "user_id": USER,
    })
    assert r1.status_code == 200
    session_id = r1.json()["session_id"]

    # Follow-up using same session
    r2 = await client.post("/api/chat", json={
        "message": "Can you give me an example?",
        "session_id": session_id,
        "user_id": USER,
    })
    assert r2.status_code == 200
    assert r2.json()["session_id"] == session_id

    # Retrieve session history
    history = await client.get(f"/api/chat/sessions/{session_id}")
    assert history.status_code == 200
    messages = history.json()["messages"]
    assert len(messages) == 4  # 2 user + 2 assistant


# ---------------------------------------------------------------------------
# E2E Workflow 4: Documentation and content generation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_e2e_documentation_generation(client: AsyncClient):
    """Generate documentation for a project."""
    p = (await client.post("/api/projects", json={
        "name": "DocGen Project",
        "description": "A FastAPI application",
        "technology": "FastAPI",
        "user_id": USER,
    })).json()

    resp = await client.post("/api/documentation", json={
        "project_id": p["id"],
        "doc_type": "readme",
        "user_id": USER,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "content" in data or "error" in data
    if "content" in data:
        assert len(data["content"]) > 20


@pytest.mark.asyncio
async def test_e2e_content_generation(client: AsyncClient):
    """Generate hackathon submission content."""
    p = (await client.post("/api/projects", json={
        "name": "Hackathon Content",
        "description": "AI workspace",
        "technology": "Python",
        "user_id": USER,
    })).json()

    resp = await client.post("/api/content", json={
        "project_id": p["id"],
        "content_type": "elevator_pitch",
        "user_id": USER,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "content" in data or "error" in data


# ---------------------------------------------------------------------------
# E2E Workflow 5: Reminders
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_e2e_create_reminder(client: AsyncClient):
    """Create and list a reminder."""
    resp = await client.post("/api/reminders", json={
        "title": "Submit Hackathon Project",
        "description": "Final submission deadline",
        "due_date": "2024-12-06",
        "user_id": USER,
    })
    assert resp.status_code == 201
    reminder = resp.json()
    assert reminder["title"] == "Submit Hackathon Project"
    assert reminder["due_date"] == "2024-12-06"

    list_resp = await client.get(f"/api/reminders?user_id={USER}")
    assert list_resp.status_code == 200
    reminders = list_resp.json()
    assert any(r["title"] == "Submit Hackathon Project" for r in reminders)


# ---------------------------------------------------------------------------
# E2E Workflow 6: Notification read
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_e2e_notification_mark_read(client: AsyncClient):
    """Create a notification (via agent), then mark it as read."""
    # Trigger analysis to create a notification
    p = (await client.post("/api/projects", json={
        "name": "Notif Test Project",
        "user_id": USER,
    })).json()
    await client.post("/api/analyze", json={"project_id": p["id"], "user_id": USER})

    # Get notifications
    notifs = (await client.get(f"/api/notifications?user_id={USER}")).json()
    assert len(notifs) >= 1

    # Mark first unread notification as read
    unread = [n for n in notifs if not n["read"]]
    if unread:
        nid = unread[0]["id"]
        mark_resp = await client.patch(f"/api/notifications/{nid}/read")
        assert mark_resp.status_code == 200
        assert mark_resp.json()["read"] is True


# ---------------------------------------------------------------------------
# E2E Workflow 7: Release check
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_e2e_release_check(client: AsyncClient):
    """Run a release readiness check."""
    p = (await client.post("/api/projects", json={
        "name": "Release Test",
        "repository_path": ".",
        "user_id": USER,
    })).json()

    resp = await client.post("/api/release/check", json={"project_id": p["id"], "user_id": USER})
    assert resp.status_code == 200
    data = resp.json()
    assert "ready" in data or "error" in data
    if "ready" in data:
        assert isinstance(data["ready"], bool)
        assert "passed_checks" in data
        assert "blocking_issues" in data


# ---------------------------------------------------------------------------
# E2E Workflow 8: Full analytics after all activity
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_e2e_final_analytics(client: AsyncClient):
    """After all the E2E activity, analytics should reflect everything."""
    resp = await client.get(f"/api/analytics?user_id={USER}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_projects"] >= 3
    assert data["reminders_total"] >= 1
    assert data["recommendations_generated"] >= 0
