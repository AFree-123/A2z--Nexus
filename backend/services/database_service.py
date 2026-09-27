"""
DatabaseService — shared data-access layer used by all agents and routers.

Agents call this service instead of using SQLAlchemy directly.
This keeps agent code clean and makes the DB layer independently testable.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    AgentResult,
    Notification,
    Project,
    Recommendation,
    ReleaseStatus,
    Reminder,
    SubmissionStatus,
    TestResult,
    User,
)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _uid() -> str:
    return str(uuid.uuid4())


class DatabaseService:
    """Thin async wrapper around SQLAlchemy operations used by agents."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # User
    # ------------------------------------------------------------------
    async def ensure_user(self, user_id: str, name: str = "Default User") -> User:
        result = await self._db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                id=user_id,
                name=name,
                email=f"{user_id}@a2znexus.local",
            )
            self._db.add(user)
            await self._db.commit()
            await self._db.refresh(user)
        return user

    # ------------------------------------------------------------------
    # Project
    # ------------------------------------------------------------------
    async def get_project(self, project_id: str) -> Project | None:
        result = await self._db.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def update_project_fields(self, project_id: str, **fields: Any) -> Project | None:
        project = await self.get_project(project_id)
        if project is None:
            return None
        for k, v in fields.items():
            setattr(project, k, v)
        project.updated_at = _now()
        await self._db.commit()
        await self._db.refresh(project)
        return project

    # ------------------------------------------------------------------
    # AgentResult  — stores raw agent output (JSON blob)
    # ------------------------------------------------------------------
    async def save_agent_result(
        self, project_id: str, agent_name: str, result: dict[str, Any]
    ) -> AgentResult:
        record = AgentResult(
            id=_uid(),
            project_id=project_id,
            agent_name=agent_name,
            result_json=json.dumps(result),
            created_at=_now(),
        )
        self._db.add(record)
        await self._db.commit()
        await self._db.refresh(record)
        return record

    async def get_latest_agent_result(
        self, project_id: str, agent_name: str
    ) -> dict[str, Any] | None:
        result = await self._db.execute(
            select(AgentResult)
            .where(AgentResult.project_id == project_id, AgentResult.agent_name == agent_name)
            .order_by(AgentResult.created_at.desc())
            .limit(1)
        )
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return json.loads(record.result_json)

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------
    async def save_recommendations(
        self, project_id: str, recommendations: list[dict[str, Any]]
    ) -> list[Recommendation]:
        records = []
        for rec in recommendations:
            record = Recommendation(
                id=_uid(),
                project_id=project_id,
                priority=rec.get("priority", "MEDIUM"),
                category=rec.get("category", "general"),
                title=rec["title"],
                description=rec.get("description", ""),
                created_at=_now(),
            )
            self._db.add(record)
            records.append(record)
        await self._db.commit()
        return records

    async def get_recommendations(self, project_id: str) -> list[Recommendation]:
        result = await self._db.execute(
            select(Recommendation)
            .where(Recommendation.project_id == project_id, Recommendation.resolved == False)  # noqa: E712
            .order_by(Recommendation.created_at.desc())
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # TestResult
    # ------------------------------------------------------------------
    async def save_test_result(
        self,
        project_id: str,
        total: int,
        passed: int,
        failed: int,
        skipped: int,
        details: list[dict[str, Any]],
    ) -> TestResult:
        record = TestResult(
            id=_uid(),
            project_id=project_id,
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            details_json=json.dumps(details),
            created_at=_now(),
        )
        self._db.add(record)
        await self._db.commit()
        await self._db.refresh(record)
        return record

    async def get_latest_test_result(self, project_id: str) -> TestResult | None:
        result = await self._db.execute(
            select(TestResult)
            .where(TestResult.project_id == project_id)
            .order_by(TestResult.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Notification
    # ------------------------------------------------------------------
    async def create_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        category: str = "info",
        project_id: str | None = None,
    ) -> Notification:
        record = Notification(
            id=_uid(),
            user_id=user_id,
            project_id=project_id,
            category=category,
            title=title,
            message=message,
            created_at=_now(),
        )
        self._db.add(record)
        await self._db.commit()
        await self._db.refresh(record)
        return record

    # ------------------------------------------------------------------
    # SubmissionStatus
    # ------------------------------------------------------------------
    async def save_submission_status(
        self,
        project_id: str,
        readiness_percentage: float,
        completed: list[str],
        missing: list[str],
        warnings: list[str],
        next_actions: list[str],
    ) -> SubmissionStatus:
        record = SubmissionStatus(
            id=_uid(),
            project_id=project_id,
            readiness_percentage=readiness_percentage,
            completed_json=json.dumps(completed),
            missing_json=json.dumps(missing),
            warnings_json=json.dumps(warnings),
            next_actions_json=json.dumps(next_actions),
            created_at=_now(),
        )
        self._db.add(record)
        await self._db.commit()
        await self._db.refresh(record)
        return record

    async def get_latest_submission_status(self, project_id: str) -> SubmissionStatus | None:
        result = await self._db.execute(
            select(SubmissionStatus)
            .where(SubmissionStatus.project_id == project_id)
            .order_by(SubmissionStatus.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # ReleaseStatus
    # ------------------------------------------------------------------
    async def save_release_status(
        self,
        project_id: str,
        ready: bool,
        passed_checks: list[str],
        warnings: list[str],
        blocking_issues: list[str],
        recommended_actions: list[str],
    ) -> ReleaseStatus:
        record = ReleaseStatus(
            id=_uid(),
            project_id=project_id,
            ready=ready,
            passed_checks_json=json.dumps(passed_checks),
            warnings_json=json.dumps(warnings),
            blocking_issues_json=json.dumps(blocking_issues),
            recommended_actions_json=json.dumps(recommended_actions),
            created_at=_now(),
        )
        self._db.add(record)
        await self._db.commit()
        await self._db.refresh(record)
        return record

    async def get_latest_release_status(self, project_id: str) -> ReleaseStatus | None:
        result = await self._db.execute(
            select(ReleaseStatus)
            .where(ReleaseStatus.project_id == project_id)
            .order_by(ReleaseStatus.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Reminder
    # ------------------------------------------------------------------
    async def create_reminder(
        self,
        user_id: str,
        title: str,
        description: str = "",
        due_date: str | None = None,
        project_id: str | None = None,
    ) -> Reminder:
        record = Reminder(
            id=_uid(),
            user_id=user_id,
            project_id=project_id,
            title=title,
            description=description,
            due_date=due_date,
            created_at=_now(),
        )
        self._db.add(record)
        await self._db.commit()
        await self._db.refresh(record)
        return record
