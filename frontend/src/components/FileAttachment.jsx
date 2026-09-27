import { File, X } from "lucide-react";

export default function FileAttachment({ file, onRemove }) {
  const sizeKb = (file.size / 1024).toFixed(0);
  return (
    <div className="flex items-center gap-2 rounded-lg border border-line bg-white px-2.5 py-1.5">
      <File size={15} className="text-primary shrink-0" />
      <div className="min-w-0">
        <p className="text-xs text-ink truncate max-w-[140px]">{file.name}</p>
        <p className="text-[10px] text-muted">{sizeKb} KB</p>
      </div>
      <button onClick={onRemove} className="text-muted hover:text-ink" aria-label="Remove attachment">
        <X size={13} />
      </button>
    </div>
  );
}
