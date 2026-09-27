"""Central capability/status registry for A2Z Nexus.

Never returns secrets.  This endpoint is safe to expose to the frontend and
is intentionally based only on settings that actually exist in this build.
"""
from __future__ import annotations

from config.settings import settings

AGENTS = [
    {"name": "information", "role": "General developer technical Q&A"},
    {"name": "code_analysis", "role": "Project structure, code and issue analysis"},
    {"name": "testing", "role": "Run and generate tests; explain failures"},
    {"name": "recommendation", "role": "Evidence-based project improvement recommendations"},
    {"name": "documentation", "role": "README, API and setup documentation"},
    {"name": "content", "role": "Project descriptions, abstracts and presentation content"},
    {"name": "narration", "role": "Demo and presentation narration"},
    {"name": "reminder", "role": "Deadline detection and reminder workflow"},
    {"name": "submission", "role": "Submission readiness checks"},
    {"name": "release", "role": "Release/deployment readiness checks"},
]

WORKFLOWS = {
    "project_improvement": ["code_analysis", "testing", "recommendation"],
    "submission_prep": ["code_analysis", "testing", "submission"],
    "release_check": ["testing", "release"],
}


def get_capabilities() -> dict:
    provider = settings.AI_PROVIDER.lower().strip()
    if provider == "gemini":
        model = settings.GEMINI_MODEL
    else:
        model = settings.AI_MODEL

    return {
        "ai_provider": provider,
        "ai_model": model,
        "ai_ready": (
            bool(settings.GEMINI_API_KEY.strip()) if provider == "gemini"
            else bool(settings.AI_API_KEY.strip())
        ),
        "agents": AGENTS,
        "workflows": WORKFLOWS,
        "integrations": {
            "gemini": bool(settings.GEMINI_API_KEY.strip()),
            "github": bool(settings.GITHUB_TOKEN.strip()),
            "google_calendar": bool(settings.GOOGLE_CLIENT_ID.strip() and settings.GOOGLE_CLIENT_SECRET.strip()),
            "microsoft": bool(settings.MICROSOFT_CLIENT_ID.strip() and settings.MICROSOFT_CLIENT_SECRET.strip()),
            "database": settings.DATABASE_URL.split(":", 1)[0],
        },
    }
