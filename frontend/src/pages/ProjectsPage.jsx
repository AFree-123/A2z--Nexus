import { useEffect, useMemo, useState } from "react";
import { ChevronDown, ChevronRight, File, Folder, Search, RefreshCw } from "lucide-react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";

const API = import.meta.env.VITE_API_URL || "http://localhost:4000";

function Tree({ items, selected, onSelect, level = 0 }) {
  return <div>{items.map(item => <TreeItem key={item.path} item={item} selected={selected} onSelect={onSelect} level={level} />)}</div>;
}
function TreeItem({ item, selected, onSelect, level }) {
  const [open, setOpen] = useState(level < 1);
  const has = item.type === "folder" && item.children?.length;
  return <>
    <button onClick={() => { if (has) setOpen(v=>!v); onSelect(item); }} className={`w-full flex items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm ${selected?.path===item.path ? "bg-[#e8ecff] text-[#3049c7]" : "text-[#172554] hover:bg-white/70"}`} style={{paddingLeft: 8 + level*16}}>
      {has ? (open ? <ChevronDown size={14}/> : <ChevronRight size={14}/>) : <span className="w-[14px]"/>}
      {item.type === "folder" ? <Folder size={16} className="text-[#5b6ee1]"/> : <File size={15} className="text-[#7b84a5]"/>}
      <span className="truncate">{item.name}</span>
    </button>
    {open && has && <Tree items={item.children} selected={selected} onSelect={onSelect} level={level+1}/>} 
  </>;
}

export default function ProjectsPage() {
  const [projects,setProjects]=useState([]); const [project,setProject]=useState(null); const [tree,setTree]=useState([]); const [selected,setSelected]=useState(null); const [q,setQ]=useState("");
  const [loading,setLoading]=useState(true); const navigate=useNavigate();
  async function load(){ setLoading(true); try { const r=await fetch(`${API}/api/projects?user_id=default-user`); const data=await r.json(); setProjects(data); if(data[0]) await openProject(data[0]); } finally {setLoading(false);} }
  async function openProject(p){ setProject(p); localStorage.setItem("a2z-nexus-project-id",p.id); try{const r=await fetch(`${API}/api/workspace/projects/${p.id}/tree`); if(r.ok){const d=await r.json();setTree(d.tree||[]);}}catch{} }
  useEffect(()=>{load()},[]);
  const visible=useMemo(()=>projects.filter(p=>p.name.toLowerCase().includes(q.toLowerCase())),[projects,q]);
  return <div className="flex h-screen bg-[#f7f8ff] text-[#172554]">
    <Sidebar open={true} mobileOpen={true} usage={{used:0,limit:10}} onNewChat={()=>navigate('/chat')}/>
    <main className="flex-1 min-w-0 overflow-hidden">
      <div className="h-full flex flex-col p-5 md:p-7">
        <div className="flex items-center justify-between mb-5"><div><h1 className="text-2xl font-bold">Projects</h1><p className="text-sm text-[#7b84a5] mt-1">Your project folders from chat</p></div><div className="flex items-center gap-2"><div className="relative"><Search className="absolute left-3 top-2.5 text-[#8b93b1]" size={17}/><input value={q} onChange={e=>setQ(e.target.value)} placeholder="Search folders or files..." className="w-64 rounded-xl border border-[#e1e5f2] bg-white px-9 py-2 text-sm outline-none"/></div><button onClick={load} className="p-2 rounded-xl border border-[#e1e5f2] bg-white"><RefreshCw size={17}/></button></div></div>
        <div className="flex-1 min-h-0 grid grid-cols-[280px_1fr] gap-4">
          <section className="rounded-2xl border border-[#e1e5f2] bg-white p-4 overflow-auto"><div className="font-semibold mb-3">Files</div>{loading?<div className="text-sm text-[#7b84a5]">Loading...</div>:!project?<div className="text-sm text-[#7b84a5]">No project yet. Send a project from Chat.</div>:<><button onClick={()=>openProject(project)} className="flex items-center gap-2 text-sm font-semibold mb-2"><Folder size={17} className="text-[#5b6ee1]"/>{project.name}</button><Tree items={tree} selected={selected} onSelect={setSelected}/></>}</section>
          <section className="rounded-2xl border border-[#e1e5f2] bg-white p-5 overflow-auto"><div className="flex items-center justify-between border-b border-[#eef0f6] pb-4"><div><div className="flex items-center gap-2"><Folder size={20} className="text-[#5b6ee1]"/><h2 className="text-lg font-semibold">{selected?.name || project?.name || "Select a project"}</h2></div><p className="text-xs text-[#8b93b1] mt-1">{selected?.path || "/"}</p></div>{selected?.type === 'folder' && <button onClick={()=>navigate(`/analysis?project=${project.id}&path=${encodeURIComponent(selected.path)}`)} className="rounded-xl bg-[#4f46e5] text-white px-4 py-2 text-sm font-semibold">Analyze Folder</button>}</div>
            {selected?.type==='folder' ? <Tree items={selected.children||[]} selected={null} onSelect={setSelected}/> : selected?.type==='file' ? <div className="mt-8"><button onClick={()=>navigate(`/analysis?project=${project.id}&path=${encodeURIComponent(selected.path)}`)} className="text-sm text-[#4f46e5] font-semibold">Open file analysis →</button></div> : <div className="h-full min-h-[280px] flex items-center justify-center text-center text-[#7b84a5]">Select a file or folder<br/><span className="text-xs">Choose an item from the left panel.</span></div>}
          </section>
        </div>
      </div>
    </main>
  </div>
}
