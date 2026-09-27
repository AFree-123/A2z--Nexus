"""
Phase 3 & 4 tests — DatabaseService and AI service.
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.engine import Base
from services.database_service import DatabaseService

# ---------------------------------------------------------------------------
# Test DB
# ---------------------------------------------------------------------------
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        import database.models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def db_service():
    async with TestSessionLocal() as session:
        yield DatabaseService(session)


# ---------------------------------------------------------------------------
# DatabaseService tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ensure_user_creates(db_service: DatabaseService):
    user = await db_service.ensure_user("u-test-001", "Test User")
    assert user.id == "u-test-001"
    # idempotent
    user2 = await db_service.ensure_user("u-test-001")
    assert user2.id == user.id


@pytest.mark.asyncio
async def test_create_notification(db_service: DatabaseService):
    await db_service.ensure_user("u-notif-001")
    notif = await db_service.create_notification(
        user_id="u-notif-001",
        title="Test Notification",
        message="Something happened",
        category="info",
    )
    assert notif.id is not None
    assert notif.title == "Test Notification"
    assert notif.read is False


@pytest.mark.asyncio
async def test_save_and_retrieve_agent_result(db_service: DatabaseService):
    # Need a project first — create it directly via SQLAlchemy
    from database.models import Project, User
    import uuid
    async with TestSessionLocal() as session2:
        uid = str(uuid.uuid4())
        pid = str(uuid.uuid4())
        session2.add(User(id=uid, name="u", email=f"{uid}@test.local"))
        session2.add(Project(
            id=pid, user_id=uid, name="P", description="", repository_path="",
            technology="", status="active", health="unknown", test_status="unknown",
            open_issues=0,
        ))
        await session2.commit()

    result_data = {"files": 10, "languages": ["Python"]}
    record = await db_service.save_agent_result(pid, "code_analysis", result_data)
    assert record.agent_name == "code_analysis"

    retrieved = await db_service.get_latest_agent_result(pid, "code_analysis")
    assert retrieved == result_data


@pytest.mark.asyncio
async def test_save_test_result(db_service: DatabaseService):
    from database.models import Project, User
    import uuid
    async with TestSessionLocal() as s:
        uid = str(uuid.uuid4())
        pid = str(uuid.uuid4())
        s.add(User(id=uid, name="u2", email=f"{uid}@test.local"))
        s.add(Project(
            id=pid, user_id=uid, name="P2", description="", repository_path="",
            technology="", status="active", health="unknown", test_status="unknown",
            open_issues=0,
        ))
        await s.commit()

    tr = await db_service.save_test_result(
        project_id=pid, total=10, passed=8, failed=2, skipped=0,
        details=[{"name": "test_foo", "status": "passed"}],
    )
    assert tr.total == 10
    assert tr.passed == 8

    latest = await db_service.get_latest_test_result(pid)
    assert latest is not None
    assert latest.failed == 2


# ---------------------------------------------------------------------------
# AI service tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mock_provider_available():
    from services.ai_service import MockAIProvider
    p = MockAIProvider()
    assert p.is_available() is True


@pytest.mark.asyncio
async def test_mock_provider_generic_response():
    from services.ai_service import Message, MockAIProvider
    p = MockAIProvider()
    resp = await p.chat([Message("user", "Hello, how are you?")])
    assert len(resp.content) > 0
    assert resp.provider == "mock"


@pytest.mark.asyncio
async def test_mock_provider_code_analysis_response():
    from services.ai_service import Message, MockAIProvider
    p = MockAIProvider()
    resp = await p.chat([Message("user", "Analyze my project code")])
    assert "Mock" in resp.content or "analysis" in resp.content.lower()


@pytest.mark.asyncio
async def test_mock_provider_recommendation_response():
    from services.ai_service import Message, MockAIProvider
    p = MockAIProvider()
    resp = await p.chat([Message("user", "How can I improve my project?")])
    assert "recommend" in resp.content.lower() or "Mock" in resp.content


@pytest.mark.asyncio
async def test_get_ai_provider_returns_mock_by_default():
    """With AI_PROVIDER=mock (default), should return MockAIProvider."""
    from services.ai_service import get_ai_provider, MockAIProvider
    provider = get_ai_provider()
    assert isinstance(provider, MockAIProvider)


@pytest.mark.asyncio
async def test_ai_provider_fallback_to_mock_when_no_key(monkeypatch):
    """If openai is selected but key is empty, fall back to mock."""
    from config import settings as settings_module
    monkeypatch.setattr(settings_module.settings, "AI_PROVIDER", "openai")
    monkeypatch.setattr(settings_module.settings, "AI_API_KEY", "")
    from services import ai_service
    monkeypatch.setattr(ai_service, "_provider", None)  # reset singleton

    from services.ai_service import get_ai_provider, MockAIProvider
    provider = get_ai_provider()
    assert isinstance(provider, MockAIProvider)
