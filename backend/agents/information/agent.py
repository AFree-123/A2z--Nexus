"""
Information Agent — answers general technical questions.

Works with or without a project context.
Called directly by the orchestrator for informational queries.
"""
from __future__ import annotations

from services.ai_service import AIResponse, BaseAIProvider, Message

SYSTEM_PROMPT = """You are A2Z Nexus — an expert AI assistant for developers and engineers.

Your role is to answer technical questions clearly and accurately.

Guidelines:
- Give precise, correct answers backed by technical knowledge.
- Use code examples when they help understanding.
- Keep answers concise but complete.
- If a question is ambiguous, clarify before answering.
- Never make up facts. If you don't know something, say so.
- Format responses in Markdown where appropriate.
"""


class InformationAgent:
    """
    Answers general technical questions.

    Examples of what this handles:
      - "What is a REST API?"
      - "Explain React hooks."
      - "Why does this Python error happen?"
      - "What is the difference between async and sync?"
    """

    def __init__(self, ai: BaseAIProvider) -> None:
        self._ai = ai

    async def answer(
        self,
        question: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> AIResponse:
        """
        Answer a technical question.

        Args:
            question: The user's question.
            conversation_history: Optional list of prior messages
                                   [{"role": "user"|"assistant", "content": "..."}]

        Returns:
            AIResponse with the answer.
        """
        messages: list[Message] = []

        # Include prior conversation turns for context
        if conversation_history:
            for turn in conversation_history[-10:]:  # last 10 turns max
                messages.append(Message(role=turn["role"], content=turn["content"]))

        messages.append(Message(role="user", content=question))

        return await self._ai.chat(
            messages=messages,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=1024,
        )
