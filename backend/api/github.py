
"""Optional GitHub repository inspection endpoint."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from integrations.github import inspect_repository

router = APIRouter(prefix="/github", tags=["github"])

class GitHubInspectRequest(BaseModel):
    repo_url: str

@router.post("/inspect")
async def github_inspect(payload: GitHubInspectRequest) -> dict:
    try:
        return await inspect_repository(payload.repo_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"GitHub inspection failed: {exc}") from exc

@router.post("/import")
async def github_import(payload: GitHubInspectRequest):
    """Download a public/private GitHub repository archive for A2Z analysis.
    This endpoint does not modify the user's GitHub repository."""
    import tempfile, zipfile, shutil
    from pathlib import Path
    from services.project_workspace import safe_extract
    from integrations.github import parse_repo_url, _headers
    import httpx
    from config.settings import settings
    owner, repo = parse_repo_url(payload.repo_url)
    dest = Path(__file__).resolve().parents[1] / "data" / "github_imports" / f"{owner}_{repo}"
    if dest.exists(): shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(base_url=settings.GITHUB_API_URL, headers=_headers(), timeout=httpx.Timeout(settings.GITHUB_TIMEOUT_SECONDS)) as client:
        meta=await client.get(f"/repos/{owner}/{repo}"); meta.raise_for_status(); branch=meta.json().get("default_branch","main")
        archive=await client.get(f"/repos/{owner}/{repo}/zipball/{branch}"); archive.raise_for_status()
    tmp=Path(tempfile.mktemp(suffix='.zip'))
    try:
        tmp.write_bytes(archive.content)
        with zipfile.ZipFile(tmp) as z: safe_extract(z, dest)
        from services.project_workspace import normalize_root
        root=normalize_root(dest)
        from services.project_intelligence import full_analysis
        result=await full_analysis(root)
        (dest/'analysis.json').write_text(__import__('json').dumps(result,indent=2),encoding='utf-8')
        return {"success":True,"owner":owner,"repo":repo,"root":root.name,"repository_path":str(dest),"analysis":result}
    finally:
        tmp.unlink(missing_ok=True)
