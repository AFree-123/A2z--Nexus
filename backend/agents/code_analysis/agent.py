"""
Code Analysis Agent — analyzes an actual project on disk.

Inspects:
  - project structure (files, folders)
  - programming languages used
  - frameworks and dependencies
  - important files (README, config, tests, etc.)
  - potential issues (missing error handling, no tests, no docs, etc.)
  - code organization

Returns structured findings — never invents data without reading the project.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from services.ai_service import AIResponse, BaseAIProvider, Message

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# File extensions → language
LANG_MAP: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript (JSX)",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (TSX)",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sql": "SQL",
    ".sh": "Shell",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".md": "Markdown",
    ".toml": "TOML",
}

# Dependency/config files and their meanings
IMPORTANT_FILES = {
    "package.json": "Node.js project",
    "requirements.txt": "Python dependencies",
    "pyproject.toml": "Python project config",
    "Pipfile": "Pipenv config",
    "pom.xml": "Maven (Java)",
    "build.gradle": "Gradle (Java/Kotlin)",
    "go.mod": "Go modules",
    "Cargo.toml": "Rust Cargo",
    "Gemfile": "Ruby Bundler",
    "composer.json": "PHP Composer",
    "Dockerfile": "Docker container config",
    "docker-compose.yml": "Docker Compose config",
    ".env": "Environment variables (WARNING: should not be committed)",
    ".env.example": "Environment variable template",
    "README.md": "Project documentation",
    "pytest.ini": "pytest configuration",
    "jest.config.js": "Jest test configuration",
    "vite.config.ts": "Vite build config",
    "tsconfig.json": "TypeScript config",
    ".gitignore": "Git ignore rules",
    "LICENSE": "License file",
}

# Directories to skip
SKIP_DIRS = {
    "node_modules", ".git", ".venv", "venv", "env", "__pycache__",
    ".pytest_cache", "dist", "build", ".next", ".nuxt", "coverage",
    "htmlcov", ".mypy_cache", ".ruff_cache",
}

MAX_FILE_SCAN = 500   # max number of files to scan
MAX_CONTENT_CHARS = 8000  # max chars of project content to send to AI


ANALYSIS_SYSTEM_PROMPT = """You are a senior software engineer performing a code review and project analysis.

You will receive a structured summary of a project: its file tree, detected languages, frameworks, and dependency files.

Your job is to provide a STRUCTURED analysis with these sections:

## Project Overview
Brief description of what the project appears to be.

## Languages & Frameworks
List detected languages and frameworks.

## Project Structure
Assessment of how well-organized the project is.

## Dependencies
Key dependencies detected. Any outdated or unusual ones.

## Potential Issues
Real issues found in the project structure (missing tests, no README, no error handling patterns, missing config, etc.).
Only report issues that are actually evidenced by the file scan. Do NOT invent issues.

## Documentation
Is there a README? API docs? Setup guide? What is missing?

## Recommendations Summary
3–5 specific, actionable improvements backed by the evidence above.

Be specific. Do not give generic advice not supported by the actual project data.
"""


class CodeAnalysisAgent:
    """
    Analyzes a project at a given filesystem path.
    Returns structured findings from real project data.
    """

    def __init__(self, ai: BaseAIProvider) -> None:
        self._ai = ai

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze(self, project_path: str, project_name: str = "") -> dict:
        """
        Analyze a project directory.

        Returns a dict with:
          - path
          - structure (file tree summary)
          - languages
          - frameworks
          - important_files
          - issues (pre-scan heuristics)
          - ai_analysis (full AI report text)
          - raw_stats
        """
        path = Path(project_path)
        if not path.exists() or not path.is_dir():
            return self._not_found_result(project_path)

        # 1. Scan the filesystem
        scan = self._scan_project(path)

        # 2. Heuristic issue detection
        issues = self._detect_issues(scan)

        # 3. Build context for AI
        context = self._build_context(scan, project_name or path.name)

        # 4. Ask AI for structured analysis
        ai_response = await self._ai.chat(
            messages=[Message("user", context)],
            system_prompt=ANALYSIS_SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=2048,
        )

        return {
            "path": str(path),
            "project_name": project_name or path.name,
            "structure": scan["tree_summary"],
            "languages": scan["languages"],
            "frameworks": scan["frameworks"],
            "important_files": scan["important_files"],
            "file_count": scan["file_count"],
            "issues": issues,
            "ai_analysis": ai_response.content,
            "raw_stats": {
                "total_files": scan["file_count"],
                "total_dirs": scan["dir_count"],
                "lines_of_code_estimate": scan["loc_estimate"],
            },
        }

    # ------------------------------------------------------------------
    # Internal scanning
    # ------------------------------------------------------------------

    def _scan_project(self, root: Path) -> dict:
        """Walk the project tree and collect metadata."""
        lang_counts: dict[str, int] = {}
        important_files: list[str] = []
        tree_lines: list[str] = []
        file_count = 0
        dir_count = 0
        loc_estimate = 0
        frameworks: set[str] = set()

        for dirpath, dirnames, filenames in os.walk(root):
            # Prune skip dirs in-place
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

            rel_dir = Path(dirpath).relative_to(root)
            depth = len(rel_dir.parts)
            indent = "  " * depth
            if depth <= 3:  # only show tree 3 levels deep
                tree_lines.append(f"{indent}{rel_dir.name or root.name}/")
            dir_count += 1

            for fname in filenames:
                if file_count >= MAX_FILE_SCAN:
                    break
                file_count += 1
                fpath = Path(dirpath) / fname
                rel_path = fpath.relative_to(root)

                # Language detection
                ext = fpath.suffix.lower()
                if ext in LANG_MAP:
                    lang_counts[LANG_MAP[ext]] = lang_counts.get(LANG_MAP[ext], 0) + 1

                # Important file detection
                if fname in IMPORTANT_FILES or fname.lower() in IMPORTANT_FILES:
                    important_files.append(str(rel_path))

                # Framework detection from dependency files
                if fname == "package.json":
                    frameworks.update(self._detect_node_frameworks(fpath))
                elif fname == "requirements.txt":
                    frameworks.update(self._detect_python_frameworks(fpath))
                elif fname == "pyproject.toml":
                    frameworks.update(self._detect_pyproject_frameworks(fpath))

                # LOC estimate (text files only)
                if ext in LANG_MAP and ext not in (".json", ".yaml", ".yml", ".md", ".toml"):
                    try:
                        with open(fpath, encoding="utf-8", errors="ignore") as f:
                            loc_estimate += sum(1 for _ in f)
                    except OSError:
                        pass

                if depth <= 3:
                    tree_lines.append(f"{indent}  {fname}")

        # Sort languages by file count
        sorted_langs = sorted(lang_counts.items(), key=lambda x: -x[1])

        return {
            "tree_summary": "\n".join(tree_lines[:80]),  # cap at 80 lines
            "languages": [lang for lang, _ in sorted_langs],
            "lang_counts": dict(sorted_langs),
            "frameworks": sorted(frameworks),
            "important_files": important_files,
            "file_count": file_count,
            "dir_count": dir_count,
            "loc_estimate": loc_estimate,
        }

    def _detect_node_frameworks(self, pkg_json: Path) -> list[str]:
        found = []
        try:
            with open(pkg_json, encoding="utf-8") as f:
                data = json.load(f)
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            framework_map = {
                "react": "React", "vue": "Vue.js", "angular": "@angular/core",
                "next": "Next.js", "nuxt": "Nuxt.js", "express": "Express",
                "fastify": "Fastify", "svelte": "Svelte", "vite": "Vite",
                "tailwindcss": "Tailwind CSS",
            }
            for key, label in framework_map.items():
                if key in deps:
                    found.append(label)
        except Exception:
            pass
        return found

    def _detect_python_frameworks(self, req_txt: Path) -> list[str]:
        found = []
        framework_map = {
            "fastapi": "FastAPI", "flask": "Flask", "django": "Django",
            "sqlalchemy": "SQLAlchemy", "pydantic": "Pydantic",
            "celery": "Celery", "pytest": "pytest", "uvicorn": "uvicorn",
            "anthropic": "Anthropic SDK", "openai": "OpenAI SDK",
        }
        try:
            with open(req_txt, encoding="utf-8") as f:
                content = f.read().lower()
            for key, label in framework_map.items():
                if key in content:
                    found.append(label)
        except Exception:
            pass
        return found

    def _detect_pyproject_frameworks(self, toml_path: Path) -> list[str]:
        found = []
        try:
            with open(toml_path, encoding="utf-8") as f:
                content = f.read().lower()
            framework_map = {
                "fastapi": "FastAPI", "flask": "Flask", "django": "Django",
                "sqlalchemy": "SQLAlchemy", "pydantic": "Pydantic",
            }
            for key, label in framework_map.items():
                if key in content:
                    found.append(label)
        except Exception:
            pass
        return found

    def _detect_issues(self, scan: dict) -> list[dict]:
        """Heuristic issues that don't require AI."""
        issues = []
        important = [f.lower() for f in scan["important_files"]]

        if not any("readme" in f for f in important):
            issues.append({"severity": "HIGH", "issue": "No README.md found"})
        if not any("test" in f or "spec" in f for f in scan["tree_summary"].lower().split("\n")):
            issues.append({"severity": "HIGH", "issue": "No test files detected"})
        if not any("dockerfile" in f or "docker-compose" in f for f in important):
            issues.append({"severity": "LOW", "issue": "No Docker configuration found"})
        if ".env" in important and ".env.example" not in important:
            issues.append({"severity": "MEDIUM", "issue": ".env file present but no .env.example template"})
        if not any("gitignore" in f for f in important):
            issues.append({"severity": "MEDIUM", "issue": "No .gitignore found"})
        if not any("license" in f for f in important):
            issues.append({"severity": "LOW", "issue": "No LICENSE file found"})

        return issues

    def _build_context(self, scan: dict, project_name: str) -> str:
        lines = [
            f"# Project: {project_name}",
            f"Total files: {scan['file_count']}  |  Estimated LOC: {scan['loc_estimate']}",
            "",
            "## File Tree (first 80 entries)",
            "```",
            scan["tree_summary"][:MAX_CONTENT_CHARS // 2],
            "```",
            "",
            "## Languages detected",
            ", ".join(f"{lang} ({scan['lang_counts'].get(lang, 0)} files)"
                      for lang in scan["languages"]) or "None detected",
            "",
            "## Frameworks / Libraries detected",
            ", ".join(scan["frameworks"]) or "None detected",
            "",
            "## Important files found",
            "\n".join(f"- {f}" for f in scan["important_files"]) or "None",
            "",
            "## Pre-scan heuristic issues",
        ]
        for issue in self._detect_issues(scan):
            lines.append(f"- [{issue['severity']}] {issue['issue']}")
        if not self._detect_issues(scan):
            lines.append("- None detected by heuristics")

        return "\n".join(lines)

    @staticmethod
    def _not_found_result(project_path: str) -> dict:
        return {
            "path": project_path,
            "project_name": "",
            "error": f"Project path '{project_path}' does not exist or is not a directory.",
            "structure": "",
            "languages": [],
            "frameworks": [],
            "important_files": [],
            "file_count": 0,
            "issues": [{"severity": "CRITICAL", "issue": "Project path not found"}],
            "ai_analysis": "Cannot analyze: project path does not exist.",
            "raw_stats": {},
        }
