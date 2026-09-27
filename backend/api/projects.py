"""
Projects CRUD router.

POST   /api/projects
GET    /api/projects          ?user_id=
GET    /api/projects/{id}
PATCH  /api/projects/{id}
DELETE /api/projects/{id}
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import get_db
from database.models import Project, User
from models.schemas import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def _ensure_user(user_id: str, db: AsyncSession) -> User:
    """Auto-create a stub user if one doesn't exist yet (dev convenience)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            id=user_id,
            name="Default User",
            email=f"{user_id}@a2znexus.local",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def _get_project_or_404(project_id: str, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return project


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    payload: ProjectCreate,
    user_id: str = Query(default="default-user"),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    # Accept user_id from body OR query param (body wins)
    uid = getattr(payload, "user_id", None) or user_id
    await _ensure_user(uid, db)

    project = Project(
        id=str(uuid.uuid4()),
        user_id=uid,
        name=payload.name,
        description=payload.description or "",
        repository_path=payload.repository_path or "",
        technology=payload.technology or "",
        deadline=payload.deadline,
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return ProjectResponse.model_validate(project)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    user_id: str = Query(default="default-user"),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectResponse]:
    result = await db.execute(
        select(Project).where(Project.user_id == user_id).order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    return [ProjectResponse.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    project = await _get_project_or_404(project_id, db)
    return ProjectResponse.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    project = await _get_project_or_404(project_id, db)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    project.updated_at = _now()
    await db.commit()
    await db.refresh(project)
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    project = await _get_project_or_404(project_id, db)
    await db.delete(project)
    await db.commit()
