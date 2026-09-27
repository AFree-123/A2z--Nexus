import { Menu, Share2, Plus, MoreVertical } from "lucide-react";

export default function ChatHeader({ title, onOpenSidebar, onShare, onNewChat }) {
  return (
    <header className="flex items-center justify-between gap-3 px-4 md:px-6 h-16 border-b border-line bg-[#ffffff]/95 backdrop-blur-sm">
      <div className="flex items-center gap-2 min-w-0">
        <button onClick={onOpenSidebar} className="md:hidden p-1.5 text-muted hover:text-ink">
          <Menu size={20} />
        </button>
        <h1 className="text-sm md:text-base font-medium text-ink truncate">{title}</h1>
      </div>

      <div className="flex items-center gap-1.5 shrink-0">
        <button
          onClick={onShare}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-ink border border-line hover:bg-bgSoft transition-colors"
        >
          <Share2 size={15} />
          <span className="hidden sm:inline">Share</span>
        </button>
        <button
          onClick={onNewChat}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-white bg-primary hover:bg-primary/90 transition-colors"
        >
          <Plus size={15} />
          <span className="hidden sm:inline">New Chat</span>
        </button>
        <button className="p-1.5 rounded-lg text-muted hover:bg-bgSoft transition-colors">
          <MoreVertical size={18} />
        </button>
      </div>
    </header>
  );
}
