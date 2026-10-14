import { useState } from "react";
import UploadModal from "../components/documents/UploadModal";

export default function DocumentsPage() {
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  return (
    <div className="mx-auto max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">
            My Documents
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Upload and manage your PDF documents.
          </p>
        </div>

        <button
          type="button"
          className="rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 cursor-pointer"
          onClick={() => setIsUploadOpen(true)}
        >
          + Upload PDF
        </button>
      </div>

      <div className="mt-8 overflow-hidden rounded-xl border border-slate-200">
        <div className="grid grid-cols-3 border-b border-slate-200 bg-slate-50 px-5 py-3 text-sm font-medium text-slate-600">
          <span>Document Name</span>
          <span>Uploaded On</span>
          <span>Status</span>
        </div>

        <div className="px-5 py-12 text-center">
          <p className="font-medium text-slate-700">
            No documents uploaded yet
          </p>
          <p className="mt-1 text-sm text-slate-500">
            Upload your first PDF to start chatting.
          </p>
        </div>
      </div>
      {isUploadOpen && <UploadModal onClose={() => setIsUploadOpen(false)} />}
    </div>
  );
}
