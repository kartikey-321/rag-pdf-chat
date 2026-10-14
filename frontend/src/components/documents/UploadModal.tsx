
import { useState } from "react";

type UploadModalProps = {
  onClose: () => void;
};

export default function UploadModal({ onClose }: UploadModalProps) {
  const [file, setFile] = useState<File | null>(null);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="upload-title"
        className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl"
      >
        <div className="flex items-center justify-between">
          <h2 id="upload-title" className="text-xl font-semibold">
            Upload PDF
          </h2>
          <button onClick={onClose} aria-label="Close modal" className="cursor-pointer">
            ✕
          </button>
        </div>

        <input
          type="file"
          accept=".pdf,application/pdf"
          className="mt-6 w-full rounded-lg border border-slate-200 p-3 text-sm"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />

        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="rounded-lg border px-4 py-2 cursor-pointer"
          >
            Cancel
          </button>

          <button
            disabled={!file}
            className="rounded-lg bg-blue-600 px-4 py-2 text-white disabled:cursor-not-allowed disabled:opacity-50 cursor-pointer"
          >
            Upload
          </button>
        </div>
      </div>
    </div>
  );
}
