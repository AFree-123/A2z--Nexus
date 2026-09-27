"""
Analytics router.

GET /api/analytics   ?user_id=
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import get_db
from database.models import (
    AgentResult,
    Project,
    Recommendation,
    Reminder,
    TestResult,
)
from models.schemas import AnalyticsResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsResponse)
async def get_analytics(
    user_id: str = Query(default="default-user"),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsResponse:
    # --- Project counts ---
    total_q = await db.execute(
        select(func.count(Project.id)).where(Project.user_id == user_id)
    )
    total_projects = total_q.scalar_one() or 0

    active_q = await db.execute(
        select(func.count(Project.id)).where(
            Project.user_id == user_id, Project.status == "active"
        )
    )
    active_projects = active_q.scalar_one() or 0

    completed_q = await db.execute(
        select(func.count(Project.id)).where(
            Project.user_id == user_id, Project.status == "completed"
        )
    )
    completed_projects = completed_q.scalar_one() or 0

    # --- Test counts (across all user projects) ---
    user_project_ids_q = await db.execute(
        select(Project.id).where(Project.user_id == user_id)
    )
    user_project_ids = [row[0] for row in user_project_ids_q.fetchall()]

    tests_run = tests_passed = tests_failed = 0
    if user_project_ids:
        tr_q = await db.execute(
            select(
                func.sum(TestResult.total),
                func.sum(TestResult.passed),
                func.sum(TestResult.failed),
            ).where(TestResult.project_id.in_(user_project_ids))
        )
        row = tr_q.one()
        tests_run = int(row[0] or 0)
        tests_passed = int(row[1] or 0)
        tests_failed = int(row[2] or 0)

    # --- Recommendation count ---
    recs_q = await db.execute(
        select(func.count(Recommendation.id)).where(
            Recommendation.project_id.in_(user_project_ids) if user_project_ids else False
        )
    )
    recommendations_generated = recs_q.scalar_one() or 0

    # --- Reminders count ---
    rem_q = await db.execute(
        select(func.count(Reminder.id)).where(Reminder.user_id == user_id)
    )
    reminders_total = rem_q.scalar_one() or 0

    # --- Agent activity ---
    agent_activity: dict[str, int] = {}
    if user_project_ids:
        agent_q = await db.execute(
            select(AgentResult.agent_name, func.count(AgentResult.id))
            .where(AgentResult.project_id.in_(user_project_ids))
            .group_by(AgentResult.agent_name)
        )
        for agent_name, count in agent_q.fetchall():
            agent_activity[agent_name] = count

    return AnalyticsResponse(
        total_projects=total_projects,
        active_projects=active_projects,
        completed_projects=completed_projects,
        tests_run=tests_run,
        tests_passed=tests_passed,
        tests_failed=tests_failed,
        recommendations_generated=recommendations_generated,
        reminders_total=reminders_total,
        agent_activity=agent_activity,
    )
