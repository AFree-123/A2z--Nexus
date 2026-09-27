"""
Content Agent — generates project descriptions, abstracts, problem/solution statements,
presentation content, release notes.
"""
from __future__ import annotations

from services.ai_service import BaseAIProvider, Message

CONTENT_PROMPTS: dict[str, str] = {
    "description": "Write a compelling 2-3 sentence project description suitable for a portfolio or GitHub About section.",
    "abstract": "Write a formal 150-word academic-style abstract for this project.",
    "problem_statement": "Write a clear problem statement explaining what problem this project solves and who it affects.",
    "solution_statement": "Write a solution statement explaining how this project solves the identified problem.",
    "presentation": """Create presentation slide content for this project.

Format:
# Slide 1: Title
# Slide 2: Problem
# Slide 3: Solution
# Slide 4: Demo / Features
# Slide 5: Technical Architecture
# Slide 6: Impact / Results
# Slide 7: Next Steps

Keep each slide to 3-5 bullet points.""",

    "release_notes": """Write release notes for this project.

Format:
## Version X.X.X

### New Features
### Bug Fixes
### Breaking Changes
### Improvements

Be specific about what changed based on the project info.""",

    "elevator_pitch": "Write a 30-second elevator pitch for this project (max 80 words).",

    "hackathon_submission": """Write a hackathon submission description for this project.

Include:
- Project name and tagline
- Problem being solved
- Solution approach
- Key technical innovations
- Demo description
- Team / tools used

Keep it compelling and under 300 words.""",
}

SYSTEM_PROMPT = """You are a technical content writer specializing in developer tools and software products.
Create compelling, accurate content based on the project information provided.
Do not exaggerate or invent capabilities not supported by the project data."""


class ContentAgent:
    """Generates marketing and presentation content for projects."""

    def __init__(self, ai: BaseAIProvider) -> None:
        self._ai = ai

    async def generate(
        self,
        content_type: str,
        project_name: str,
        project_context: str,
    ) -> dict:
        """
        Generate content of the specified type.

        Args:
            content_type: One of the keys in CONTENT_PROMPTS
            project_name: Project name
            project_context: Project description / analysis context

        Returns:
            {"content_type": str, "content": str, "project_name": str}
        """
        prompt = CONTENT_PROMPTS.get(content_type, CONTENT_PROMPTS["description"])

        user_message = (
            f"Project: {project_name}\n\n"
            f"Context:\n{project_context[:2000]}\n\n"
            f"Task: {prompt}"
        )

        response = await self._ai.chat(
            messages=[Message("user", user_message)],
            system_prompt=SYSTEM_PROMPT,
            temperature=0.5,
            max_tokens=1024,
        )
        return {
            "content_type": content_type,
            "content": response.content,
            "project_name": project_name,
        }
