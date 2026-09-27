"""
Documentation Agent — generates README, setup guide, API docs, architecture docs, changelog.
"""
from __future__ import annotations

from services.ai_service import BaseAIProvider, Message

DOC_PROMPTS: dict[str, str] = {
    "readme": """Generate a professional README.md for this project.

Include:
- Project title and tagline
- Brief description (2-3 sentences)
- Features list
- Prerequisites
- Installation / Setup steps
- Usage examples
- API overview (if applicable)
- Contributing guide (brief)
- License

Use Markdown. Be specific and accurate based on the project info provided.
Do not invent features or steps not supported by the project data.""",

    "setup": """Generate a detailed setup guide for this project.

Include:
- Prerequisites (exact versions where known)
- Step-by-step installation
- Environment variable configuration
- Database setup (if applicable)
- Running in development mode
- Running tests
- Common setup issues and solutions

Be accurate. Only include steps that are supported by the project info.""",

    "api": """Generate API documentation for this project.

Format:
- For each endpoint: method, path, description, request body, response, example
- Group by resource/category
- Include authentication requirements if evident
- Include error responses

Only document APIs that are evident from the project analysis.
Use Markdown with proper code blocks.""",

    "architecture": """Generate an architecture document for this project.

Include:
- System overview
- Component diagram (text-based or Mermaid)
- Technology stack
- Data flow description
- Key design decisions
- Database schema overview (if applicable)

Base everything on the project analysis provided.""",

    "changelog": """Generate an initial CHANGELOG.md for this project.

Format:
## [Unreleased]
### Added
### Changed
### Fixed

## [0.1.0] - Initial Release
### Added
- List the main features evident from the project

Follow Keep-a-Changelog format.""",
}

SYSTEM_PROMPT = """You are a technical writer and software engineer.
Generate accurate, professional documentation based on the project information provided.
Do not invent technical details not supported by the project data.
Use Markdown formatting."""


class DocumentationAgent:
    """Generates various types of project documentation."""

    def __init__(self, ai: BaseAIProvider) -> None:
        self._ai = ai

    async def generate(
        self,
        doc_type: str,
        project_name: str,
        project_context: str,
    ) -> dict:
        """
        Generate a documentation artifact.

        Args:
            doc_type: One of: readme | setup | api | architecture | changelog
            project_name: Project name
            project_context: Stringified project data (from code analysis, etc.)

        Returns:
            {"doc_type": str, "content": str, "project_name": str}
        """
        prompt_template = DOC_PROMPTS.get(doc_type, DOC_PROMPTS["readme"])

        user_message = (
            f"Project: {project_name}\n\n"
            f"Project context:\n{project_context[:3000]}\n\n"
            f"{prompt_template}"
        )

        response = await self._ai.chat(
            messages=[Message("user", user_message)],
            system_prompt=SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=2048,
        )
        return {
            "doc_type": doc_type,
            "content": response.content,
            "project_name": project_name,
        }
