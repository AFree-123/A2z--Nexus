import {
  FileText,
  Presentation,
  Sheet,
  FileSpreadsheet,
  File,
  Eye,
  Download,
} from "lucide-react";

const ICONS = {
  pdf: FileText,
  pptx: Presentation,
  docx: FileText,
  xlsx: Sheet,
  csv: FileSpreadsheet,
  txt: File,
};

export default function GeneratedFileCard({ file }) {
  if (!file) return null;

  const Icon = ICONS[file.kind] || File;

  const fileName = file.name || "A2Z-Nexus-Document.docx";
  const fileUrl = file.url;

  const handlePreview = () => {
    if (!fileUrl) {
      alert("Document is not available yet.");
      return;
    }

    window.open(fileUrl, "_blank", "noopener,noreferrer");
  };

  const handleDownload = async () => {
    if (!fileUrl) {
      alert("Document is not available yet.");
      return;
    }

    try {
      const response = await fetch(fileUrl);

      if (!response.ok) {
        throw new Error("Unable to fetch document");
      }

      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = fileName;

      document.body.appendChild(link);
      link.click();
      link.remove();

      window.URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error("Download error:", error);

      // Fallback: open the document directly
      window.open(fileUrl, "_blank", "noopener,noreferrer");
    }
  };

  return (
    <div className="mt-4 w-full max-w-md rounded-xl border border-line bg-bgLight p-3">
      <div className="flex items-center gap-3">

        {/* File Icon */}
        <div className="w-11 h-11 rounded-lg bg-white border border-line flex items-center justify-center text-primary shrink-0">
          <Icon size={21} />
        </div>

        {/* File Information */}
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-ink truncate">
            {fileName}
          </p>

          <p className="text-xs text-muted mt-0.5">
            {file.type || "Microsoft Word Document"}
          </p>

          <p className="text-[11px] text-primary mt-1">
            Document generated successfully
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 shrink-0">

          <button
            type="button"
            onClick={handlePreview}
            className="w-8 h-8 rounded-lg flex items-center justify-center hover:bg-white text-muted hover:text-ink transition"
            title="Open document"
          >
            <Eye size={17} />
          </button>

          <button
            type="button"
            onClick={handleDownload}
            className="w-8 h-8 rounded-lg flex items-center justify-center hover:bg-white text-primary transition"
            title="Download document"
          >
            <Download size={17} />
          </button>

        </div>
      </div>

      {/* Download Button */}
      <button
        type="button"
        onClick={handleDownload}
        className="mt-3 w-full rounded-lg border border-line bg-white px-3 py-2 text-xs font-medium text-ink hover:bg-bgSoft transition"
      >
        Download Document
      </button>
    </div>
  );
}