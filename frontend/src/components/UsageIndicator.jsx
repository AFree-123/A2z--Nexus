export default function UsageIndicator({ used = 4, limit = 10 }) {
  const pct = Math.min(100, (used / limit) * 100);
  const reached = used >= limit;
  const remaining = Math.max(0, limit - used);

  return (
    <div className="px-3 py-3 rounded-xl bg-bgSoft border border-line">
      <div className="flex items-center justify-between text-xs mb-2">
        <span className="text-muted font-medium">Chats today</span>
        <span className="text-ink font-semibold">
          {used} / {limit}
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-white overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${pct}%`,
            background: reached ? "#EF4444" : "linear-gradient(90deg,#A78BFA,#7C3AED)",
          }}
        />
      </div>
      <p className="text-[11px] text-muted mt-2 leading-snug">
        {reached
          ? "Daily new-chat limit reached. Your existing chats stay open."
          : `${remaining} new chat${remaining === 1 ? "" : "s"} remaining today`}
      </p>
    </div>
  );
}
