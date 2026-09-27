"""
Abstract AI service layer.

Supports:
  - gemini   → Google Gemini REST API
  - openai / anthropic → optional provider adapters retained for compatibility
  - mock      → Deterministic offline responses for development/testing

Select the provider via AI_PROVIDER in .env.
Never expose credentials outside this module.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Message:
    """A single chat message."""

    def __init__(self, role: str, content: str) -> None:
        self.role = role
        self.content = content

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


class AIResponse:
    """Normalized response from any AI provider."""

    def __init__(self, content: str, model: str, provider: str, usage: dict[str, int] | None = None) -> None:
        self.content = content
        self.model = model
        self.provider = provider
        self.usage = usage or {}


class BaseAIProvider(ABC):
    """All provider adapters implement this interface."""

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AIResponse:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...


# ---------------------------------------------------------------------------
# Mock provider  (development / testing, no external calls)
# ---------------------------------------------------------------------------

class MockAIProvider(BaseAIProvider):
    """Returns deterministic responses for offline development."""

    def is_available(self) -> bool:
        return True

    async def chat(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AIResponse:
        last_user = next(
            (m.content for m in reversed(messages) if m.role == "user"), ""
        )
        # The orchestrator also calls chat() to classify intent (it expects a
        # single Intent label back, e.g. "code_analysis"). Without this branch,
        # the mock provider always returned a full mock paragraph instead of a
        # label, which never matches an Intent enum value, so every message
        # not hit by the keyword fast-path fell through to "unknown" and the
        # user got a generic "I'm not sure what you'd like me to do" reply
        # even for very ordinary phrasing like "analyze my project".
        if system_prompt and "intent classifier" in system_prompt.lower():
            content = self._mock_intent_guess(last_user)
        elif system_prompt and "deadline and task detector" in system_prompt.lower():
            content = self._mock_reminder_detect(last_user)
        else:
            content = self._mock_response(last_user)
        return AIResponse(content=content, model="mock", provider="mock")

    def _mock_reminder_detect(self, user_message: str) -> str:
        """Mirrors ReminderAgent.DETECT_SYSTEM_PROMPT's expected JSON shape,
        using plain keyword/regex matching so reminders still work end-to-end
        without a real AI key configured."""
        import json as _json
        import re as _re

        # detect_from_message() wraps the real message inside a bigger prompt
        # ("Today's date: ...\n\nUser message:\n\"<msg>\"\n\nDetect any...").
        # Pull the real message back out so the saved title/description don't
        # end up containing that whole wrapper prompt.
        wrapped = _re.search(r'User message:\s*\n"(.*)"\s*\n\nDetect', user_message, _re.DOTALL)
        clean_message = wrapped.group(1) if wrapped else user_message

        msg = clean_message.lower()
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        relative_phrase = None
        for day in weekdays:
            if day in msg:
                relative_phrase = day if f"next {day}" not in msg else f"next {day}"
                break
        if not relative_phrase:
            for phrase in ("tomorrow", "next week", "in two weeks", "in 2 weeks", "next month"):
                if phrase in msg:
                    relative_phrase = phrase
                    break

        date_match = _re.search(r"\b\d{4}-\d{2}-\d{2}\b", clean_message)
        due_date = date_match.group(0) if date_match else None

        has_deadline_word = any(
            w in msg for w in ["deadline", "due", "submit", "submission", "remind", "release", "demo", "meeting"]
        )

        if not (relative_phrase or due_date or has_deadline_word):
            return _json.dumps({"detected": False, "items": [], "confirmation_prompt": None})

        title = clean_message.strip()[:60] or "Reminder"
        item_type = "submission" if "submi" in msg else "demo" if "demo" in msg else "release" if "release" in msg else "general"
        item = {
            "type": item_type,
            "title": title,
            "description": clean_message,
            "due_date": due_date,
            "relative_description": relative_phrase,
            "confidence": "medium",
        }
        return _json.dumps({
            "detected": True,
            "items": [item],
            "confirmation_prompt": f"Would you like me to create a reminder for '{title}'?",
        })

    def _mock_intent_guess(self, user_message: str) -> str:
        msg = user_message.lower()
        guesses = [
            (["analy", "project", "code", "scan", "review"], "code_analysis"),
            (["test"], "testing"),
            (["improve", "recommend", "better", "fix"], "recommendation"),
            (["readme", "doc"], "documentation"),
            (["pitch", "presentation", "abstract", "slide"], "content"),
            (["narrat", "demo script"], "narration"),
            (["remind", "deadline", "due", "submit by"], "reminder"),
            (["ready to submit", "submission"], "submission"),
            (["ready to release", "release", "deploy"], "release"),
        ]
        for keywords, intent in guesses:
            if any(k in msg for k in keywords):
                return intent
        return "information"

    def _mock_response(self, user_message: str) -> str:
        msg = user_message.lower()
        if any(w in msg for w in ["analyze", "analysis", "project", "code"]):
            return (
                "**[Mock — Code Analysis]**\n\n"
                "This is a mock analysis response.\n"
                "- Project structure: detected\n"
                "- Languages: Python, TypeScript\n"
                "- Issues found: 0 (mock)\n\n"
                "_Set AI_PROVIDER=gemini and provide GEMINI_API_KEY for real analysis._"
            )
        if any(w in msg for w in ["test", "testing", "pytest"]):
            return (
                "**[Mock — Testing]**\n\n"
                "Mock test report: 5 tests detected, 5 passed.\n\n"
                "_Set AI_PROVIDER to a real provider for actual test execution._"
            )
        if any(w in msg for w in ["recommend", "improve", "better"]):
            return (
                "**[Mock — Recommendations]**\n\n"
                "Mock recommendations:\n"
                "- HIGH: Add unit tests\n"
                "- MEDIUM: Improve documentation\n"
                "- LOW: Add input validation\n\n"
                "_Set AI_PROVIDER to a real provider for project-specific recommendations._"
            )
        if any(w in msg for w in ["readme", "doc", "documentation"]):
            return (
                "**[Mock — Documentation]**\n\n"
                "# Project Name\n\nA mock README was generated.\n\n"
                "## Setup\n\n```bash\nnpm install\n```\n\n"
                "_Set AI_PROVIDER to a real provider for real documentation._"
            )
        if any(w in msg for w in ["reminder", "deadline", "submit", "friday"]):
            return (
                "**[Mock — Reminder]**\n\n"
                "I detected a deadline in your message. "
                "Would you like me to create a reminder?\n\n"
                "_Set AI_PROVIDER to a real provider for intelligent deadline detection._"
            )
        # Generic fallback
        return (
            f"**[Mock AI Response]**\n\n"
            f"You said: *\"{user_message[:200]}\"*\n\n"
            f"This is a mock response. The AI Orchestrator will route your request "
            f"to the appropriate specialized agent once the orchestrator is connected (Phase 13).\n\n"
            f"Set `AI_PROVIDER=openai` (or `anthropic`) in `.env` and provide "
            f"an API key for real AI responses."
        )


# ---------------------------------------------------------------------------
# OpenAI provider
# ---------------------------------------------------------------------------

class OpenAIProvider(BaseAIProvider):
    """OpenAI Chat Completions (gpt-4o, gpt-4-turbo, gpt-3.5-turbo, etc.)"""

    def __init__(self) -> None:
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from openai import AsyncOpenAI  # type: ignore[import]
                self._client = AsyncOpenAI(api_key=settings.AI_API_KEY)
            except ImportError:
                raise RuntimeError("openai package not installed.")
        return self._client

    def is_available(self) -> bool:
        return bool(settings.AI_API_KEY)

    async def chat(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AIResponse:
        client = self._get_client()
        openai_messages = []
        if system_prompt:
            openai_messages.append({"role": "system", "content": system_prompt})
        openai_messages.extend([m.to_dict() for m in messages])

        response = await client.chat.completions.create(
            model=settings.AI_MODEL,
            messages=openai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content or ""
        usage = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
        }
        return AIResponse(content=content, model=settings.AI_MODEL, provider="openai", usage=usage)


# ---------------------------------------------------------------------------
# Anthropic provider
# ---------------------------------------------------------------------------

class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude (claude-3-5-sonnet, claude-3-haiku, etc.)"""

    def __init__(self) -> None:
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                import anthropic as _anthropic  # type: ignore[import]
                self._client = _anthropic.AsyncAnthropic(api_key=settings.AI_API_KEY)
            except ImportError:
                raise RuntimeError("anthropic package not installed.")
        return self._client

    def is_available(self) -> bool:
        return bool(settings.AI_API_KEY)

    async def chat(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AIResponse:
        client = self._get_client()
        anthropic_messages = [m.to_dict() for m in messages if m.role != "system"]
        kwargs: dict[str, Any] = dict(
            model=settings.AI_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=anthropic_messages,
        )
        if system_prompt:
            kwargs["system"] = system_prompt

        response = await client.messages.create(**kwargs)
        content = response.content[0].text if response.content else ""
        return AIResponse(content=content, model=settings.AI_MODEL, provider="anthropic")


# ---------------------------------------------------------------------------
# Gemini provider (current Google Gen AI SDK)
# ---------------------------------------------------------------------------

class GeminiProvider(BaseAIProvider):
    """
    Google Gemini provider using the current `google-genai` SDK.

    The SDK handles the current Gemini API transport and model routing.
    Credentials are read only from GEMINI_API_KEY in the local environment.
    """

    def is_available(self) -> bool:
        return bool(settings.GEMINI_API_KEY and settings.GEMINI_MODEL)

    async def chat(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AIResponse:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError(
                "Gemini SDK is not installed. Run: "
                "python -m pip install -r backend/requirements.txt"
            ) from exc

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        # Keep the existing provider interface unchanged. The orchestrator can
        # continue passing Message objects while the SDK receives one prompt.
        conversation_parts: list[str] = []
        for message in messages:
            conversation_parts.append(
                f"{message.role.upper()}:\n{message.content}"
            )
        prompt = "\n\n".join(conversation_parts).strip()

        config_kwargs: dict[str, Any] = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if system_prompt:
            config_kwargs["system_instruction"] = system_prompt

        models = [settings.GEMINI_MODEL]
        if (
            settings.GEMINI_FALLBACK_MODEL
            and settings.GEMINI_FALLBACK_MODEL not in models
        ):
            models.append(settings.GEMINI_FALLBACK_MODEL)

        last_error: Exception | None = None

        try:
            for model in models:
                try:
                    response = await client.aio.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(**config_kwargs),
                    )
                    content = (response.text or "").strip()
                    if content:
                        return AIResponse(
                            content=content,
                            model=model,
                            provider="gemini",
                        )
                    last_error = RuntimeError(
                        f"Gemini returned an empty response from model {model}."
                    )
                except Exception as exc:
                    last_error = exc
                    logger.warning(
                        "Gemini model %s failed; trying fallback if configured: %s",
                        model,
                        exc,
                    )
        finally:
            # Close the async transport created by the SDK.
            try:
                await client.aio.aclose()
            except Exception:
                pass

        raise RuntimeError(
            "Gemini request failed for primary/fallback models. "
            f"Last error: {last_error}"
        )
# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_ai_provider() -> BaseAIProvider:
    """Return the configured AI provider instance."""
    provider = settings.AI_PROVIDER.lower()
    if provider == "openai":
        p = OpenAIProvider()
    elif provider == "anthropic":
        p = AnthropicProvider()
    elif provider == "gemini":
        p = GeminiProvider()
    else:
        p = MockAIProvider()

    if not isinstance(p, MockAIProvider) and not p.is_available():
        logger.warning(
            "AI provider '%s' selected but required credentials are missing. Falling back to mock.",
            provider,
        )
        return MockAIProvider()

    logger.info("AI provider: %s", provider)
    return p


# ---------------------------------------------------------------------------
# Singleton — one instance per process
# ---------------------------------------------------------------------------
_provider: BaseAIProvider | None = None


def ai_provider() -> BaseAIProvider:
    global _provider
    if _provider is None:
        _provider = get_ai_provider()
    return _provider
