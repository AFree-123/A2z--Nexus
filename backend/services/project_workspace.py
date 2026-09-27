from __future__ import annotations
import ast, json, os, re, shutil, subprocess, tempfile, zipfile
from pathlib import Path
from datetime import datetime, timezone

IGNORE_DIRS={'.git','node_modules','.venv','venv','__pycache__','.next','dist','build','coverage','.idea','.pytest_cache'}
CODE_EXT={'.py','.js','.jsx','.ts','.tsx','.java','.c','.cpp','.cs','.go','.rs','.php','.rb','.swift','.kt'}
TEXT_EXT=CODE_EXT|{'.json','.yaml','.yml','.toml','.ini','.md','.txt','.env','.html','.css','.scss','.sql','.xml','.sh','.ps1'}

def now(): return datetime.now(timezone.utc).isoformat()

def safe_extract(z: zipfile.ZipFile, dest: Path):
    root=dest.resolve()
    for m in z.infolist():
        target=(dest/m.filename).resolve()
        if not str(target).startswith(str(root)):
            raise ValueError('Unsafe archive path')
    z.extractall(dest)

# Files the backend itself writes into a project's workspace folder after
# extraction. These must NOT count as "real" project content when deciding
# whether the zip had a single wrapper folder, otherwise the detected root
# silently changes between upload time and every later request (upload vs.
# GET /tree, /analysis, /folder-analysis, /file all disagreeing on the root
# causes "File/Folder not found" errors for files that clearly exist).
GENERATED_FILES = {'analysis.json', '.DS_Store', 'Thumbs.db'}

def normalize_root(dest: Path):
    entries=[p for p in dest.iterdir() if p.name not in {'__MACOSX'} and p.name not in GENERATED_FILES]
    dirs=[p for p in entries if p.is_dir()]
    files=[p for p in entries if p.is_file()]
    if len(dirs)==1 and not files:
        return dirs[0]
    return dest

def iter_files(root: Path):
    for p in root.rglob('*'):
        if not p.is_file(): continue
        if any(part in IGNORE_DIRS for part in p.parts): continue
        yield p

def tree(root: Path):
    def walk(p: Path):
        out=[]
        for x in sorted(p.iterdir(), key=lambda q:(q.is_file(), q.name.lower())):
            if x.name in IGNORE_DIRS: continue
            rel=str(x.relative_to(root)).replace('\\','/')
            item={'name':x.name,'path':rel,'type':'file' if x.is_file() else 'folder'}
            if x.is_dir(): item['children']=walk(x)
            out.append(item)
        return out
    return walk(root)

def read_text(p: Path, limit=300_000):
    try: return p.read_text(encoding='utf-8', errors='ignore')[:limit]
    except Exception: return ''

def complexity_for_python(text):
    try:
        t=ast.parse(text)
    except Exception: return 0,0,0
    funcs=classes=0; complexity=1
    for n in ast.walk(t):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)): funcs+=1
        elif isinstance(n,ast.ClassDef): classes+=1
        elif isinstance(n,(ast.If,ast.For,ast.While,ast.Try,ast.With,ast.ExceptHandler,ast.IfExp,ast.BoolOp,ast.comprehension)): complexity+=1
    return funcs,classes,complexity

def analyze(root: Path, rel_prefix=''):
    files=list(iter_files(root))
    selected=[p for p in files if p.suffix.lower() in TEXT_EXT or p.name in {'Dockerfile','Makefile'}]
    total_lines=0; funcs=classes=complexity=0; issues=[]; types={}; top=[]
    for p in selected:
        text=read_text(p); lines=text.count('\n')+ (1 if text else 0); total_lines+=lines
        ext=p.suffix.lower() or p.name
        types[ext]=types.get(ext,0)+1
        f=c=cx=0
        if ext=='.py': f,c,cx=complexity_for_python(text)
        else:
            f=len(re.findall(r'\b(?:function\s+\w+|(?:const|let|var)\s+\w+\s*=\s*(?:async\s*)?\()',text))
            c=len(re.findall(r'\bclass\s+\w+',text)); cx=1+len(re.findall(r'\b(?:if|for|while|catch|case)\b|&&|\|\|',text))
        funcs+=f; classes+=c; complexity+=cx
        rel=str(p.relative_to(root)).replace('\\','/')
        top.append({'file':rel,'lines':lines})
        for pat,title,severity in [
            (r'\beval\s*\(', 'Use of eval detected','high'),
            (r'(?i)(api[_-]?key|secret|password)\s*=\s*["\'][^"\']+["\']', 'Possible hard-coded secret','high'),
            (r'(?i)\bSELECT\b.*\+.*\bFROM\b', 'Possible SQL injection pattern','high'),
            (r'(?i)TODO|FIXME', 'Unresolved TODO/FIXME marker','low'),
        ]:
            if re.search(pat,text):
                issues.append({'file':rel,'title':title,'severity':severity,'evidence':'Static scan match'})
        if ext=='.py' and text and 'except:' in text:
            issues.append({'file':rel,'title':'Bare except can hide errors','severity':'medium','evidence':'Static Python scan'})
    top.sort(key=lambda x:x['lines'], reverse=True)
    tests=[str(p.relative_to(root)).replace('\\','/') for p in files if re.search(r'(^test_|_test\.|tests?[/\\])',str(p))]
    deps=[]
    for name in ['requirements.txt','pyproject.toml','package.json','pom.xml','build.gradle','go.mod','Cargo.toml']:
        p=root/name
        if p.exists(): deps.append(name)
    deploy=[]
    for name in ['Dockerfile','docker-compose.yml','vercel.json','render.yaml','netlify.toml','fly.toml','Procfile']:
        if (root/name).exists(): deploy.append(name)
    if (root/'.env.example').exists(): deploy.append('.env.example')
    security=sum(1 for i in issues if i['severity']=='high')
    health=max(0,min(100,100-security*18-len([i for i in issues if i['severity']=='medium'])*7-len([i for i in issues if i['severity']=='low'])*2))
    maintain=max(0,min(100,100-(complexity//max(1,len(selected)))*3))
    avg_complexity=round(complexity/max(1,len(selected)),1)
    complexity_label='Low' if avg_complexity<4 else 'Medium' if avg_complexity<10 else 'High'
    return {
        'analyzed_at':now(),'root':str(root),'total_files':len(files),'analyzed_files':len(selected),'lines_of_code':total_lines,
        'functions':funcs,'classes':classes,'dependencies':deps,'deployment_files':deploy,'test_files':tests,
        'code_health':health,'maintainability':maintain,'complexity_score':avg_complexity,'complexity':complexity_label,
        'security_score':max(0,100-security*25),'test_coverage':None,'file_types':types,'top_files':top[:10],'issues':issues,
        'recommendations':[{'priority':'HIGH' if i['severity']=='high' else 'MEDIUM','title':i['title'],'file':i['file']} for i in issues[:10]],
        'deployment_readiness': bool(deploy) and not any(i['severity']=='high' for i in issues),
        'submission_readiness': max(0,min(100,health + (10 if tests else 0) + (5 if deps else 0) + (5 if deploy else 0))),
    }

def save_project(project_dir: Path, archive: Path):
    if project_dir.exists(): shutil.rmtree(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z: safe_extract(z, project_dir)
    root=normalize_root(project_dir)
    return root
