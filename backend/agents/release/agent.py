"""
Release Agent — checks project readiness for release/deployment.

Checks:
  - build status
  - tests passing
  - dependencies
  - environment variables configured
  - deployment configuration
  - critical issues
  - documentation

Returns:
  - ready: bool
  - passed_checks
  - warnings
  - blocking_issues
  - recommended_actions

Does NOT perform real deployment without explicit instruction.
"""
from __future__ import annotations

import os
from pathlib import Path

from services.ai_service import BaseAIProvider, Message

RELEASE_SYSTEM_PROMPT = """You are a senior DevOps engineer performing a release readiness check.

Given a project analysis, determine if the project is ready for release.

Output STRICT JSON (no markdown):
{
  "ready": true | false,
  "passed_checks": ["list of checks that passed"],
  "warnings": ["list of non-blocking concerns"],
  "blocking_issues": ["list of issues that MUST be fixed before release"],
  "recommended_actions": ["ordered list of what to do"],
  "release_score": 0-100,
  "summary": "2-3 sentence assessment"
}

A project is "ready" only if there are NO blocking issues.
Base your assessment only on the evidence provided. Do not invent data.
"""

# Release checklist
RELEASE_CHECKS = [
    ("has_source",        "Source code present"),
    ("has_tests",         "Test files present"),
    ("has_readme",        "README.md present"),
    ("has_env_example",   ".env.example template present"),
    ("has_gitignore",     ".gitignore present"),
    ("no_env_committed",  ".env NOT committed to version control"),
    ("has_docker",        "Docker configuration present"),
    ("has_ci",            "CI/CD configuration present"),
]


class ReleaseAgent:
    """Checks project readiness for production release."""

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
        Check release readiness.

        Returns structured result with passed_checks, warnings, blocking_issues.
        """
        path = Path(project_path) if project_path else None
        heuristic = self._heuristic_check(path)
        context = self._build_context(
            project_name or (path.name if path else "Unknown"),
            heuristic, code_analysis, test_results
        )

        response = await self._ai.chat(
            messages=[Message("user", context)],
            system_prompt=RELEASE_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=1024,
        )

        return self._parse_result(response.content)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _heuristic_check(self, path: Path | None) -> dict:
        if path is None or not path.exists():
            return {
                "accessible": False,
                "checks": {k: False for k, _ in RELEASE_CHECKS},
            }

        checks: dict[str, bool] = {}

        # Source code
        code_exts = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb"}
        has_source = any(
            Path(dp, f).suffix in code_exts
            for dp, _, files in os.walk(path)
            for f in files
            if not any(s in dp for s in ["node_modules", ".git", ".venv"])
        )
        checks["has_source"] = has_source

        # Tests
        checks["has_tests"] = any(
            "test" in f.lower()
            for _, _, files in os.walk(path)
            for f in files
        )

        # Common files
        checks["has_readme"] = (path / "README.md").exists() or (path / "README.rst").exists()
        checks["has_env_example"] = (path / ".env.example").exists()
        checks["has_gitignore"] = (path / ".gitignore").exists()

        # .env should NOT exist in repo root (security)
        checks["no_env_committed"] = not (path / ".env").exists()

        # Docker
        checks["has_docker"] = (path / "Dockerfile").exists() or (path / "docker-compose.yml").exists()

        # CI/CD
        ci_paths = [
            ".github/workflows", ".gitlab-ci.yml", "Jenkinsfile",
            ".circleci/config.yml", ".travis.yml",
        ]
        checks["has_ci"] = any((path / ci).exists() for ci in ci_paths)

        return {"accessible": True, "checks": checks}

    def _build_context(
        self, project_name: str, heuristic: dict,
        code_analysis: dict | None, test_results: dict | None
    ) -> str:
        lines = [f"Project: {project_name}\n", "## Release Checklist Results"]
        checks = heuristic.get("checks", {})
        for key, label in RELEASE_CHECKS:
            status = "✅ PASS" if checks.get(key, False) else "❌ FAIL"
            lines.append(f"- {status}: {label}")

        if code_analysis:
            lines.append("\n## Code Analysis")
            lines.append(f"- Languages: {', '.join(code_analysis.get('languages', []))}")
            issues = code_analysis.get("issues", [])
            high_issues = [i for i in issues if i.get("severity") in ("HIGH", "CRITICAL")]
            if high_issues:
                lines.append(f"- High severity issues: {len(high_issues)}")
                for i in high_issues:
                    lines.append(f"  - {i['issue']}")

        if test_results:
            lines.append("\n## Test Results")
            lines.append(f"- Framework: {test_results.get('framework', 'unknown')}")
            lines.append(f"- Total: {test_results.get('total', 0)}")
            lines.append(f"- Passed: {test_results.get('passed', 0)}")
            lines.append(f"- Failed: {test_results.get('failed', 0)}")
            if test_results.get("failed", 0) > 0:
                lines.append("  ⚠️ Failing tests are a BLOCKING issue for release.")

        lines.append("\nDetermine release readiness based on this data.")
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
                "ready": bool(data.get("ready", False)),
                "passed_checks": list(data.get("passed_checks", [])),
                "warnings": list(data.get("warnings", [])),
                "blocking_issues": list(data.get("blocking_issues", [])),
                "recommended_actions": list(data.get("recommended_actions", [])),
                "release_score": float(data.get("release_score", 0)),
                "summary": str(data.get("summary", "")),
            }
        except (json.JSONDecodeError, TypeError):
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                try:
                    return ReleaseAgent._parse_result(match.group(0))
                except Exception:
                    pass
        return {
            "ready": False,
            "passed_checks": [],
            "warnings": [],
            "blocking_issues": ["Unable to parse release check result"],
            "recommended_actions": ["Retry release check"],
            "release_score": 0.0,
            "summary": "Release check could not be completed.",
        }
