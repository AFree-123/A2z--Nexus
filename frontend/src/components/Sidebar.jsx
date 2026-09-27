import { useEffect, useMemo, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Plus,
  MessageSquare,
  Folder,
  Bell,
  BarChart3,
  History,
  ChevronDown,
  ChevronsLeft,
  ChevronsRight,
  ArrowRight,
} from "lucide-react";

import A2ZNexusLogo from "./A2ZNexusLogo";
import ChatHistoryItem from "./ChatHistoryItem";
import ConfirmModal from "./ConfirmModal";

export default function Sidebar({
  open = true,
  onToggle,

  activeChat,
  chats = [],

  onSelectChat,
  onNewChat,
  onDeleteChat,
  onShareChat,

  mobileOpen = true,
  onCloseMobile,

  usage = {
    used: 0,
    limit: 10,
  },
}) {
  // =====================================================
  // SIDEBAR STATE
  // =====================================================

  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(open);

  useEffect(() => {
    setSidebarOpen(open);
  }, [open]);

  function toggleSidebar() {
    setSidebarOpen((prev) => !prev);
    onToggle?.();
  }

  // =====================================================
  // STATES
  // =====================================================

  const [pendingDelete, setPendingDelete] = useState(null);
  const [historyOpen, setHistoryOpen] = useState(true);

  // =====================================================
  // SESSION
  // =====================================================

  let session = null;

  try {
    session = JSON.parse(
      localStorage.getItem("a2z-nexus-session") || "null"
    );
  } catch {
    session = null;
  }

  // =====================================================
  // GROUP CHAT HISTORY
  // =====================================================

  const groupedChats = useMemo(() => {
    const groups = {
      Today: [],
      Yesterday: [],
      "Previous 7 Days": [],
      Older: [],
    };

    const cleanChats = Array.isArray(chats) ? chats : [];

    const now = new Date();

    cleanChats.forEach((chat) => {
      const date = new Date(
        chat.updatedAt ||
          chat.createdAt ||
          Date.now()
      );

      const today = new Date(now);
      today.setHours(0, 0, 0, 0);

      const chatDate = new Date(date);
      chatDate.setHours(0, 0, 0, 0);

      const diffDays = Math.floor(
        (today.getTime() - chatDate.getTime()) /
          (1000 * 60 * 60 * 24)
      );

      if (diffDays === 0) {
        groups.Today.push(chat);
      } else if (diffDays === 1) {
        groups.Yesterday.push(chat);
      } else if (diffDays <= 7) {
        groups["Previous 7 Days"].push(chat);
      } else {
        groups.Older.push(chat);
      }
    });

    return Object.entries(groups).filter(
      ([, items]) => items.length > 0
    );
  }, [chats]);

  // =====================================================
  // DELETE / SHARE
  // =====================================================

  function handleAction(action, chatId) {
    if (action === "delete") {
      setPendingDelete(chatId);
      return;
    }

    if (action === "share") {
      onShareChat?.(chatId);
    }
  }

  function confirmDelete() {
    if (!pendingDelete) return;

    onDeleteChat?.(pendingDelete);

    setPendingDelete(null);
  }

  // =====================================================
  // MOBILE
  // =====================================================

  function closeMobileSidebar() {
    onCloseMobile?.();
  }

  // =====================================================
  // NEW CHAT
  // =====================================================

  function handleNewChat() {
    onNewChat?.();
  }

  // =====================================================
  // UI
  // =====================================================

  return (
    <>
      {/* =================================================
          MOBILE OVERLAY
      ================================================= */}

      {mobileOpen && (
        <div
          className="
            fixed
            inset-0
            z-40
            bg-black/30
            backdrop-blur-[2px]
            md:hidden
          "
          onClick={closeMobileSidebar}
        />
      )}

      {/* =================================================
          SIDEBAR
      ================================================= */}

      <aside
        className={`
          fixed
          md:relative
          top-0
          left-0
          z-50
          h-full
          shrink-0
          flex
          flex-col
          overflow-visible

          border-r
          border-[#e5e8f3]

          bg-gradient-to-b
          from-[#f9faff]
          via-[#f5f7ff]
          to-[#eef2ff]

          transition-all
          duration-300
          ease-in-out

          ${
            mobileOpen
              ? "translate-x-0"
              : "-translate-x-full md:translate-x-0"
          }

          ${
            sidebarOpen
              ? "w-[315px]"
              : "w-[72px]"
          }
        `}
      >
        {/* =================================================
            TOP BRAND HEADER
        ================================================= */}

        <div
          className={`
            relative
            flex
            items-center
            h-[145px]
            shrink-0
            border-b
            border-[#e5e8f3]
            transition-all
            duration-300

            ${
              sidebarOpen
                ? "px-4 justify-center"
                : "px-2 justify-center"
            }
          `}
        >
          {/* =================================================
              LOGO + NAME
          ================================================= */}

          <div
            className="
              flex
              items-center
              justify-center
              gap-3
              shrink-0
              translate-y-[8px]
              -ml-24
              transition-all
              duration-300
            "
          >
            {/* =================================================
                LOGO
            ================================================= */}

            <div
              className={`
                flex
                items-center
                justify-center
                shrink-0
                transition-all
                duration-300

                ${
                  sidebarOpen
                    ? "w-[68px] h-[68px]"
                    : "w-[48px] h-[48px]"
                }
              `}
            >
              <div
                className={`
                  transition-all
                  duration-300

                  ${
                    sidebarOpen
                      ? "scale-100"
                      : "scale-[0.72]"
                  }
                `}
              >
                <A2ZNexusLogo
                  size={
                    sidebarOpen
                      ? "md"
                      : "sm"
                  }
                />
              </div>
            </div>

            {/* =================================================
                A2Z NEXUS NAME
            ================================================= */}

            {sidebarOpen && (
              <div
                className="
                  flex
                  flex-row
                  items-center
                  whitespace-nowrap
                  leading-none
                "
              >
                <span
                  className="
                    text-[24px]
                    font-bold
                    tracking-[-0.5px]
                    text-[#172554]
                  "
                >
                  A2Z
                </span>

                <span
                  className="
                    ml-1
                    text-[24px]
                    font-medium
                    text-[#4f46e5]
                  "
                >
                  Nexus
                </span>
              </div>
            )}
          </div>

          {/* =================================================
              FLOATING SIDEBAR TOGGLE
          ================================================= */}

          <button
            type="button"
            onClick={toggleSidebar}
            title={
              sidebarOpen
                ? "Collapse sidebar"
                : "Open sidebar"
            }
            aria-label={
              sidebarOpen
                ? "Collapse sidebar"
                : "Open sidebar"
            }
            className={`
              group
              absolute
              top-1/2
              -translate-y-1/2
              z-[60]

              flex
              items-center
              justify-center

              w-[30px]
              h-[54px]

              rounded-r-[16px]
              rounded-l-[10px]

              bg-white/95
              backdrop-blur-md

              border
              border-l-0
              border-[#dfe4f2]

              text-[#6874a8]

              shadow-[4px_6px_18px_rgba(79,70,229,0.12)]

              transition-all
              duration-300
              ease-out

              hover:bg-[#f8f9ff]
              hover:text-[#4f46e5]
              hover:border-[#c9cff5]
              hover:shadow-[5px_8px_22px_rgba(79,70,229,0.20)]
              hover:w-[34px]

              active:scale-95

              ${
                sidebarOpen
                  ? "-right-[1px]"
                  : "right-[-1px]"
              }
            `}
          >
            {sidebarOpen ? (
              <ChevronsLeft
                size={18}
                strokeWidth={2.2}
                className="
                  transition-all
                  duration-300
                  group-hover:-translate-x-[1px]
                "
              />
            ) : (
              <ChevronsRight
                size={18}
                strokeWidth={2.2}
                className="
                  transition-all
                  duration-300
                  group-hover:translate-x-[1px]
                "
              />
            )}
          </button>
        </div>

        {/* =================================================
            OPEN SIDEBAR CONTENT
        ================================================= */}

        {sidebarOpen && (
          <>
            {/* =================================================
                NEW CHAT
            ================================================= */}

            <div
              className="
                px-4
                pt-4
                pb-3
                shrink-0
              "
            >
              <button
                type="button"
                onClick={handleNewChat}
                className="
                  group
                  w-full
                  h-[50px]
                  rounded-[15px]
                  flex
                  items-center
                  justify-between
                  px-4

                  text-white

                  bg-gradient-to-r
                  from-[#3267ff]
                  via-[#4f46e5]
                  to-[#7138f5]

                  shadow-[0_8px_25px_rgba(79,70,229,0.22)]

                  hover:shadow-[0_12px_32px_rgba(79,70,229,0.30)]
                  hover:-translate-y-[1px]

                  active:scale-[0.98]

                  transition-all
                "
              >
                <span
                  className="
                    flex
                    items-center
                    gap-3
                  "
                >
                  <span
                    className="
                      w-7
                      h-7
                      rounded-full
                      bg-white/20
                      flex
                      items-center
                      justify-center
                    "
                  >
                    <Plus
                      size={17}
                      strokeWidth={2.5}
                    />
                  </span>

                  <span
                    className="
                      text-[14px]
                      font-semibold
                    "
                  >
                    New Chat
                  </span>
                </span>

                <ArrowRight
                  size={17}
                  className="
                    opacity-70
                    group-hover:translate-x-1
                    transition-transform
                  "
                />
              </button>
            </div>

            {/* =================================================
                NAVIGATION
            ================================================= */}

            <nav
              className="
                px-4
                space-y-1
                shrink-0
              "
            >
              {/* CHAT */}

              <button
                type="button"
                onClick={() => navigate("/chat")}
                className="
                  w-full
                  h-[44px]
                  px-3
                  rounded-[13px]
                  flex
                  items-center
                  gap-3
                  text-left

                  bg-[#e8ecff]
                  text-[#3049c7]
                  font-semibold

                  transition
                "
              >
                <MessageSquare size={19} />

                <span className="text-[14px]">
                  Chat
                </span>
              </button>

              {/* PROJECTS */}

              <button
                type="button"
                onClick={() => navigate("/projects")}
                className="
                  w-full
                  h-[44px]
                  px-3
                  rounded-[13px]
                  flex
                  items-center
                  gap-3
                  text-left

                  text-[#172554]

                  hover:bg-white/70

                  transition
                "
              >
                <Folder size={19} />

                <span
                  className="
                    text-[14px]
                    font-medium
                  "
                >
                  Projects
                </span>
              </button>

              {/* NOTIFICATIONS */}

              <button
                type="button"
                onClick={() => navigate("/notifications")}
                className="
                  w-full
                  h-[44px]
                  px-3
                  rounded-[13px]
                  flex
                  items-center
                  gap-3
                  text-left

                  text-[#172554]

                  hover:bg-white/70

                  transition
                "
              >
                <span className="relative">
                  <Bell size={19} />

                  <span
                    className="
                      absolute
                      -right-1
                      -top-1
                      w-[6px]
                      h-[6px]
                      rounded-full
                      bg-red-500
                    "
                  />
                </span>

                <span
                  className="
                    text-[14px]
                    font-medium
                  "
                >
                  Notifications
                </span>
              </button>

              {/* ANALYTICS */}

              <button
                type="button"
                onClick={() => navigate("/analysis")}
                className="
                  w-full
                  h-[44px]
                  px-3
                  rounded-[13px]
                  flex
                  items-center
                  gap-3
                  text-left

                  text-[#172554]

                  hover:bg-white/70

                  transition
                "
              >
                <BarChart3 size={19} />

                <span
                  className="
                    text-[14px]
                    font-medium
                  "
                >
                  Analytics
                </span>
              </button>
            </nav>

            {/* =================================================
                DIVIDER
            ================================================= */}

            <div
              className="
                mx-4
                my-3
                border-t
                border-[#e1e5f2]
                shrink-0
              "
            />

            {/* =================================================
                CHAT HISTORY HEADER
            ================================================= */}

            <div className="px-4 shrink-0">
              <button
                type="button"
                onClick={() =>
                  setHistoryOpen(
                    (value) => !value
                  )
                }
                className="
                  w-full
                  flex
                  items-center
                  justify-between
                  py-2
                  text-left
                  text-[#172554]
                "
              >
                <span
                  className="
                    flex
                    items-center
                    gap-3
                  "
                >
                  <History size={19} />

                  <span
                    className="
                      text-[14px]
                      font-semibold
                    "
                  >
                    Chat History
                  </span>
                </span>

                <ChevronDown
                  size={16}
                  className={`
                    transition-transform

                    ${
                      historyOpen
                        ? "rotate-0"
                        : "-rotate-90"
                    }
                  `}
                />
              </button>
            </div>

            {/* =================================================
                CHAT HISTORY
            ================================================= */}

            {historyOpen && (
              <div
                className="
                  flex-1
                  basis-0
                  min-h-0
                  overflow-y-auto
                  overscroll-contain
                  px-4
                  pt-1
                  pb-3
                  scrollbar-thin
                "
              >
                {groupedChats.length === 0 ? (
                  <div className="px-2 py-8">
                    <div
                      className="
                        w-10
                        h-10
                        rounded-xl
                        bg-white
                        shadow-sm
                        flex
                        items-center
                        justify-center
                        mb-3
                      "
                    >
                      <MessageSquare
                        size={18}
                        className="
                          text-[#6874a8]
                        "
                      />
                    </div>

                    <p
                      className="
                        text-[13px]
                        font-semibold
                        text-[#18214d]
                      "
                    >
                      No conversations yet
                    </p>

                    <p
                      className="
                        text-[11px]
                        text-[#7b84a5]
                        mt-1
                        leading-5
                      "
                    >
                      Start a new chat to see
                      your history here.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {groupedChats.map(
                      ([label, groupChats]) => (
                        <div key={label}>
                          <div
                            className="
                              flex
                              items-center
                              justify-between
                              px-1
                              mb-2
                            "
                          >
                            <span
                              className="
                                text-[11px]
                                font-medium
                                text-[#8991ad]
                              "
                            >
                              {label}
                            </span>

                            <ChevronDown
                              size={13}
                              className="
                                text-[#a0a7bd]
                              "
                            />
                          </div>

                          <div className="space-y-1">
                            {groupChats.map(
                              (chat) => (
                                <ChatHistoryItem
                                  key={chat.id}
                                  chat={chat}
                                  active={
                                    chat.id ===
                                    activeChat
                                  }
                                  onSelect={
                                    onSelectChat
                                  }
                                  onAction={
                                    handleAction
                                  }
                                />
                              )
                            )}
                          </div>
                        </div>
                      )
                    )}
                  </div>
                )}
              </div>
            )}

            {/* =================================================
                USER PROFILE
            ================================================= */}

            <div
              className="
                px-4
                pb-5
                pt-2
                shrink-0
              "
            >
              <div
                className="
                  w-full
                  rounded-[15px]
                  px-3
                  py-3
                  flex
                  items-center
                  gap-3
                  bg-white/60
                  border
                  border-white/80
                  shadow-[0_5px_18px_rgba(70,80,160,0.08)]
                "
              >
                <div
                  className="
                    w-10
                    h-10
                    rounded-full
                    bg-gradient-to-br
                    from-[#6366f1]
                    to-[#7c3aed]
                    flex
                    items-center
                    justify-center
                    text-white
                    text-sm
                    font-bold
                    shadow-md
                    shrink-0
                  "
                >
                  {(session?.name?.[0] || session?.email?.[0] || "A").toUpperCase()}
                </div>

                <div className="min-w-0 flex-1 leading-tight">
                  <p className="text-[13px] font-semibold text-[#172554] truncate">
                    {session?.name || session?.email || "User"}
                  </p>
                  <p className="text-[10px] text-[#64748b] mt-0.5">
                    AI Workspace
                  </p>
                </div>
              </div>
            </div>
          </>
        )}

        {/* =================================================
            COLLAPSED SIDEBAR
        ================================================= */}

        {!sidebarOpen && (
          <div
            className="
              flex
              flex-1
              flex-col
              items-center
              pt-5
              gap-3
            "
          >
            {/* NEW CHAT */}

            <button
              type="button"
              onClick={handleNewChat}
              title="New Chat"
              className="
                w-11
                h-11
                rounded-[14px]

                flex
                items-center
                justify-center

                text-white

                bg-gradient-to-r
                from-[#3267ff]
                to-[#7138f5]

                shadow-[0_7px_20px_rgba(79,70,229,0.22)]

                hover:scale-105

                transition
              "
            >
              <Plus size={19} />
            </button>

            <div
              className="
                w-8
                border-t
                border-[#e0e4f0]
                my-1
              "
            />

            {/* CHAT */}

            <button
              type="button"
              title="Chat"
              className="
                w-11
                h-11
                rounded-[13px]

                flex
                items-center
                justify-center

                bg-[#e8ecff]
                text-[#3049c7]

                transition
              "
            >
              <MessageSquare size={19} />
            </button>

            {/* PROJECTS */}

            <button
              type="button"
              title="Projects"
              className="
                w-11
                h-11
                rounded-[13px]

                flex
                items-center
                justify-center

                text-[#64709a]

                hover:bg-white
                hover:text-[#3049c7]

                transition
              "
            >
              <Folder size={19} />
            </button>

            {/* NOTIFICATIONS */}

            <button
              type="button"
              title="Notifications"
              className="
                relative
                w-11
                h-11
                rounded-[13px]

                flex
                items-center
                justify-center

                text-[#64709a]

                hover:bg-white
                hover:text-[#3049c7]

                transition
              "
            >
              <Bell size={19} />

              <span
                className="
                  absolute
                  right-[9px]
                  top-[8px]
                  w-[6px]
                  h-[6px]
                  rounded-full
                  bg-red-500
                "
              />
            </button>

            {/* ANALYTICS */}

            <button
              type="button"
              title="Analytics"
              className="
                w-11
                h-11
                rounded-[13px]

                flex
                items-center
                justify-center

                text-[#64709a]

                hover:bg-white
                hover:text-[#3049c7]

                transition
              "
            >
              <BarChart3 size={19} />
            </button>

            <div className="flex-1" />

            {/* USER PROFILE */}

            <div
              className="
                w-11
                h-11
                rounded-full
                bg-gradient-to-br
                from-[#6366f1]
                to-[#7c3aed]
                flex
                items-center
                justify-center
                text-white
                text-sm
                font-bold
                shadow-md
                mb-5
              "
              title={session?.name || session?.email || "User"}
            >
              {(session?.name?.[0] || session?.email?.[0] || "A").toUpperCase()}
            </div>
          </div>
        )}
      </aside>

      {/* =================================================
          DELETE CONFIRM MODAL
      ================================================= */}

      <ConfirmModal
        open={!!pendingDelete}
        title="Delete this conversation?"
        description="This action cannot be undone."
        onCancel={() =>
          setPendingDelete(null)
        }
        onConfirm={confirmDelete}
      />
    </>
  );
}