"""
Submission Agent — checks project readiness for submission.

Checks (where applicable):
  - source code present
  - README exists
  - documentation
  - tests exist and passing
  - demo URL
  - presentation
  - required configuration

Returns:
  - completed items
  - missing items
  - warnings
  - readiness percentage (0-100)
  - next actions

Never invents completion status.
"""
from __future__ import annotations

import os
from pathlib import Path

from services.ai_service import BaseAIProvider, Message

SUBMISSION_SYSTEM_PROMPT = """You are a project submission reviewer.

Given a project analysis, determine submission readiness.

Output STRICT JSON (no markdown):
{
  "readiness_percentage": 0-100,
  "completed": ["list of completed items"],
  "missing": ["list of missing required items"],
  "warnings": ["list of optional items not done"],
  "next_actions": ["prioritized list of what to do next"],
  "summary": "2-3 sentence overall assessment"
}

Base your assessment ONLY on the evidence provided. Do not invent completion status.
"""


# Submission checklist items
CHECKLIST = [
    ("readme",          "README.md",          True,  "README.md documentation"),
    ("source_code",     "source_files",       True,  "Source code files"),
    ("tests",           "test_files",         False, "Test files"),
    ("env_example",     ".env.example",       False, ".env.example template"),
    ("gitignore",       ".gitignore",         False, ".gitignore file"),
    ("license",         "LICENSE",            False, "LICENSE file"),
    ("dockerfile",      "Dockerfile",         False, "Dockerfile / Docker config"),
]


class SubmissionAgent:
    """Checks a project for submission readiness."""

    def __init__(self, ai: BaseAIProvider) -> None:
        self._ai = ai

    async def check(
        self,
        project_path: str,
        project_name: str = "",
        code_analysis: dict | None = None,
        test_results: dict | None = None,
    ) -> dict:
        """
        Check submission readiness.

        Returns structured result with readiness percentage, completed, missing, warnings.
        """
        path = Path(project_path) if project_path else None
        heuristic = self._heuristic_check(path)
        context = self._build_context(
            project_name or (path.name if path else "Unknown"),
            heuristic, code_analysis, test_results
        )

        response = await self._ai.chat(
            messages=[Message("user", context)],
            system_prompt=SUBMISSION_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=1024,
        )

        result = self._parse_result(response.content)

        # Override readiness percentage if path was invalid
        if path and not path.exists():
            result["readiness_percentage"] = 0.0
            result["missing"].insert(0, "Project path not accessible")

        return result

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _heuristic_check(self, path: Path | None) -> dict:
        """Quick filesystem checks without AI."""
        if path is None or not path.exists():
            return {"accessible": False, "files_found": [], "files_missing": [c[3] for c in CHECKLIST], "files_warnings": []}

        found = []
        missing = []
        warnings = []

        # Check for README
        if (path / "README.md").exists() or (path / "README.rst").exists():
            found.append("README.md")
        else:
            missing.append("README.md")

        # Check for source code (any code files)
        code_exts = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb", ".php", ".cs"}
        has_source = False
        for dirpath, dirnames, filenames in os.walk(path):
            dirnames[:] = [d for d in dirnames if d not in {"node_modules", ".git", ".venv", "venv", "__pycache__"}]
            for f in filenames:
                if Path(f).suffix in code_exts:
                    has_source = True
                    break
            if has_source:
                break
        if has_source:
            found.append("Source code files")
        else:
            missing.append("Source code files")

        # Check for tests
        has_tests = any(
            "test" in str(p).lower()
            for p in path.rglob("*.py")
            if "test" in p.name.lower()
        )
        if has_tests:
            found.append("Test files")
        else:
            warnings.append("No test files detected")

        # Check other files
        for _, filename, _, label in CHECKLIST[2:]:  # skip readme + source already checked
            if (path / filename).exists():
                found.append(label)
            else:
                warnings.append(f"Missing: {label}")

        return {
            "accessible": True,
            "files_found": found,
            "files_missing": missing,
            "files_warnings": warnings,
        }

    def _build_context(
        self, project_name: str, heuristic: dict,
        code_analysis: dict | None, test_results: dict | None
    ) -> str:
        lines = [f"Project: {project_name}\n"]
        lines.append("## File System Check")
        lines.append(f"- Accessible: {heuristic.get('accessible', False)}")
        lines.append(f"- Found: {', '.join(heuristic.get('files_found', []))}")
        lines.append(f"- Missing: {', '.join(heuristic.get('files_missing', []))}")
        lines.append(f"- Warnings: {', '.join(heuristic.get('files_warnings', []))}")

        if code_analysis:
            lines.append("\n## Code Analysis")
            lines.append(f"- Languages: {', '.join(code_analysis.get('languages', []))}")
            lines.append(f"- File count: {code_analysis.get('file_count', 0)}")

        if test_results:
            lines.append("\n## Test Results")
            lines.append(f"- Framework: {test_results.get('framework', 'unknown')}")
            lines.append(f"- Passed: {test_results.get('passed', 0)}/{test_results.get('total', 0)}")
            lines.append(f"- Failed: {test_results.get('failed', 0)}")

        lines.append("\nAssess submission readiness based on this data.")
        return "\n".join(lines)

    @staticmethod
    def _parse_result(content: str) -> dict:
        import json, re  # noqa: E401
        content = content.strip()
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content).strip()
        try:
            data = json.loads(content)
            return {
                "readiness_percentage": float(data.get("readiness_percentage", 0)),
                "completed": list(data.get("completed", [])),
                "missing": list(data.get("missing", [])),
                "warnings": list(data.get("warnings", [])),
                "next_actions": list(data.get("next_actions", [])),
                "summary": str(data.get("summary", "")),
            }
        except (json.JSONDecodeError, TypeError):
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                try:
                    return SubmissionAgent._parse_result(match.group(0))
                except Exception:
                    pass
        return {
            "readiness_percentage": 0.0,
            "completed": [],
            "missing": ["Unable to parse submission check result"],
            "warnings": [],
            "next_actions": ["Retry submission check"],
            "summary": "Submission check could not be completed.",
        }
