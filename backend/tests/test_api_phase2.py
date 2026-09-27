"""
Phase 2 smoke tests — Backend API Foundation.

Tests: health, projects CRUD, chat stub, notifications, reminders, analytics.
Uses an in-memory SQLite database so tests are isolated and fast.
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.engine import Base, get_db
from main import app

# ---------------------------------------------------------------------------
# Test DB setup — in-memory SQLite, isolated per test session
# ---------------------------------------------------------------------------
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create all tables once for the test session."""
    async with test_engine.begin() as conn:
        import database.models  # noqa: F401 — populate metadata
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    """AsyncClient with the test DB override applied."""
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
USER_ID = "test-user-001"


async def _create_project(client: AsyncClient, name: str = "Test Project") -> dict:
    resp = await client.post(
        "/api/projects",
        json={
            "name": name,
            "description": "A test project",
            "technology": "FastAPI",
            "user_id": USER_ID,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


# ---------------------------------------------------------------------------
# Projects CRUD
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    project = await _create_project(client, "My Hackathon Project")
    assert project["name"] == "My Hackathon Project"
    assert project["technology"] == "FastAPI"
    assert project["status"] == "active"
    assert "id" in project


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient):
    await _create_project(client, "List Project A")
    await _create_project(client, "List Project B")
    resp = await client.get(f"/api/projects?user_id={USER_ID}")
    assert resp.status_code == 200
    projects = resp.json()
    assert isinstance(projects, list)
    assert len(projects) >= 2


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient):
    project = await _create_project(client, "Get Project")
    pid = project["id"]
    resp = await client.get(f"/api/projects/{pid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == pid


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient):
    resp = await client.get("/api/projects/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient):
    project = await _create_project(client, "Update Project")
    pid = project["id"]
    resp = await client.patch(
        f"/api/projects/{pid}",
        json={"description": "Updated description", "status": "completed"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["description"] == "Updated description"
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient):
    project = await _create_project(client, "Delete Project")
    pid = project["id"]
    resp = await client.delete(f"/api/projects/{pid}")
    assert resp.status_code == 204
    # Confirm it's gone
    resp2 = await client.get(f"/api/projects/{pid}")
    assert resp2.status_code == 404


# ---------------------------------------------------------------------------
# Chat stub
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_chat_information(client: AsyncClient):
    resp = await client.post(
        "/api/chat",
        json={"message": "What is a REST API?", "user_id": USER_ID},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert "content" in data
    assert len(data["content"]) > 0
    assert "agents_used" in data
    assert isinstance(data["agents_used"], list)


@pytest.mark.asyncio
async def test_chat_session_continuity(client: AsyncClient):
    # First message — creates session
    resp1 = await client.post(
        "/api/chat",
        json={"message": "First message", "user_id": USER_ID},
    )
    session_id = resp1.json()["session_id"]

    # Second message — reuses session
    resp2 = await client.post(
        "/api/chat",
        json={"message": "Follow-up message", "user_id": USER_ID, "session_id": session_id},
    )
    assert resp2.json()["session_id"] == session_id

    # Retrieve messages
    resp3 = await client.get(f"/api/chat/sessions/{session_id}")
    assert resp3.status_code == 200
    messages = resp3.json()["messages"]
    assert len(messages) == 4  # 2 user + 2 assistant


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_list_notifications_empty(client: AsyncClient):
    resp = await client.get(f"/api/notifications?user_id={USER_ID}")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ---------------------------------------------------------------------------
# Reminders
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_and_list_reminder(client: AsyncClient):
    resp = await client.post(
        "/api/reminders",
        json={
            "title": "Submit project by Friday",
            "description": "Hackathon submission deadline",
            "due_date": "2024-12-06",
            "user_id": USER_ID,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Submit project by Friday"

    list_resp = await client.get(f"/api/reminders?user_id={USER_ID}")
    assert list_resp.status_code == 200
    reminders = list_resp.json()
    assert any(r["title"] == "Submit project by Friday" for r in reminders)


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_analytics(client: AsyncClient):
    resp = await client.get(f"/api/analytics?user_id={USER_ID}")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_projects" in data
    assert "tests_run" in data
    assert "agent_activity" in data
    assert data["total_projects"] >= 0


# ---------------------------------------------------------------------------
# Agent endpoints (real implementations)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_agent_endpoints_return_200(client: AsyncClient):
    """All agent endpoints must return 200 with a valid JSON body."""
    project = await _create_project(client, "Agent Endpoint Project")
    pid = project["id"]

    endpoints = [
        ("/api/analyze",          {"project_id": pid}),
        ("/api/test/run",         {"project_id": pid}),
        ("/api/test/generate",    {"project_id": pid}),
        ("/api/recommendations",  {"project_id": pid}),
        ("/api/submission/check", {"project_id": pid}),
        ("/api/release/check",    {"project_id": pid}),
    ]
    for ep, body in endpoints:
        resp = await client.post(ep, json=body)
        assert resp.status_code == 200, f"{ep} returned {resp.status_code}: {resp.text}"
        assert isinstance(resp.json(), dict), f"{ep} did not return a JSON object"


@pytest.mark.asyncio
async def test_documentation_endpoint(client: AsyncClient):
    project = await _create_project(client, "Doc Project")
    resp = await client.post(
        "/api/documentation",
        json={"project_id": project["id"], "doc_type": "readme"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "doc_type" in data or "content" in data or "error" in data


@pytest.mark.asyncio
async def test_content_endpoint(client: AsyncClient):
    project = await _create_project(client, "Content Project")
    resp = await client.post(
        "/api/content",
        json={"project_id": project["id"], "content_type": "description"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "content_type" in data or "content" in data or "error" in data


@pytest.mark.asyncio
async def test_narration_endpoint(client: AsyncClient):
    project = await _create_project(client, "Narration Project")
    resp = await client.post(
        "/api/narration",
        json={"project_id": project["id"], "narration_for": "demo"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "narration_for" in data or "script" in data or "error" in data
