"""
Reminder Agent — detects deadlines/tasks in user messages and manages reminders.

Detects:
  - project submission deadlines
  - demo dates
  - testing/documentation deadlines
  - general task reminders

Asks for confirmation before creating calendar events.
Never exposes OAuth credentials.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone

from services.ai_service import BaseAIProvider, Message

DETECT_SYSTEM_PROMPT = """You are an intelligent deadline and task detector.

Given a user message, detect any project-related deadlines, tasks, or reminders.

Output STRICT JSON (no markdown fences):
{
  "detected": true | false,
  "items": [
    {
      "type": "submission" | "demo" | "testing" | "documentation" | "meeting" | "release" | "general",
      "title": "Short title",
      "description": "What was said",
      "due_date": "YYYY-MM-DD or null",
      "relative_description": "e.g. 'next Friday' or null",
      "confidence": "high" | "medium" | "low"
    }
  ],
  "confirmation_prompt": "Ask the user: 'Would you like me to create a reminder for X on Y?'"
}

If nothing is detected, return {"detected": false, "items": [], "confirmation_prompt": null}.
Today's date context will be provided.
"""

RELATIVE_DATE_MAP = {
    "tomorrow": 1,
    "next week": 7,
    "in two weeks": 14,
    "in 2 weeks": 14,
    "next month": 30,
}


class ReminderAgent:
    """
    Detects deadlines and tasks from natural language.
    Creates, lists, and manages reminders.
    Optionally creates Google Calendar events (if integration is configured).
    """

    def __init__(self, ai: BaseAIProvider) -> None:
        self._ai = ai

    async def detect_from_message(self, message: str) -> dict:
        """
        Parse a user message for deadline/task mentions.

        Returns detection result with items and a confirmation prompt.
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d (%A)")
        user_prompt = (
            f"Today's date: {today}\n\n"
            f"User message:\n\"{message}\"\n\n"
            "Detect any deadlines, tasks, or reminders in this message."
        )

        response = await self._ai.chat(
            messages=[Message("user", user_prompt)],
            system_prompt=DETECT_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=512,
        )

        return self._parse_detection(response.content)

    async def create_calendar_event(
        self,
        title: str,
        description: str,
        due_date: str,
        user_id: str,
    ) -> dict:
        """
        Create a Google Calendar event if configured.
        Returns a result dict with success/error status.

        NEVER exposes OAuth credentials in the response.
        """
        from config.settings import settings
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            return {
                "success": False,
                "error": "Google Calendar integration is not configured.",
                "note": "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env to enable calendar events.",
            }

        # Google Calendar integration (Phase integration — requires OAuth flow)
        # For now, return a clear placeholder indicating what would happen.
        return {
            "success": False,
            "error": "Google Calendar OAuth flow not yet completed.",
            "note": "The reminder was saved in A2Z Nexus. Google Calendar integration requires OAuth setup.",
        }

    def resolve_relative_date(self, relative: str) -> str | None:
        """Convert relative date strings to YYYY-MM-DD."""
        today = datetime.now(timezone.utc)
        rel = relative.lower().strip()

        # "next [weekday]"
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for i, day in enumerate(weekdays):
            if f"next {day}" in rel or rel == day:
                days_ahead = (i - today.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

        for phrase, days in RELATIVE_DATE_MAP.items():
            if phrase in rel:
                return (today + timedelta(days=days)).strftime("%Y-%m-%d")

        # Try to parse common date formats
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%B %d", "%b %d"):
            try:
                parsed = datetime.strptime(relative, fmt)
                if parsed.year == 1900:  # no year given
                    parsed = parsed.replace(year=today.year)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue

        return None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_detection(content: str) -> dict:
        content = content.strip()
        # Remove markdown fences
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content).strip()

        try:
            data = json.loads(content)
            return data
        except json.JSONDecodeError:
            # Try to extract JSON object
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass

        return {"detected": False, "items": [], "confirmation_prompt": None}
