
"""Optional GitHub REST integration used for repository metadata/tree inspection."""
from __future__ import annotations

import re
from typing import Any
import httpx
from config.settings import settings

_REPO_RE = re.compile(r"github\.com[/:]([^/]+)/([^/#]+?)(?:\.git)?$", re.I)

def parse_repo_url(repo_url: str) -> tuple[str, str]:
    match = _REPO_RE.search(repo_url.strip())
    if not match:
        raise ValueError("Enter a valid GitHub repository URL, e.g. https://github.com/owner/repo")
    return match.group(1), match.group(2)

def _headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
    return headers

async def inspect_repository(repo_url: str) -> dict[str, Any]:
    owner, repo = parse_repo_url(repo_url)
    timeout = httpx.Timeout(settings.GITHUB_TIMEOUT_SECONDS)
    async with httpx.AsyncClient(base_url=settings.GITHUB_API_URL, headers=_headers(), timeout=timeout) as client:
        response = await client.get(f"/repos/{owner}/{repo}")
        response.raise_for_status()
        meta = response.json()
        tree = await client.get(f"/repos/{owner}/{repo}/git/trees/{meta['default_branch']}", params={"recursive": "1"})
        tree.raise_for_status()
        items = tree.json().get("tree", [])
    return {
        "owner": owner,
        "repo": repo,
        "name": meta.get("name", repo),
        "full_name": meta.get("full_name", f"{owner}/{repo}"),
        "description": meta.get("description") or "",
        "default_branch": meta.get("default_branch", "main"),
        "language": meta.get("language"),
        "stars": meta.get("stargazers_count", 0),
        "private": bool(meta.get("private", False)),
        "html_url": meta.get("html_url", repo_url),
        "tree": [{"path": x.get("path"), "type": x.get("type"), "size": x.get("size")} for x in items[:1000]],
    }
