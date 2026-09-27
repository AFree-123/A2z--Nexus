"""
Agent API endpoints — full implementations (Phases 5-12).

These replace the Phase 2 stubs and call the real agent implementations.
All endpoints save results to the database and create notifications.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import get_db
from database.models import Project
from services.ai_service import ai_provider
from services.database_service import DatabaseService

router = APIRouter(tags=["agents"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ProjectRequest(BaseModel):
    project_id: str
    user_id: str = "default-user"


class DocumentationRequest(BaseModel):
    project_id: str
    doc_type: str = "readme"
    user_id: str = "default-user"


class ContentRequest(BaseModel):
    project_id: str
    content_type: str = "description"
    user_id: str = "default-user"


class NarrationRequest(BaseModel):
    project_id: str
    narration_for: str = "demo"
    user_id: str = "default-user"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_project(project_id: str, db: AsyncSession) -> Project | None:
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


def _project_context(p: Project) -> str:
    return (
        f"Name: {p.name}\n"
        f"Description: {p.description}\n"
        f"Technology: {p.technology}\n"
        f"Repository: {p.repository_path}\n"
    )


# ---------------------------------------------------------------------------
# Code Analysis  (Phase 6)
# ---------------------------------------------------------------------------

@router.post("/analyze")
async def analyze_project(
    payload: ProjectRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    from agents.code_analysis.agent import CodeAnalysisAgent

    project = await _get_project(payload.project_id, db)
    if project is None:
        return {"error": f"Project '{payload.project_id}' not found."}

    svc = DatabaseService(db)
    agent = CodeAnalysisAgent(ai_provider())
    result = await agent.analyze(project.repository_path, project.name)

    await svc.save_agent_result(project.id, "code_analysis", result)
    await svc.create_notification(
        user_id=payload.user_id,
        title="Code analysis completed",
        message=f"Project '{project.name}' — {result.get('file_count', 0)} files analyzed, {len(result.get('issues', []))} issues found.",
        category="info",
        project_id=project.id,
    )
    return result


# ---------------------------------------------------------------------------
# Testing  (Phase 7)
# ---------------------------------------------------------------------------

@router.post("/test/run")
async def run_tests(
    payload: ProjectRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    from agents.testing.agent import TestingAgent

    project = await _get_project(payload.project_id, db)
    if project is None:
        return {"error": f"Project '{payload.project_id}' not found."}

    svc = DatabaseService(db)
    agent = TestingAgent(ai_provider())
    result = await agent.run_tests(project.repository_path)

    await svc.save_test_result(
        project_id=project.id,
        total=result.get("total", 0),
        passed=result.get("passed", 0),
        failed=result.get("failed", 0),
        skipped=result.get("skipped", 0),
        details=result.get("details", []),
    )
    category = "error" if result.get("failed", 0) > 0 else "success"
    await svc.create_notification(
        user_id=payload.user_id,
        title=f"Tests: {result.get('passed', 0)} passed, {result.get('failed', 0)} failed",
        message=f"Project '{project.name}' — {result.get('total', 0)} tests run.",
        category=category,
        project_id=project.id,
    )
    return result


@router.post("/test/generate")
async def generate_tests(
    payload: ProjectRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    from agents.testing.agent import TestingAgent

    project = await _get_project(payload.project_id, db)
    if project is None:
        return {"error": f"Project '{payload.project_id}' not found."}

    agent = TestingAgent(ai_provider())
    result = await agent.generate_tests(project.repository_path)
    return result


# ---------------------------------------------------------------------------
# Recommendations  (Phase 8)
# ---------------------------------------------------------------------------

@router.post("/recommendations")
async def get_recommendations(
    payload: ProjectRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    from agents.recommendation.agent import RecommendationAgent

    project = await _get_project(payload.project_id, db)
    if project is None:
        return {"error": f"Project '{payload.project_id}' not found."}

    svc = DatabaseService(db)
    # Pull latest code analysis and test results if available
    code_result = await svc.get_latest_agent_result(project.id, "code_analysis")
    latest_test = await svc.get_latest_test_result(project.id)
    test_result = None
    if latest_test:
        import json
        test_result = {
            "framework": latest_test.details_json,
            "total": latest_test.total,
            "passed": latest_test.passed,
            "failed": latest_test.failed,
            "skipped": latest_test.skipped,
        }

    agent = RecommendationAgent(ai_provider())
    recs = await agent.recommend(
        project_name=project.name,
        code_analysis=code_result,
        test_results=test_result,
        project_metadata={"technology": project.technology, "status": project.status},
    )
    await svc.save_recommendations(project.id, recs)
    await svc.create_notification(
        user_id=payload.user_id,
        title=f"{len(recs)} recommendations generated",
        message=f"Project '{project.name}' — {sum(1 for r in recs if r.get('priority') == 'HIGH')} high priority.",
        category="info",
        project_id=project.id,
    )
    return {"recommendations": recs, "count": len(recs)}


# ---------------------------------------------------------------------------
# Documentation  (Phase 9)
# ---------------------------------------------------------------------------

@router.post("/documentation")
async def generate_documentation(
    payload: DocumentationRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    from agents.documentation.agent import DocumentationAgent

    project = await _get_project(payload.project_id, db)
    if project is None:
        return {"error": f"Project '{payload.project_id}' not found."}

    agent = DocumentationAgent(ai_provider())
    result = await agent.generate(payload.doc_type, project.name, _project_context(project))

    svc = DatabaseService(db)
    await svc.create_notification(
        user_id=payload.user_id,
        title=f"{payload.doc_type.upper()} documentation generated",
        message=f"Project '{project.name}'",
        category="success",
        project_id=project.id,
    )
    return result


# ---------------------------------------------------------------------------
# Content  (Phase 9)
# ---------------------------------------------------------------------------

@router.post("/content")
async def generate_content(
    payload: ContentRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    from agents.content.agent import ContentAgent

    project = await _get_project(payload.project_id, db)
    if project is None:
        return {"error": f"Project '{payload.project_id}' not found."}

    agent = ContentAgent(ai_provider())
    result = await agent.generate(payload.content_type, project.name, _project_context(project))
    return result


# ---------------------------------------------------------------------------
# Narration  (Phase 9)
# ---------------------------------------------------------------------------

@router.post("/narration")
async def generate_narration(
    payload: NarrationRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    from agents.narration.agent import NarrationAgent

    project = await _get_project(payload.project_id, db)
    if project is None:
        return {"error": f"Project '{payload.project_id}' not found."}

    agent = NarrationAgent(ai_provider())
    result = await agent.generate(payload.narration_for, project.name, _project_context(project))
    return result


# ---------------------------------------------------------------------------
# Submission check  (Phase 11)
# ---------------------------------------------------------------------------

@router.post("/submission/check")
async def submission_check(
    payload: ProjectRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    from agents.submission.agent import SubmissionAgent

    project = await _get_project(payload.project_id, db)
    if project is None:
        return {"error": f"Project '{payload.project_id}' not found."}

    svc = DatabaseService(db)
    code_result = await svc.get_latest_agent_result(project.id, "code_analysis")

    agent = SubmissionAgent(ai_provider())
    result = await agent.check(
        project_path=project.repository_path,
        project_name=project.name,
        code_analysis=code_result,
    )
    await svc.save_submission_status(
        project_id=project.id,
        readiness_percentage=result.get("readiness_percentage", 0),
        completed=result.get("completed", []),
        missing=result.get("missing", []),
        warnings=result.get("warnings", []),
        next_actions=result.get("next_actions", []),
    )
    return result


# ---------------------------------------------------------------------------
# Release check  (Phase 12)
# ---------------------------------------------------------------------------

@router.post("/release/check")
async def release_check(
    payload: ProjectRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    from agents.release.agent import ReleaseAgent

    project = await _get_project(payload.project_id, db)
    if project is None:
        return {"error": f"Project '{payload.project_id}' not found."}

    svc = DatabaseService(db)
    code_result = await svc.get_latest_agent_result(project.id, "code_analysis")

    agent = ReleaseAgent(ai_provider())
    result = await agent.check(
        project_path=project.repository_path,
        project_name=project.name,
        code_analysis=code_result,
    )
    await svc.save_release_status(
        project_id=project.id,
        ready=result.get("ready", False),
        passed_checks=result.get("passed_checks", []),
        warnings=result.get("warnings", []),
        blocking_issues=result.get("blocking_issues", []),
        recommended_actions=result.get("recommended_actions", []),
    )
    return result
