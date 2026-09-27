export default function ConfirmModal({ open, title, description, confirmLabel = "Delete", onConfirm, onCancel }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/30 backdrop-blur-sm px-4">
      <div className="w-full max-w-sm rounded-2xl bg-white border border-line shadow-premium p-5">
        <h3 className="text-base font-semibold text-ink mb-1.5">{title}</h3>
        <p className="text-sm text-muted mb-5">{description}</p>
        <div className="flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm rounded-lg border border-line text-ink hover:bg-bgSoft transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 text-sm rounded-lg bg-red-600 text-white hover:bg-red-700 transition-colors"
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
