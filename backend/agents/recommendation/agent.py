"""
Project Improvement Recommendation Agent.

Uses findings from Code Analysis, Testing, Documentation, and project metadata
to generate specific, evidence-based recommendations.

This is NOT a course/job recommendation system.
Purpose: "How can I make this project better?"
"""
from __future__ import annotations

from services.ai_service import BaseAIProvider, Message

RECOMMENDATION_SYSTEM_PROMPT = """You are a senior software engineer reviewing a project for quality and completeness.

You will receive structured findings from multiple agents:
- Code analysis results
- Test results
- Documentation status
- Project metadata

Your job is to produce a PRIORITIZED list of specific, actionable improvements.

Output format — STRICT JSON array:
[
  {
    "priority": "HIGH" | "MEDIUM" | "LOW",
    "category": "testing" | "code_quality" | "documentation" | "security" | "performance" | "architecture" | "configuration" | "deployment",
    "title": "Short title (max 60 chars)",
    "description": "Specific description referencing actual evidence from the findings"
  }
]

Rules:
- Every recommendation MUST reference specific evidence from the findings.
- Do NOT invent problems not supported by the data.
- HIGH = blocks submission/release or has security implications.
- MEDIUM = important for quality, correctness, or maintainability.
- LOW = nice-to-have improvements.
- Maximum 10 recommendations. Focus on the most impactful.
- Output ONLY the JSON array — no markdown fences, no explanations outside the JSON.
"""


class RecommendationAgent:
    """
    Generates project-specific improvement recommendations based on
    evidence from code analysis, testing, and documentation findings.
    """

    def __init__(self, ai: BaseAIProvider) -> None:
        self._ai = ai

    async def recommend(
        self,
        project_name: str,
        code_analysis: dict | None = None,
        test_results: dict | None = None,
        documentation_status: dict | None = None,
        project_metadata: dict | None = None,
    ) -> list[dict]:
        """
        Generate recommendations from aggregated agent findings.

        Returns a list of recommendation dicts:
          [{"priority": "HIGH", "category": "...", "title": "...", "description": "..."}, ...]
        """
        context = self._build_context(
            project_name, code_analysis, test_results,
            documentation_status, project_metadata
        )

        response = await self._ai.chat(
            messages=[Message("user", context)],
            system_prompt=RECOMMENDATION_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=2048,
        )

        return self._parse_recommendations(response.content)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_context(
        self,
        project_name: str,
        code_analysis: dict | None,
        test_results: dict | None,
        documentation_status: dict | None,
        project_metadata: dict | None,
    ) -> str:
        parts = [f"# Project: {project_name}\n"]

        if code_analysis:
            parts.append("## Code Analysis Findings")
            parts.append(f"- Languages: {', '.join(code_analysis.get('languages', []))}")
            parts.append(f"- Frameworks: {', '.join(code_analysis.get('frameworks', []))}")
            parts.append(f"- Files: {code_analysis.get('file_count', 0)}")
            issues = code_analysis.get("issues", [])
            if issues:
                parts.append("- Pre-scan issues:")
                for issue in issues:
                    parts.append(f"  - [{issue.get('severity', '?')}] {issue.get('issue', '')}")
            ai_analysis = code_analysis.get("ai_analysis", "")
            if ai_analysis:
                parts.append(f"\nAI Code Review Summary:\n{ai_analysis[:2000]}")
            parts.append("")

        if test_results:
            parts.append("## Test Results")
            parts.append(f"- Framework: {test_results.get('framework', 'unknown')}")
            parts.append(f"- Total: {test_results.get('total', 0)}")
            parts.append(f"- Passed: {test_results.get('passed', 0)}")
            parts.append(f"- Failed: {test_results.get('failed', 0)}")
            parts.append(f"- Skipped: {test_results.get('skipped', 0)}")
            if test_results.get("error"):
                parts.append(f"- Error: {test_results['error']}")
            if test_results.get("explanation"):
                parts.append(f"- Failure explanation: {test_results['explanation'][:500]}")
            parts.append("")

        if documentation_status:
            parts.append("## Documentation Status")
            for key, value in documentation_status.items():
                parts.append(f"- {key}: {value}")
            parts.append("")

        if project_metadata:
            parts.append("## Project Metadata")
            for key, value in project_metadata.items():
                parts.append(f"- {key}: {value}")
            parts.append("")

        if not any([code_analysis, test_results, documentation_status]):
            parts.append(
                "No agent findings available. Provide general recommendations "
                "for a well-structured software project."
            )

        return "\n".join(parts)

    @staticmethod
    def _parse_recommendations(content: str) -> list[dict]:
        """Parse the JSON array from AI response. Gracefully handle malformed output."""
        import json
        import re

        # Try to extract JSON array from the response
        content = content.strip()

        # Remove markdown code fences if present
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
        content = content.strip()

        try:
            data = json.loads(content)
            if isinstance(data, list):
                # Validate and normalize each item
                validated = []
                for item in data:
                    if isinstance(item, dict) and "title" in item:
                        validated.append({
                            "priority": item.get("priority", "MEDIUM").upper(),
                            "category": item.get("category", "general"),
                            "title": str(item.get("title", ""))[:100],
                            "description": str(item.get("description", "")),
                        })
                return validated
        except json.JSONDecodeError:
            pass

        # Fallback: try to find JSON array embedded in text
        match = re.search(r"\[.*\]", content, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                pass

        # Last resort: return a single generic recommendation noting parse failure
        return [{
            "priority": "MEDIUM",
            "category": "general",
            "title": "Review AI analysis output",
            "description": f"AI response could not be parsed as structured recommendations. Raw: {content[:300]}",
        }]
