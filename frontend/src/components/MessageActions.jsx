import { useState } from "react";
import { Copy, RotateCcw, ThumbsUp, ThumbsDown, MoreHorizontal, Check } from "lucide-react";

export default function MessageActions({ content }) {
  const [copied, setCopied] = useState(false);
  const [reaction, setReaction] = useState(null);

  function copy() {
    navigator.clipboard?.writeText(content).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="flex items-center gap-0.5 mt-2 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity">
      <button onClick={copy} className="p-1.5 rounded-md hover:bg-bgSoft text-muted" aria-label="Copy">
        {copied ? <Check size={14} /> : <Copy size={14} />}
      </button>
      <button className="p-1.5 rounded-md hover:bg-bgSoft text-muted" aria-label="Regenerate">
        <RotateCcw size={14} />
      </button>
      <button
        onClick={() => setReaction(reaction === "up" ? null : "up")}
        className={`p-1.5 rounded-md hover:bg-bgSoft ${reaction === "up" ? "text-primary" : "text-muted"}`}
        aria-label="Like"
      >
        <ThumbsUp size={14} />
      </button>
      <button
        onClick={() => setReaction(reaction === "down" ? null : "down")}
        className={`p-1.5 rounded-md hover:bg-bgSoft ${reaction === "down" ? "text-primary" : "text-muted"}`}
        aria-label="Dislike"
      >
        <ThumbsDown size={14} />
      </button>
      <button className="p-1.5 rounded-md hover:bg-bgSoft text-muted" aria-label="More">
        <MoreHorizontal size={14} />
      </button>
    </div>
  );
}
