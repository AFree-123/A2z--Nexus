export default function AgentBadge({ agent }) {
  if (!agent) return null;
  return (
    <span className="inline-flex items-center gap-1.5 text-[11px] text-muted mb-1.5">
      <span className="w-1.5 h-1.5 rounded-full bg-secondary" />
      A2Z Nexus · {agent}
    </span>
  );
}
