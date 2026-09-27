"""
Chat router — powered by the AI Orchestrator.

POST /api/chat
GET  /api/chat/sessions/{session_id}
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import get_db
from database.models import ChatMessage, ChatSession, Project, Reminder
from models.schemas import ChatRequest, ChatResponse
from services.ai_service import ai_provider

router = APIRouter(prefix="/chat", tags=["chat"])


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    from api.projects import _ensure_user
    from orchestrator.orchestrator import Orchestrator

    user_id = payload.user_id or "default-user"
    await _ensure_user(user_id, db)

    # Resolve or create session
    session_id = payload.session_id
    if session_id:
        result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
        session = result.scalar_one_or_none()
        if session is None:
            session_id = None

    if not session_id:
        session = ChatSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            project_id=payload.project_id,
            created_at=_now(),
        )
        db.add(session)
        await db.flush()
        session_id = session.id

    # Load conversation history for context
    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .limit(20)
    )
    history = [
        {"role": m.role, "content": m.content}
        for m in history_result.scalars().all()
        if m.role in ("user", "assistant")
    ]

    # Load project context if project_id provided
    project: dict | None = None
    if payload.project_id:
        proj_result = await db.execute(
            select(Project).where(Project.id == payload.project_id)
        )
        proj_obj = proj_result.scalar_one_or_none()
        if proj_obj:
            project = {
                "id": proj_obj.id,
                "name": proj_obj.name,
                "description": proj_obj.description,
                "repository_path": proj_obj.repository_path,
                "technology": proj_obj.technology,
            }

    # Store user message
    user_msg = ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        content=payload.message,
        created_at=_now(),
    )
    db.add(user_msg)

    # Let the AI know about any attachments the frontend sent (images / other
    # files). Without this, attachments were accepted by the UI but the agent
    # had no idea they existed, since ChatRequest previously dropped them.
    orchestrator_message = payload.message
    attachment_notes: list[str] = []
    if payload.image:
        attachment_notes.append("an image")
    if payload.files:
        names = ", ".join(f.get("name", "file") for f in payload.files[:5])
        attachment_notes.append(f"file(s): {names}")
    if attachment_notes:
        orchestrator_message = (
            f"{payload.message}\n\n[User also attached {', '.join(attachment_notes)}.]"
        )

    # Run the orchestrator
    orchestrator = Orchestrator(ai_provider())
    orch_result = await orchestrator.process(
        message=orchestrator_message,
        project=project,
        conversation_history=history,
    )

    # ------------------------------------------------------------------
    # Reminder agent: previously this only ever *asked* "would you like me
    # to create a reminder?" and then dead-ended — nothing ever called
    # POST /api/reminders, so nothing was ever saved, and the ChatResponse
    # never carried a `reminder` field even though the frontend
    # (ChatMessage.jsx) already had a "Reminder Set" card waiting for one.
    # Now: when a deadline is detected with reasonable confidence, actually
    # save it and tell the frontend about it.
    # ------------------------------------------------------------------
    reminder_payload: dict | None = None
    if orch_result.intent == "reminder" and orch_result.metadata.get("detected"):
        items = orch_result.metadata.get("items") or []
        item = next((i for i in items if i.get("confidence") != "low"), items[0] if items else None)
        if item:
            from agents.reminder.agent import ReminderAgent

            due_date = item.get("due_date")
            if not due_date and item.get("relative_description"):
                due_date = ReminderAgent(ai_provider()).resolve_relative_date(
                    item["relative_description"]
                )
            reminder_row = Reminder(
                id=str(uuid.uuid4()),
                user_id=user_id,
                project_id=payload.project_id,
                title=item.get("title") or "Reminder",
                description=item.get("description") or payload.message,
                due_date=due_date,
                created_at=_now(),
            )
            db.add(reminder_row)
            reminder_payload = {"title": reminder_row.title, "date": due_date}

    # Store assistant response
    assistant_msg_id = str(uuid.uuid4())
    assistant_msg = ChatMessage(
        id=assistant_msg_id,
        session_id=session_id,
        role="assistant",
        content=orch_result.content,
        agent_used=",".join(orch_result.agents_used),
        created_at=_now(),
    )
    db.add(assistant_msg)
    await db.commit()

    return ChatResponse(
        session_id=session_id,
        message_id=assistant_msg_id,
        content=orch_result.content,
        agents_used=orch_result.agents_used,
        metadata={
            "intent": orch_result.intent,
            **orch_result.metadata,
        },
        reminder=reminder_payload,
    )


@router.get("/sessions/{session_id}")
async def get_session_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    msgs_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = msgs_result.scalars().all()
    return {
        "session_id": session_id,
        "project_id": session.project_id,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "agent_used": m.agent_used,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    }
