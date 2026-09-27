"""Project intelligence pipeline for A2Z Nexus.

Combines deterministic filesystem/static checks with Gemini for explanations,
prioritisation, recommendations, submission and deployment guidance.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.ai_service import ai_provider, Message
from services.project_workspace import analyze, iter_files, read_text

SYSTEM = """You are A2Z Nexus Project Intelligence. Analyze a software project using ONLY the evidence supplied.
Return strict JSON with these keys:
summary (string), project_type (string), languages (array), critical_issues (array),
recommendations (array of objects with priority, category, title, description, file),
submission (object with readiness_percentage, missing, warnings, next_actions),
deployment (object with readiness_percentage, blockers, warnings, next_actions),
quality (object with code_quality, security, testing, documentation, maintainability).
Do not invent files, errors, tests, URLs, or successful deployment. If evidence is missing, say so.
Scores are 0-100 and are evidence-based estimates, not test results unless actual test output is supplied."""


def _evidence(root: Path, static: dict[str, Any]) -> str:
    parts = [json.dumps({k: v for k, v in static.items() if k not in {"root"}}, indent=2)]
    count = 0
    for p in iter_files(root):
        if p.suffix.lower() in {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".cs", ".cpp", ".c"}:
            text = read_text(p, 5000)
            if text:
                parts.append(f"\nFILE: {p.relative_to(root)}\n{text}")
                count += len(text)
                if count > 30000:
                    break
    return "\n".join(parts)


async def full_analysis(root: Path) -> dict[str, Any]:
    static = analyze(root)
    result: dict[str, Any] = {
        **static,
        "ai_analysis": None,
        "ai_available": False,
        "pipeline": ["static_scan"],
    }
    ai = ai_provider()
    if not ai.is_available():
        result["ai_analysis"] = {
            "summary": "Gemini is not configured. Deterministic project analysis is available; add GEMINI_API_KEY for AI analysis.",
            "recommendations": static.get("recommendations", []),
        }
        return result
    try:
        response = await ai.chat(
            [Message("user", _evidence(root, static))],
            system_prompt=SYSTEM,
            temperature=0.1,
            max_tokens=5000,
        )
        text = response.content.strip()
        if text.startswith("```"):
            text = text.strip("`").replace("json\n", "", 1).strip()
        parsed = json.loads(text)
        result["ai_analysis"] = parsed
        result["ai_available"] = True
        result["pipeline"] = ["static_scan", "gemini_analysis"]
        # Keep frontend-friendly top-level values while preserving deterministic evidence.
        if isinstance(parsed.get("languages"), list) and parsed["languages"]:
            result["languages"] = parsed["languages"]
        result["ai_summary"] = parsed.get("summary", "")
        result["ai_recommendations"] = parsed.get("recommendations", [])
        result["submission_assessment"] = parsed.get("submission", {})
        result["deployment_assessment"] = parsed.get("deployment", {})
        result["quality_assessment"] = parsed.get("quality", {})
    except Exception as exc:
        result["ai_analysis"] = {"summary": "Gemini analysis could not be completed.", "error": str(exc)[:300]}
        result["ai_available"] = False
    return result
