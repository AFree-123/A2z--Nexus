
"""Explicit multi-agent workflow endpoints.

Chat remains the primary user-facing entry point; these endpoints are useful
for the dashboard/project workspace and make the multi-agent pipeline explicit.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from database.engine import get_db
from database.models import Project
from services.ai_service import ai_provider
from services.database_service import DatabaseService
from orchestrator.orchestrator import Orchestrator

router = APIRouter(prefix="/workflows", tags=["workflows"])

class WorkflowRequest(BaseModel):
    project_id: str
    user_id: str = "default-user"

async def _project(project_id: str, db: AsyncSession) -> Project:
    from sqlalchemy import select
    result = await db.execute(select(Project).where(Project.id == project_id))
    p = result.scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return p

@router.post("/project-improvement")
async def project_improvement(payload: WorkflowRequest, db: AsyncSession = Depends(get_db)) -> dict:
    p = await _project(payload.project_id, db)
    svc = DatabaseService(db)
    ai = ai_provider()
    orch = Orchestrator(ai)
    result = await orch.process(
        "Improve my project",
        project={"id": p.id, "name": p.name, "repository_path": p.repository_path, "technology": p.technology},
    )
    if result.metadata.get("code_analysis"):
        await svc.save_agent_result(p.id, "code_analysis", result.metadata["code_analysis"])
    if result.metadata.get("test_results"):
        t = result.metadata["test_results"]
        await svc.save_test_result(p.id, t.get("total",0), t.get("passed",0), t.get("failed",0), t.get("skipped",0), t.get("details",[]))
    recs = result.metadata.get("recommendations") or []
    if recs:
        await svc.save_recommendations(p.id, recs)
    return {"workflow": "project_improvement", "agents_used": result.agents_used, "intent": result.intent, "report": result.content, "metrics": {"tests_total": (result.metadata.get("test_results") or {}).get("total",0), "tests_passed": (result.metadata.get("test_results") or {}).get("passed",0), "tests_failed": (result.metadata.get("test_results") or {}).get("failed",0), "recommendations": len(recs)}}

@router.post("/submission-prep")
async def submission_prep(payload: WorkflowRequest, db: AsyncSession = Depends(get_db)) -> dict:
    p = await _project(payload.project_id, db)
    orch = Orchestrator(ai_provider())
    result = await orch.process("Prepare for submission", project={"id":p.id,"name":p.name,"repository_path":p.repository_path,"technology":p.technology})
    return {"workflow":"submission_prep","agents_used":result.agents_used,"intent":result.intent,"report":result.content,"metadata":result.metadata}

@router.post("/release-check")
async def release_check(payload: WorkflowRequest, db: AsyncSession = Depends(get_db)) -> dict:
    p = await _project(payload.project_id, db)
    orch = Orchestrator(ai_provider())
    result = await orch.process("Check everything for release", project={"id":p.id,"name":p.name,"repository_path":p.repository_path,"technology":p.technology})
    return {"workflow":"release_check","agents_used":result.agents_used,"intent":result.intent,"report":result.content,"metadata":result.metadata}
