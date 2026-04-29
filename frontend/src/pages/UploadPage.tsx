import { FileUp, Trash2 } from "lucide-react";
import { useState } from "react";
import { useParams } from "react-router-dom";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader } from "../components/ui/Card";
import { uploadCaseDocument } from "../services/cases";

interface UploadItem {
  id: string;
  file: File;
  status: "queued" | "uploaded" | "error";
}

/** Document upload route with drag-and-drop-ready file queue. */
export function UploadPage(): JSX.Element {
  const { caseId = "7f4b6c9d-7a65-4b18-b551-e94db6c49a01" } = useParams();
  const [items, setItems] = useState<UploadItem[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  function addFiles(fileList: FileList | null): void {
    if (!fileList) {
      return;
    }
    const next = Array.from(fileList).map((file) => ({
      id: crypto.randomUUID(),
      file,
      status: "queued" as const
    }));
    setItems((current) => [...current, ...next]);
  }

  async function uploadAll(): Promise<void> {
    setIsUploading(true);
    for (const item of items) {
      try {
        await uploadCaseDocument(caseId, item.file);
        setItems((current) =>
          current.map((entry) => (entry.id === item.id ? { ...entry, status: "uploaded" } : entry))
        );
      } catch {
        setItems((current) =>
          current.map((entry) => (entry.id === item.id ? { ...entry, status: "error" } : entry))
        );
      }
    }
    setIsUploading(false);
  }

  return (
    <div className="grid gap-5">
      <div>
        <h1 className="text-3xl font-extrabold text-slate-950">Upload documents</h1>
        <p className="mt-2 text-slate-600">Case ID: {caseId}</p>
      </div>
      <Card>
        <CardContent>
          <label
            className="grid min-h-56 cursor-pointer place-items-center rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 p-6 text-center transition-colors hover:border-primary hover:bg-blue-50"
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault();
              addFiles(event.dataTransfer.files);
            }}
          >
            <input
              className="sr-only"
              type="file"
              multiple
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={(event) => addFiles(event.target.files)}
            />
            <span>
              <FileUp className="mx-auto h-10 w-10 text-primary" aria-hidden="true" />
              <span className="mt-3 block text-lg font-extrabold text-slate-950">
                Drop files here or choose documents
              </span>
              <span className="mt-2 block text-sm text-slate-500">PDF, JPG, or PNG up to backend limits</span>
            </span>
          </label>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-3">
          <h2 className="font-extrabold text-slate-950">Upload queue</h2>
          <Button type="button" isLoading={isUploading} disabled={items.length === 0} onClick={uploadAll}>
            Upload all
          </Button>
        </CardHeader>
        <CardContent className="grid gap-3">
          {items.length === 0 ? (
            <p className="text-sm text-slate-500">No files selected yet.</p>
          ) : (
            items.map((item) => (
              <div key={item.id} className="flex items-center justify-between gap-3 rounded-lg bg-slate-50 p-3">
                <div>
                  <p className="font-semibold text-slate-950">{item.file.name}</p>
                  <p className="text-sm capitalize text-slate-500">{item.status}</p>
                </div>
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  aria-label={`Remove ${item.file.name}`}
                  onClick={() => setItems((current) => current.filter((entry) => entry.id !== item.id))}
                >
                  <Trash2 className="h-4 w-4" aria-hidden="true" />
                </Button>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
