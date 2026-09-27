import { MoreHorizontal, Trash2, Share2 } from "lucide-react";
import { useState } from "react";

export default function ChatHistoryItem({
  chat,
  active = false,
  onSelect,
  onAction,
}) {
  const [menuOpen, setMenuOpen] = useState(false);

  const title = chat?.title || "New Chat";

  function handleSelect() {
    setMenuOpen(false);
    onSelect?.(chat.id);
  }

  function handleDelete(e) {
    e.stopPropagation();
    setMenuOpen(false);
    onAction?.("delete", chat.id);
  }

  function handleShare(e) {
    e.stopPropagation();
    setMenuOpen(false);
    onAction?.("share", chat.id);
  }

  return (
    <div
      onClick={handleSelect}
      className={`
        group
        relative
        w-full
        flex
        items-center
        gap-2
        px-3
        py-2.5
        rounded-xl
        cursor-pointer
        transition-all
        ${
          active
            ? "bg-primary/10 text-primary"
            : "text-ink hover:bg-bgSoft"
        }
      `}
    >
      {/* CHAT ICON */}
      <div
        className={`
          w-7 h-7
          rounded-lg
          flex
          items-center
          justify-center
          shrink-0
          text-xs
          font-semibold
          ${
            active
              ? "bg-primary text-white"
              : "bg-bgSoft text-muted"
          }
        `}
      >
        💬
      </div>

      {/* TITLE */}
      <div className="min-w-0 flex-1 pr-6">
        <p
          className={`
            text-sm
            truncate
            ${
              active
                ? "font-medium text-primary"
                : "text-ink"
            }
          `}
          title={title}
        >
          {title}
        </p>
      </div>

      {/* THREE DOTS */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          setMenuOpen((prev) => !prev);
        }}
        className={`
          absolute
          right-2
          top-1/2
          -translate-y-1/2
          w-7
          h-7
          rounded-lg
          flex
          items-center
          justify-center
          transition-all
          ${
            menuOpen
              ? "opacity-100 bg-bgSoft"
              : "opacity-0 group-hover:opacity-100 hover:bg-bgSoft"
          }
        `}
        aria-label="Chat options"
      >
        <MoreHorizontal size={16} />
      </button>

      {/* ACTION MENU */}
      {menuOpen && (
        <div
          onClick={(e) => e.stopPropagation()}
          className="
            absolute
            right-2
            top-full
            mt-1
            w-40
            bg-[#ffffff]
            border
            border-line
            rounded-xl
            shadow-lg
            z-50
            overflow-hidden
            py-1
          "
        >
          <button
            onClick={handleShare}
            className="
              w-full
              flex
              items-center
              gap-2
              px-3
              py-2
              text-sm
              text-ink
              hover:bg-bgSoft
              text-left
            "
          >
            <Share2 size={15} />
            Share
          </button>

          <button
            onClick={handleDelete}
            className="
              w-full
              flex
              items-center
              gap-2
              px-3
              py-2
              text-sm
              text-red-500
              hover:bg-red-50
              text-left
            "
          >
            <Trash2 size={15} />
            Delete
          </button>
        </div>
      )}
    </div>
  );
}