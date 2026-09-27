import { useState } from "react";
import { Link2, Check, X } from "lucide-react";

export default function ShareModal({ open, onClose, shareUrl = "https://a2znexus.ai/share/8f3k2n" }) {
  const [copied, setCopied] = useState(false);

  if (!open) return null;

  function copyLink() {
    navigator.clipboard?.writeText(shareUrl).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/30 backdrop-blur-sm px-4">
      <div className="w-full max-w-md rounded-2xl bg-white border border-line shadow-premium p-6">
        <div className="flex items-start justify-between mb-1">
          <h3 className="text-base font-semibold text-ink">Share this conversation</h3>
          <button onClick={onClose} className="p-1 rounded-md hover:bg-bgSoft text-muted">
            <X size={16} />
          </button>
        </div>
        <p className="text-sm text-muted mb-4">
          Anyone with this link can view this shared conversation. Your other chats and account details stay private.
        </p>

        <div className="flex items-center gap-2 rounded-xl border border-line bg-bgLight px-3 py-2.5 mb-4">
          <Link2 size={16} className="text-muted shrink-0" />
          <span className="text-sm text-ink truncate flex-1">{shareUrl}</span>
        </div>

        <div className="flex items-center justify-between gap-2">
          <button className="text-sm text-red-600 hover:underline">Disable link</button>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm rounded-lg border border-line text-ink hover:bg-bgSoft transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={copyLink}
              className="px-4 py-2 text-sm rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors flex items-center gap-1.5"
            >
              {copied ? <Check size={14} /> : <Link2 size={14} />}
              {copied ? "Copied" : "Copy link"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
