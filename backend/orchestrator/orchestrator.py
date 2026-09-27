"""
AI Orchestrator — central brain of A2Z Nexus.

Responsibilities:
1. Receive user request
2. Understand intent (classify)
3. Detect project context
4. Select required agent(s)
5. Execute workflow (single or multi-agent)
6. Combine results
7. Return one clear response

Routing examples:
  "What is REST API?"        → Information Agent
  "Analyze my project"       → Code Analysis
  "Generate tests"           → Testing
  "Improve my project"       → Code Analysis → Testing → Recommendation
  "Prepare for submission"   → Code Analysis → Testing → Submission
  "Check release readiness"  → Testing → Release
  "Submission is Friday"     → Reminder
  "Generate README"          → Documentation
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from services.ai_service import BaseAIProvider, Message
from utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Intent classification
# ---------------------------------------------------------------------------

class Intent(str, Enum):
    INFORMATION = "information"
    CODE_ANALYSIS = "code_analysis"
    TESTING = "testing"
    RECOMMENDATION = "recommendation"
    DOCUMENTATION = "documentation"
    CONTENT = "content"
    NARRATION = "narration"
    REMINDER = "reminder"
    SUBMISSION = "submission"
    RELEASE = "release"
    PROJECT_IMPROVEMENT = "project_improvement"    # multi-agent
    SUBMISSION_PREP = "submission_prep"            # multi-agent
    RELEASE_CHECK = "release_check"                # multi-agent
    UNKNOWN = "unknown"


INTENT_SYSTEM_PROMPT = """You are an intent classifier for A2Z Nexus, an AI developer workspace.

Given a user message, classify the primary intent into exactly ONE of these categories:

- information: General technical questions, explanations, "what is X", "how does Y work"
- code_analysis: Analyze project code, structure, languages, issues
- testing: Run tests, generate tests, fix test failures
- recommendation: Improve project, what should I fix, what's wrong with my project
- documentation: Generate README, API docs, setup guide, architecture docs
- content: Generate descriptions, abstracts, presentations, release notes, elevator pitch
- narration: Demo script, presentation narration, feature explanation
- reminder: Set reminder, deadline mentioned, due date, submission date, meeting
- submission: Check submission readiness, is project ready to submit
- release: Check release readiness, is project ready to deploy/release
- project_improvement: Analyze AND improve (triggers code_analysis + testing + recommendation)
- submission_prep: Prepare for submission (code_analysis + testing + submission check)
- release_check: Full release check (testing + release)
- unknown: Cannot determine intent

Respond with ONLY the intent label — no explanation, no punctuation.
"""

# Keyword shortcuts (fast path before AI classification)
KEYWORD_INTENTS: list[tuple[list[str], Intent]] = [
    (["what is", "what are", "explain", "how does", "how do", "why does", "define", "describe what"], Intent.INFORMATION),
    (["analyze code", "code analysis", "scan my", "review my code", "check my code"], Intent.CODE_ANALYSIS),
    (["run tests", "run test", "execute tests", "test results", "failing tests", "fix tests", "generate tests", "write tests"], Intent.TESTING),
    (["improve my project", "make it better", "what should i fix", "recommendations for", "how can i improve", "project review"], Intent.PROJECT_IMPROVEMENT),
    (["generate readme", "write readme", "api documentation", "create docs", "setup guide", "architecture doc"], Intent.DOCUMENTATION),
    (["project description", "elevator pitch", "presentation slides", "hackathon submission", "abstract for"], Intent.CONTENT),
    (["demo script", "narration", "presentation narration", "feature explanation"], Intent.NARRATION),
    (["remind me", "set a reminder", "deadline is", "due date", "submission is", "submit by", "friday", "tomorrow", "next week", "by end of"], Intent.REMINDER),
    (["ready to submit", "submission check", "check submission", "submission readiness", "is my project ready for submission"], Intent.SUBMISSION),
    (["ready to release", "release check", "release readiness", "ready to deploy", "production ready"], Intent.RELEASE),
    (["prepare for submission", "get ready to submit", "submission prep"], Intent.SUBMISSION_PREP),
    (["full release", "check everything for release"], Intent.RELEASE_CHECK),
]


# ---------------------------------------------------------------------------
# Workflow result
# ---------------------------------------------------------------------------

@dataclass
class OrchestratorResult:
    content: str
    agents_used: list[str] = field(default_factory=list)
    intent: str = Intent.UNKNOWN
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class Orchestrator:
    """Routes requests to the appropriate agent(s) and combines results."""

    def __init__(self, ai: BaseAIProvider) -> None:
        self._ai = ai
        self._information_agent = None
        self._code_analysis_agent = None
        self._testing_agent = None
        self._recommendation_agent = None
        self._documentation_agent = None
        self._content_agent = None
        self._narration_agent = None
        self._reminder_agent = None
        self._submission_agent = None
        self._release_agent = None

    # ------------------------------------------------------------------
    # Lazy agent initialization (agents share the same AI provider)
    # ------------------------------------------------------------------

    def _info(self):
        if self._information_agent is None:
            from agents.information.agent import InformationAgent
            self._information_agent = InformationAgent(self._ai)
        return self._information_agent

    def _code(self):
        if self._code_analysis_agent is None:
            from agents.code_analysis.agent import CodeAnalysisAgent
            self._code_analysis_agent = CodeAnalysisAgent(self._ai)
        return self._code_analysis_agent

    def _test(self):
        if self._testing_agent is None:
            from agents.testing.agent import TestingAgent
            self._testing_agent = TestingAgent(self._ai)
        return self._testing_agent

    def _recommend(self):
        if self._recommendation_agent is None:
            from agents.recommendation.agent import RecommendationAgent
            self._recommendation_agent = RecommendationAgent(self._ai)
        return self._recommendation_agent

    def _doc(self):
        if self._documentation_agent is None:
            from agents.documentation.agent import DocumentationAgent
            self._documentation_agent = DocumentationAgent(self._ai)
        return self._documentation_agent

    def _content(self):
        if self._content_agent is None:
            from agents.content.agent import ContentAgent
            self._content_agent = ContentAgent(self._ai)
        return self._content_agent

    def _narration(self):
        if self._narration_agent is None:
            from agents.narration.agent import NarrationAgent
            self._narration_agent = NarrationAgent(self._ai)
        return self._narration_agent

    def _reminder(self):
        if self._reminder_agent is None:
            from agents.reminder.agent import ReminderAgent
            self._reminder_agent = ReminderAgent(self._ai)
        return self._reminder_agent

    def _submission(self):
        if self._submission_agent is None:
            from agents.submission.agent import SubmissionAgent
            self._submission_agent = SubmissionAgent(self._ai)
        return self._submission_agent

    def _release(self):
        if self._release_agent is None:
            from agents.release.agent import ReleaseAgent
            self._release_agent = ReleaseAgent(self._ai)
        return self._release_agent

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def process(
        self,
        message: str,
        project: dict | None = None,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> OrchestratorResult:
        """
        Process a user message.

        Args:
            message: The user's raw message.
            project: Optional project dict (id, name, repository_path, technology, etc.)
            conversation_history: Prior chat messages for context.

        Returns:
            OrchestratorResult with content, agents_used, intent, metadata.
        """
        # Basic greetings are handled locally so the chat UI can be tested
        # before an external AI key is configured.
        if self._is_simple_greeting(message):
            return OrchestratorResult(
                content=(
                    "Hi! 👋 I’m A2Z Nexus. I’m ready to help with your project, "
                    "code analysis, testing, documentation, recommendations, "
                    "reminders, and submission/release checks."
                ),
                agents_used=["orchestrator"],
                intent=Intent.INFORMATION,
            )

        try:
            intent = await self._classify_intent(message)
        except Exception as exc:
            logger.exception("Intent classification failed: %s", exc)
            return OrchestratorResult(
                content=(
                    "⚠️ The AI provider is not available yet. Please check "
                    "`AI_PROVIDER`, `GEMINI_API_KEY`, and `GEMINI_MODEL` in the "
                    "project `.env`, then restart the backend. The backend itself "
                    "is running."
                ),
                agents_used=["orchestrator"],
                intent=Intent.INFORMATION,
                metadata={"error": str(exc)},
            )

        logger.info("Intent: %s | Project: %s", intent, project.get("name") if project else "none")

        project_path = project.get("repository_path", "") if project else ""
        project_name = project.get("name", "your project") if project else "your project"

        try:
            if intent == Intent.INFORMATION or (intent == Intent.UNKNOWN and not project):
                return await self._run_information(message, conversation_history)

            elif intent == Intent.CODE_ANALYSIS:
                return await self._run_code_analysis(project_path, project_name)

            elif intent == Intent.TESTING:
                return await self._run_testing(message, project_path, project_name)

            elif intent == Intent.RECOMMENDATION:
                return await self._run_recommendation(project_path, project_name)

            elif intent == Intent.PROJECT_IMPROVEMENT:
                return await self._run_project_improvement(project_path, project_name)

            elif intent == Intent.DOCUMENTATION:
                return await self._run_documentation(message, project_path, project_name)

            elif intent == Intent.CONTENT:
                return await self._run_content(message, project_path, project_name)

            elif intent == Intent.NARRATION:
                return await self._run_narration(message, project_path, project_name)

            elif intent == Intent.REMINDER:
                return await self._run_reminder(message)

            elif intent == Intent.SUBMISSION or intent == Intent.SUBMISSION_PREP:
                return await self._run_submission_prep(project_path, project_name)

            elif intent == Intent.RELEASE or intent == Intent.RELEASE_CHECK:
                return await self._run_release_check(project_path, project_name)

            else:
                # Default: treat as information if no project, else ask for clarification
                if not project:
                    return await self._run_information(message, conversation_history)
                return OrchestratorResult(
                    content=(
                        "I'm not sure what you'd like me to do. Could you clarify?\n\n"
                        "I can help you with:\n"
                        "- **Analyze** your project code\n"
                        "- **Run or generate** tests\n"
                        "- **Recommend** improvements\n"
                        "- **Generate** documentation or content\n"
                        "- **Check** submission or release readiness\n"
                        "- **Answer** general technical questions"
                    ),
                    agents_used=["orchestrator"],
                    intent=intent,
                )
        except Exception as exc:
            logger.exception("Orchestrator error for intent %s: %s", intent, exc)
            return OrchestratorResult(
                content=f"⚠️ An error occurred while processing your request: {exc}",
                agents_used=["orchestrator"],
                intent=intent,
                metadata={"error": str(exc)},
            )

    # ------------------------------------------------------------------
    # Intent classification
    # ------------------------------------------------------------------

    @staticmethod
    def _is_simple_greeting(message: str) -> bool:
        normalized = " ".join(message.strip().lower().split())
        return normalized in {
            "hi", "hello", "hey", "hii", "hiii",
            "good morning", "good afternoon", "good evening",
            "how are you",
        }

    async def _classify_intent(self, message: str) -> Intent:
        msg_lower = message.lower()

        # Fast-path keyword matching
        for keywords, intent in KEYWORD_INTENTS:
            if any(kw in msg_lower for kw in keywords):
                return intent

        # AI classification for ambiguous messages
        response = await self._ai.chat(
            messages=[Message("user", message)],
            system_prompt=INTENT_SYSTEM_PROMPT,
            temperature=0.0,
            max_tokens=20,
        )
        label = response.content.strip().lower()
        try:
            return Intent(label)
        except ValueError:
            return Intent.UNKNOWN

    # ------------------------------------------------------------------
    # Single-agent workflows
    # ------------------------------------------------------------------

    async def _run_information(
        self,
        message: str,
        history: list[dict[str, str]] | None,
    ) -> OrchestratorResult:
        response = await self._info().answer(message, history)
        return OrchestratorResult(
            content=response.content,
            agents_used=["information"],
            intent=Intent.INFORMATION,
        )

    async def _run_code_analysis(self, project_path: str, project_name: str) -> OrchestratorResult:
        if not project_path:
            return OrchestratorResult(
                content="To analyze your project, please set the **repository path** in the project settings.",
                agents_used=["orchestrator"],
                intent=Intent.CODE_ANALYSIS,
            )
        result = await self._code().analyze(project_path, project_name)
        agents_used = ["code_analysis"]
        content = self._format_code_analysis(result)
        return OrchestratorResult(content=content, agents_used=agents_used, intent=Intent.CODE_ANALYSIS, metadata=result)

    async def _run_testing(self, message: str, project_path: str, project_name: str) -> OrchestratorResult:
        if not project_path:
            return OrchestratorResult(
                content="To run or generate tests, please set the **repository path** in the project settings.",
                agents_used=["orchestrator"],
                intent=Intent.TESTING,
            )
        if any(w in message.lower() for w in ["generate", "write", "create"]):
            result = await self._test().generate_tests(project_path)
            content = f"## Generated Tests\n\n```\n{result.get('generated_code', '')}\n```"
        else:
            result = await self._test().run_tests(project_path)
            content = self._format_test_result(result)
        return OrchestratorResult(content=content, agents_used=["testing"], intent=Intent.TESTING, metadata=result)

    async def _run_documentation(self, message: str, project_path: str, project_name: str) -> OrchestratorResult:
        doc_type = self._detect_doc_type(message)
        context = f"Project: {project_name}\nPath: {project_path}"
        result = await self._doc().generate(doc_type, project_name, context)
        content = f"## {doc_type.upper()} Documentation\n\n{result['content']}"
        return OrchestratorResult(content=content, agents_used=["documentation"], intent=Intent.DOCUMENTATION, metadata=result)

    async def _run_content(self, message: str, project_path: str, project_name: str) -> OrchestratorResult:
        content_type = self._detect_content_type(message)
        context = f"Project: {project_name}\nPath: {project_path}"
        result = await self._content().generate(content_type, project_name, context)
        return OrchestratorResult(content=result["content"], agents_used=["content"], intent=Intent.CONTENT, metadata=result)

    async def _run_narration(self, message: str, project_path: str, project_name: str) -> OrchestratorResult:
        narration_for = self._detect_narration_type(message)
        context = f"Project: {project_name}\nPath: {project_path}"
        result = await self._narration().generate(narration_for, project_name, context)
        return OrchestratorResult(content=result["script"], agents_used=["narration"], intent=Intent.NARRATION, metadata=result)

    async def _run_reminder(self, message: str) -> OrchestratorResult:
        result = await self._reminder().detect_from_message(message)
        if result.get("detected"):
            items = result.get("items", [])
            confirmation = result.get("confirmation_prompt", "")
            content_lines = ["📅 **Deadline detected!**\n"]
            for item in items:
                content_lines.append(f"- **{item.get('title', '')}** — {item.get('type', '')} ({item.get('due_date') or item.get('relative_description', 'no date')})")
            if confirmation:
                content_lines.append(f"\n{confirmation}")
            content = "\n".join(content_lines)
        else:
            content = "I didn't detect a specific deadline or reminder in your message. Could you be more specific? Example: *\"My project submission is next Friday.\"*"
        return OrchestratorResult(content=content, agents_used=["reminder"], intent=Intent.REMINDER, metadata=result)

    async def _run_recommendation(self, project_path: str, project_name: str) -> OrchestratorResult:
        code_result = None
        if project_path:
            code_result = await self._code().analyze(project_path, project_name)
        recs = await self._recommend().recommend(
            project_name=project_name,
            code_analysis=code_result,
        )
        content = self._format_recommendations(recs)
        return OrchestratorResult(
            content=content,
            agents_used=["code_analysis", "recommendation"] if code_result else ["recommendation"],
            intent=Intent.RECOMMENDATION,
            metadata={"recommendations": recs},
        )

    # ------------------------------------------------------------------
    # Multi-agent workflows
    # ------------------------------------------------------------------

    async def _run_project_improvement(self, project_path: str, project_name: str) -> OrchestratorResult:
        """Code Analysis → Testing → Recommendation"""
        agents_used = []
        code_result = test_result = None

        if project_path:
            logger.info("Multi-agent: Code Analysis for %s", project_name)
            code_result = await self._code().analyze(project_path, project_name)
            agents_used.append("code_analysis")

            logger.info("Multi-agent: Testing for %s", project_name)
            test_result = await self._test().run_tests(project_path)
            agents_used.append("testing")

        logger.info("Multi-agent: Recommendation for %s", project_name)
        recs = await self._recommend().recommend(
            project_name=project_name,
            code_analysis=code_result,
            test_results=test_result,
        )
        agents_used.append("recommendation")

        parts = [f"# Project Improvement Report — {project_name}\n"]
        if code_result:
            parts.append("## Code Analysis\n")
            parts.append(self._format_code_analysis(code_result))
        if test_result:
            parts.append("\n## Test Results\n")
            parts.append(self._format_test_result(test_result))
        parts.append("\n## Recommendations\n")
        parts.append(self._format_recommendations(recs))

        return OrchestratorResult(
            content="\n".join(parts),
            agents_used=agents_used,
            intent=Intent.PROJECT_IMPROVEMENT,
            metadata={"code_analysis": code_result, "test_results": test_result, "recommendations": recs},
        )

    async def _run_submission_prep(self, project_path: str, project_name: str) -> OrchestratorResult:
        """Code Analysis → Testing → Submission Check"""
        agents_used = []
        code_result = test_result = None

        if project_path:
            code_result = await self._code().analyze(project_path, project_name)
            agents_used.append("code_analysis")
            test_result = await self._test().run_tests(project_path)
            agents_used.append("testing")

        sub_result = await self._submission().check(
            project_path=project_path or "",
            project_name=project_name,
            code_analysis=code_result,
            test_results=test_result,
        )
        agents_used.append("submission")

        content = self._format_submission(sub_result, project_name)
        return OrchestratorResult(
            content=content, agents_used=agents_used,
            intent=Intent.SUBMISSION_PREP, metadata=sub_result,
        )

    async def _run_release_check(self, project_path: str, project_name: str) -> OrchestratorResult:
        """Testing → Release Check"""
        agents_used = []
        test_result = None

        if project_path:
            test_result = await self._test().run_tests(project_path)
            agents_used.append("testing")

        release_result = await self._release().check(
            project_path=project_path or "",
            project_name=project_name,
            test_results=test_result,
        )
        agents_used.append("release")

        content = self._format_release(release_result, project_name)
        return OrchestratorResult(
            content=content, agents_used=agents_used,
            intent=Intent.RELEASE_CHECK, metadata=release_result,
        )

    # ------------------------------------------------------------------
    # Formatters
    # ------------------------------------------------------------------

    @staticmethod
    def _format_code_analysis(r: dict) -> str:
        if r.get("error"):
            return f"⚠️ {r['error']}"
        lines = [
            f"**Languages:** {', '.join(r.get('languages', [])) or 'None detected'}",
            f"**Frameworks:** {', '.join(r.get('frameworks', [])) or 'None detected'}",
            f"**Files:** {r.get('file_count', 0)}",
        ]
        issues = r.get("issues", [])
        if issues:
            lines.append("\n**Issues found:**")
            for i in issues:
                lines.append(f"- [{i['severity']}] {i['issue']}")
        if r.get("ai_analysis"):
            lines.append(f"\n{r['ai_analysis']}")
        return "\n".join(lines)

    @staticmethod
    def _format_test_result(r: dict) -> str:
        if r.get("error") and r.get("total", 0) == 0:
            return f"⚠️ {r['error']}"
        status = "✅" if r.get("failed", 0) == 0 else "❌"
        lines = [
            f"{status} **{r.get('framework', 'unknown')}** — "
            f"{r.get('passed', 0)} passed / {r.get('failed', 0)} failed / {r.get('skipped', 0)} skipped"
            f" (total: {r.get('total', 0)})"
        ]
        if r.get("explanation"):
            lines.append(f"\n**Failure analysis:**\n{r['explanation']}")
        return "\n".join(lines)

    @staticmethod
    def _format_recommendations(recs: list[dict]) -> str:
        if not recs:
            return "No recommendations generated."
        lines = []
        for r in recs:
            priority = r.get("priority", "MEDIUM")
            emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(priority, "⚪")
            lines.append(f"{emoji} **[{priority}] {r.get('title', '')}**")
            if r.get("description"):
                lines.append(f"   {r['description']}")
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _format_submission(r: dict, project_name: str) -> str:
        pct = r.get("readiness_percentage", 0)
        bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
        lines = [
            f"## Submission Readiness — {project_name}",
            f"**{pct:.0f}%** [{bar}]",
            "",
        ]
        if r.get("completed"):
            lines.append("**✅ Completed:**")
            for item in r["completed"]:
                lines.append(f"  - {item}")
        if r.get("missing"):
            lines.append("\n**❌ Missing (required):**")
            for item in r["missing"]:
                lines.append(f"  - {item}")
        if r.get("warnings"):
            lines.append("\n**⚠️ Warnings:**")
            for item in r["warnings"]:
                lines.append(f"  - {item}")
        if r.get("next_actions"):
            lines.append("\n**📋 Next Actions:**")
            for i, action in enumerate(r["next_actions"], 1):
                lines.append(f"  {i}. {action}")
        if r.get("summary"):
            lines.append(f"\n{r['summary']}")
        return "\n".join(lines)

    @staticmethod
    def _format_release(r: dict, project_name: str) -> str:
        status = "✅ READY" if r.get("ready") else "❌ NOT READY"
        lines = [f"## Release Check — {project_name}", f"**Status: {status}**", ""]
        if r.get("passed_checks"):
            lines.append("**✅ Passed:**")
            for c in r["passed_checks"]:
                lines.append(f"  - {c}")
        if r.get("blocking_issues"):
            lines.append("\n**🚫 Blocking Issues:**")
            for i in r["blocking_issues"]:
                lines.append(f"  - {i}")
        if r.get("warnings"):
            lines.append("\n**⚠️ Warnings:**")
            for w in r["warnings"]:
                lines.append(f"  - {w}")
        if r.get("recommended_actions"):
            lines.append("\n**📋 Recommended Actions:**")
            for i, a in enumerate(r["recommended_actions"], 1):
                lines.append(f"  {i}. {a}")
        if r.get("summary"):
            lines.append(f"\n{r['summary']}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Type detection helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_doc_type(message: str) -> str:
        msg = message.lower()
        if "api" in msg:
            return "api"
        if "architecture" in msg:
            return "architecture"
        if "setup" in msg or "install" in msg:
            return "setup"
        if "changelog" in msg or "change log" in msg:
            return "changelog"
        return "readme"

    @staticmethod
    def _detect_content_type(message: str) -> str:
        msg = message.lower()
        if "pitch" in msg or "elevator" in msg:
            return "elevator_pitch"
        if "abstract" in msg:
            return "abstract"
        if "problem" in msg:
            return "problem_statement"
        if "solution" in msg:
            return "solution_statement"
        if "presentation" in msg or "slide" in msg:
            return "presentation"
        if "release note" in msg or "changelog" in msg:
            return "release_notes"
        if "hackathon" in msg:
            return "hackathon_submission"
        return "description"

    @staticmethod
    def _detect_narration_type(message: str) -> str:
        msg = message.lower()
        if "presentation" in msg:
            return "presentation"
        if "feature" in msg:
            return "feature"
        if "tutorial" in msg or "getting started" in msg:
            return "tutorial"
        return "demo"
