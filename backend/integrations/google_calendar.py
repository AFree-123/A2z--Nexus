"""Google Calendar event creation using stored OAuth credentials."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from config.settings import settings


def _parse_due(value: str | None) -> datetime:
    if not value:
        raise ValueError("A due_date is required to create a calendar event.")
    raw = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        dt = datetime.fromisoformat(raw + "T09:00:00") if "T" not in raw else datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


async def create_event(access_token: str, title: str, description: str, due_date: str) -> dict[str, Any]:
    import httpx
    start = _parse_due(due_date)
    end = start.replace(hour=min(start.hour + 1, 23))
    payload = {
        "summary": title,
        "description": description or "Created by A2Z Nexus",
        "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers={"Authorization": f"Bearer {access_token}"},
            json=payload,
        )
        response.raise_for_status()
        return response.json()
