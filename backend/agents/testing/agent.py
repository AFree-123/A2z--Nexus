"""
Testing Agent — detects test framework, runs tests, generates test cases.

Never claims a test passed unless it was actually executed.
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import tempfile
from pathlib import Path

from services.ai_service import BaseAIProvider, Message

# ---------------------------------------------------------------------------
# Known test frameworks and their run commands
# ---------------------------------------------------------------------------
FRAMEWORK_DETECTORS = [
    # (marker_files_or_dirs, framework_name, run_command)
    (["pytest.ini", "pyproject.toml", "setup.cfg", "conftest.py"], "pytest", ["python", "-m", "pytest", "--tb=short", "-q"]),
    (["jest.config.js", "jest.config.ts", "jest.config.cjs"], "jest", ["npx", "jest", "--passWithNoTests"]),
    (["vitest.config.ts", "vitest.config.js"], "vitest", ["npx", "vitest", "run"]),
    (["package.json"], "npm-test", ["npm", "test", "--", "--passWithNoTests"]),
    (["go.mod"], "go-test", ["go", "test", "./..."]),
]

GENERATE_SYSTEM_PROMPT = """You are an expert software engineer specializing in test-driven development.

You will receive information about a project — its language, framework, and a sample of its source code.

Generate REAL, RUNNABLE test cases for this project.

Requirements:
- Use the correct testing framework for the project's language/stack.
- Write tests that test actual business logic, not trivial assertions.
- Include edge cases and failure scenarios.
- Follow the project's existing conventions.
- Output ONLY the test file code — no explanations outside code comments.
- Each test must have a clear docstring or comment explaining what it tests.
"""

EXPLAIN_SYSTEM_PROMPT = """You are a senior developer explaining test failures.

For each failing test, explain:
1. What the test was checking
2. Why it failed (based on the error message)
3. A specific code fix to make it pass

Be concrete and actionable. Reference the actual error messages.
"""


class TestingAgent:
    """
    Detects the test framework, runs tests safely, generates new test cases,
    explains failures, and suggests fixes.
    """

    def __init__(self, ai: BaseAIProvider) -> None:
        self._ai = ai

    # ------------------------------------------------------------------
    # Run tests
    # ------------------------------------------------------------------

    async def run_tests(self, project_path: str) -> dict:
        """
        Run the project's existing tests.

        Returns:
            {
              "framework": str,
              "total": int, "passed": int, "failed": int, "skipped": int,
              "details": [...],
              "raw_output": str,
              "error": str | None,
              "explanation": str,   # AI explanation of failures (if any)
            }
        """
        path = Path(project_path)
        if not path.exists() or not path.is_dir():
            return self._error_result(f"Project path '{project_path}' not found.")

        framework, command = self._detect_framework(path)
        if not framework:
            return {
                "framework": "none",
                "total": 0, "passed": 0, "failed": 0, "skipped": 0,
                "details": [],
                "raw_output": "",
                "error": "No supported test framework detected.",
                "explanation": "No test framework was found. Consider adding pytest (Python) or Jest (Node.js).",
            }

        # Run tests in a subprocess (safe — read-only, no mutations)
        raw_output, exit_code = await self._run_subprocess(command, cwd=str(path))
        parsed = self._parse_output(framework, raw_output, exit_code)

        # AI explanation of failures
        explanation = ""
        if parsed["failed"] > 0:
            explanation = await self._explain_failures(raw_output, framework)

        return {
            "framework": framework,
            **parsed,
            "raw_output": raw_output[:4000],
            "error": None,
            "explanation": explanation,
        }

    # ------------------------------------------------------------------
    # Generate tests
    # ------------------------------------------------------------------

    async def generate_tests(
        self, project_path: str, target_file: str | None = None
    ) -> dict:
        """
        Generate test cases for a project or a specific file.

        Returns:
            {
              "framework": str,
              "generated_code": str,
              "target": str,
            }
        """
        path = Path(project_path)
        if not path.exists():
            return {"error": f"Path '{project_path}' not found.", "generated_code": "", "framework": ""}

        framework, _ = self._detect_framework(path)
        source_snippet = self._collect_source_snippet(path, target_file)

        context = (
            f"Project path: {project_path}\n"
            f"Detected test framework: {framework or 'unknown'}\n\n"
            f"Source code sample:\n```\n{source_snippet[:4000]}\n```\n\n"
            "Generate comprehensive test cases for this project."
        )

        response = await self._ai.chat(
            messages=[Message("user", context)],
            system_prompt=GENERATE_SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=2048,
        )
        return {
            "framework": framework or "unknown",
            "generated_code": response.content,
            "target": target_file or project_path,
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _detect_framework(self, path: Path) -> tuple[str, list[str]]:
        """Return (framework_name, run_command) or ("", [])."""
        for markers, name, cmd in FRAMEWORK_DETECTORS:
            for marker in markers:
                if (path / marker).exists():
                    # Extra check: requirements.txt must mention pytest
                    if name == "pytest":
                        req = path / "requirements.txt"
                        pyproject = path / "pyproject.toml"
                        has_pytest = (
                            (req.exists() and "pytest" in req.read_text(errors="ignore").lower())
                            or (pyproject.exists() and "pytest" in pyproject.read_text(errors="ignore").lower())
                            or (path / "conftest.py").exists()
                            or (path / "pytest.ini").exists()
                        )
                        if has_pytest:
                            return name, cmd
                    else:
                        return name, cmd
        return "", []

    @staticmethod
    async def _run_subprocess(command: list[str], cwd: str) -> tuple[str, int]:
        """Run command in a subprocess, capture output, return (output, exit_code)."""
        try:
            proc = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
            return stdout.decode(errors="replace"), proc.returncode or 0
        except asyncio.TimeoutError:
            return "Test run timed out after 120 seconds.", 1
        except FileNotFoundError as e:
            return f"Command not found: {e}", 1
        except Exception as e:
            return f"Error running tests: {e}", 1

    @staticmethod
    def _parse_output(framework: str, output: str, exit_code: int) -> dict:
        """Parse test runner output into structured counts."""
        total = passed = failed = skipped = 0
        details: list[dict] = []

        if framework == "pytest":
            # Look for pytest summary line: "5 passed, 2 failed, 1 skipped"
            import re
            summary = re.search(
                r"(\d+) passed|(\d+) failed|(\d+) skipped|(\d+) error",
                output,
            )
            passed = int(re.search(r"(\d+) passed", output).group(1)) if re.search(r"(\d+) passed", output) else 0
            failed = int(re.search(r"(\d+) failed", output).group(1)) if re.search(r"(\d+) failed", output) else 0
            skipped = int(re.search(r"(\d+) skipped", output).group(1)) if re.search(r"(\d+) skipped", output) else 0
            errors = int(re.search(r"(\d+) error", output).group(1)) if re.search(r"(\d+) error", output) else 0
            failed += errors
            total = passed + failed + skipped
            # Extract individual test names
            for line in output.splitlines():
                if " PASSED" in line:
                    details.append({"name": line.strip(), "status": "passed"})
                elif " FAILED" in line:
                    details.append({"name": line.strip(), "status": "failed"})
                elif " ERROR" in line:
                    details.append({"name": line.strip(), "status": "error"})

        elif framework in ("jest", "vitest", "npm-test"):
            import re
            # Jest: "Tests: 2 failed, 8 passed, 10 total"
            t = re.search(r"(\d+) total", output)
            p = re.search(r"(\d+) passed", output)
            f = re.search(r"(\d+) failed", output)
            s = re.search(r"(\d+) skipped", output)
            total = int(t.group(1)) if t else 0
            passed = int(p.group(1)) if p else 0
            failed = int(f.group(1)) if f else 0
            skipped = int(s.group(1)) if s else 0

        elif framework == "go-test":
            import re
            for line in output.splitlines():
                if line.startswith("--- PASS"):
                    passed += 1
                    total += 1
                    details.append({"name": line[8:].strip(), "status": "passed"})
                elif line.startswith("--- FAIL"):
                    failed += 1
                    total += 1
                    details.append({"name": line[8:].strip(), "status": "failed"})

        # If we couldn't parse but exit_code != 0, mark as at least 1 failure
        if total == 0 and exit_code != 0:
            failed = 1
            total = 1

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "details": details[:50],  # cap at 50
        }

    async def _explain_failures(self, raw_output: str, framework: str) -> str:
        response = await self._ai.chat(
            messages=[Message(
                "user",
                f"Test framework: {framework}\n\nTest output:\n```\n{raw_output[:3000]}\n```\n\n"
                "Explain each failure and provide specific fixes."
            )],
            system_prompt=EXPLAIN_SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=1024,
        )
        return response.content

    @staticmethod
    def _collect_source_snippet(path: Path, target_file: str | None) -> str:
        """Collect a representative source snippet for test generation."""
        skip = {"node_modules", ".git", ".venv", "venv", "__pycache__", "dist", "build"}
        code_exts = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rb", ".java"}
        snippets: list[str] = []
        chars = 0

        if target_file:
            fpath = path / target_file
            if fpath.exists():
                try:
                    content = fpath.read_text(encoding="utf-8", errors="ignore")
                    return f"# {target_file}\n{content[:4000]}"
                except OSError:
                    pass

        for dirpath, dirnames, filenames in os.walk(path):
            dirnames[:] = [d for d in dirnames if d not in skip]
            for fname in filenames:
                fpath = Path(dirpath) / fname
                if fpath.suffix in code_exts and chars < 3000:
                    try:
                        content = fpath.read_text(encoding="utf-8", errors="ignore")
                        rel = fpath.relative_to(path)
                        snippet = f"\n# {rel}\n{content[:800]}"
                        snippets.append(snippet)
                        chars += len(snippet)
                    except OSError:
                        pass
            if chars >= 3000:
                break

        return "\n".join(snippets) if snippets else "No source files found."

    @staticmethod
    def _error_result(message: str) -> dict:
        return {
            "framework": "none",
            "total": 0, "passed": 0, "failed": 0, "skipped": 0,
            "details": [],
            "raw_output": "",
            "error": message,
            "explanation": message,
        }
