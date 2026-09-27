"""
Narration Agent — generates demo scripts, presentation narration, feature explanations.
"""
from __future__ import annotations

from services.ai_service import BaseAIProvider, Message

NARRATION_PROMPTS: dict[str, str] = {
    "demo": """Write a live demo narration script for this project.

Format it as a presenter speaking to an audience.

Include:
1. Opening hook (30 seconds)
2. Problem context (1 minute)
3. Demo walkthrough — step-by-step with exact spoken words
4. Key feature highlights
5. Closing statement (30 seconds)

Make it natural, engaging, and technically accurate.
Estimated total: 3-5 minutes of spoken content.""",

    "presentation": """Write full slide-by-slide presentation narration for this project.

For each slide, write exactly what the presenter should say.
Keep each slide section to 1-2 minutes of spoken content.
Total presentation: 10-15 minutes.""",

    "feature": """Write engaging feature explanation narration.

For each major feature:
1. What it does (1 sentence)
2. Why it matters (1-2 sentences)
3. How it works at a high level (2-3 sentences)

Make it accessible to both technical and non-technical audiences.""",

    "tutorial": """Write a step-by-step tutorial narration for getting started with this project.

Include:
1. Introduction
2. Prerequisites check
3. Setup walkthrough (narrated)
4. First usage example
5. Next steps

Use a friendly, encouraging tone.""",
}

SYSTEM_PROMPT = """You are a professional technical presenter and developer advocate.
Create natural, engaging narration that is technically accurate and audience-appropriate.
Use a confident, conversational tone. Avoid filler words and jargon without explanation."""


class NarrationAgent:
    """Generates spoken narration scripts for demos and presentations."""

    def __init__(self, ai: BaseAIProvider) -> None:
        self._ai = ai

    async def generate(
        self,
        narration_for: str,
        project_name: str,
        project_context: str,
    ) -> dict:
        """
        Generate narration script.

        Args:
            narration_for: One of: demo | presentation | feature | tutorial
            project_name: Project name
            project_context: Project description / analysis context

        Returns:
            {"narration_for": str, "script": str, "project_name": str}
        """
        prompt = NARRATION_PROMPTS.get(narration_for, NARRATION_PROMPTS["demo"])

        user_message = (
            f"Project: {project_name}\n\n"
            f"Context:\n{project_context[:2000]}\n\n"
            f"Task: {prompt}"
        )

        response = await self._ai.chat(
            messages=[Message("user", user_message)],
            system_prompt=SYSTEM_PROMPT,
            temperature=0.6,
            max_tokens=2048,
        )
        return {
            "narration_for": narration_for,
            "script": response.content,
            "project_name": project_name,
        }
