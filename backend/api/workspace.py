from __future__ import annotations
import json, shutil, tempfile, zipfile
from pathlib import Path
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.engine import get_db
from database.models import Project, Notification
from services.project_workspace import save_project, tree, analyze, now, normalize_root
from services.project_intelligence import full_analysis

router=APIRouter(prefix='/workspace', tags=['workspace'])
DATA=Path(__file__).resolve().parents[1]/'data'/'projects'
DATA.mkdir(parents=True,exist_ok=True)

def base(pid): return DATA/pid

def find_root(pid):
    """Resolve the project's real root the SAME way save_project() does at
    upload time, so /tree, /analysis, /folder-analysis and /file always agree
    on paths with what was returned right after upload."""
    b=base(pid)
    if not b.exists(): raise HTTPException(404,'Project files not found')
    return normalize_root(b)

@router.post('/projects/{project_id}/upload')
async def upload_project(project_id:str, file:UploadFile=File(...), project_name:str=Form(''), user_id:str=Form('default-user'), db:AsyncSession=Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith('.zip'):
        raise HTTPException(400,'Send the project folder as a .zip archive.')
    b=base(project_id); b.mkdir(parents=True,exist_ok=True)
    existing=await db.get(Project, project_id)
    if existing is None:
        existing=Project(
            id=project_id,
            user_id=user_id,
            name=project_name or Path(file.filename).stem,
            description='Uploaded project',
            repository_path=str(b),
            technology='',
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.add(existing)
        await db.commit()
    else:
        # The frontend creates the Project row first and uploads the ZIP second.
        # Bind the project to its extracted workspace so Chat/Analysis can use it.
        existing.repository_path = str(b)
        existing.name = project_name or existing.name
    tmp=Path(tempfile.mktemp(suffix='.zip'))
    try:
        tmp.write_bytes(await file.read())
        root=save_project(b,tmp)
        result=analyze(root)
        (b/'analysis.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        existing.repository_path = str(b)
        # Store a lightweight detected stack for project-aware Chat/Analysis.
        types = result.get('file_types', {}) or {}
        detected = []
        if '.py' in types: detected.append('Python')
        if any(ext in types for ext in ('.ts', '.tsx')): detected.append('TypeScript')
        if any(ext in types for ext in ('.js', '.jsx')): detected.append('JavaScript')
        if '.java' in types: detected.append('Java')
        if '.go' in types: detected.append('Go')
        existing.technology = ', '.join(detected)
        existing.updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
        existing.open_issues=len(result.get('issues', []))
        existing.health='good' if result.get('code_health',0)>=80 else ('warning' if result.get('code_health',0)>=60 else 'critical')
        existing.test_status='available' if result.get('test_files') else 'not-detected'
        db.add(Notification(id=str(__import__('uuid').uuid4()),user_id=existing.user_id,project_id=project_id,category='analysis',title='Analysis completed',message=f'Project {existing.name} was analyzed successfully.',read=False,created_at=datetime.now(timezone.utc).replace(tzinfo=None)))
        await db.commit()
        return {'project_id':project_id,'project_name':project_name or root.name,'root':root.name,'tree':tree(root),'analysis':result}
    finally:
        tmp.unlink(missing_ok=True)

@router.get('/projects/{project_id}/tree')
async def project_tree(project_id:str):
    root=find_root(project_id); return {'project_id':project_id,'root':root.name,'tree':tree(root)}

@router.post('/projects/{project_id}/analyze')
async def analyze_project(project_id:str, db:AsyncSession=Depends(get_db)):
    root=find_root(project_id); result=analyze(root)
    (base(project_id)/'analysis.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    existing=await db.get(Project, project_id)
    if existing:
        existing.open_issues=len(result.get('issues', []))
        existing.health='good' if result.get('code_health',0)>=80 else ('warning' if result.get('code_health',0)>=60 else 'critical')
        existing.test_status='available' if result.get('test_files') else 'not-detected'
        existing.updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
        await db.commit()
    return result

@router.get('/projects/{project_id}/analysis')
async def get_analysis(project_id:str, db:AsyncSession=Depends(get_db)):
    root=find_root(project_id)
    result=await full_analysis(root)
    p=base(project_id)/'analysis.json'
    p.write_text(json.dumps(result, indent=2), encoding='utf-8')
    existing=await db.get(Project, project_id)
    if existing:
        existing.open_issues=len(result.get('issues', []))
        existing.health='good' if result.get('code_health',0)>=80 else ('warning' if result.get('code_health',0)>=60 else 'critical')
        existing.test_status='available' if result.get('test_files') else 'not-detected'
        existing.updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
        await db.commit()
    return result

@router.post('/projects/{project_id}/folder-analysis')
async def analyze_folder(project_id:str,path:str=Form(...)):
    root=find_root(project_id); target=(root/path).resolve()
    if not str(target).startswith(str(root.resolve())) or not target.exists(): raise HTTPException(404,'Folder not found')
    if not target.is_dir(): raise HTTPException(400,'Path is not a folder')
    result=analyze(target); result['selected_path']=path; return result

@router.get('/projects/{project_id}/file')
async def file_info(project_id:str,path:str):
    root=find_root(project_id); target=(root/path).resolve()
    if not str(target).startswith(str(root.resolve())) or not target.exists() or not target.is_file(): raise HTTPException(404,'File not found')
    text=target.read_text(encoding='utf-8',errors='ignore')
    return {'path':path,'name':target.name,'lines':text.count('\n')+1,'size':target.stat().st_size,'extension':target.suffix,'content':text[:200000]}
