import { useNavigate } from "react-router-dom";
import {
  MessageSquare,
  FileText,
  Mic,
  Video,
  Search,
  Briefcase,
  BellRing,
  Menu,
} from "lucide-react";
import A2ZNexusLogo from "../components/A2ZNexusLogo";
import NotificationPanel from "../components/NotificationPanel";
import UsageIndicator from "../components/UsageIndicator";

const ACTIONS = [
  { icon: MessageSquare, title: "Chat", desc: "Ask anything.", to: "/dashboard" },
  { icon: FileText, title: "Documents", desc: "Create PDF, PPT, DOCX and more.", to: "/dashboard" },
  { icon: Mic, title: "Voice", desc: "Talk naturally with A2Z Nexus.", to: "/dashboard" },
  { icon: Video, title: "Video", desc: "Generate AI videos.", to: "/dashboard" },
  { icon: Search, title: "Search", desc: "Search the web intelligently.", to: "/dashboard" },
  { icon: Briefcase, title: "Jobs & Internships", desc: "Find relevant opportunities.", to: "/dashboard" },
  { icon: BellRing, title: "Reminders", desc: "Never miss an important task.", to: "/dashboard" },
];

export default function DashboardPage() {
  const navigate = useNavigate();
  const session = JSON.parse(localStorage.getItem("a2z-nexus-session") || "null");
  const displayName = session?.name || "Guest";

  return (
    <div className="min-h-screen bg-bgLight">
      <header className="flex items-center justify-between px-5 md:px-10 py-4 border-b border-line bg-white/70 backdrop-blur-sm">
        
        <div className="flex items-center gap-2">
          <NotificationPanel />
          <div className="w-8 h-8 rounded-full bg-bgSoft flex items-center justify-center text-primary text-sm font-semibold">
            {(displayName?.[0] || "G").toUpperCase()}
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-5 md:px-10 py-10 md:py-14">
        <h1 className="font-display text-3xl md:text-4xl text-ink mb-2">Good morning, {displayName}</h1>
        <p className="text-muted mb-8 md:mb-10">What would you like to accomplish today?</p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {ACTIONS.map(({ icon: Icon, title, desc, to }) => (
            <button
              key={title}
              onClick={() => navigate(to)}
              className="text-left rounded-2xl border border-line bg-white p-5 hover:shadow-premium hover:-translate-y-0.5 transition-all"
            >
              <div className="w-10 h-10 rounded-xl bg-bgSoft flex items-center justify-center text-primary mb-3">
                <Icon size={19} />
              </div>
              <p className="text-sm font-semibold text-ink mb-0.5">{title}</p>
              <p className="text-xs text-muted leading-snug">{desc}</p>
            </button>
          ))}
        </div>

        <div className="max-w-sm">
          <UsageIndicator used={4} limit={10} />
        </div>
      </main>
    </div>
  );
}
