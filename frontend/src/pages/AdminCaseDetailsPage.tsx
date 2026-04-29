import { Check, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { CaseTimeline } from "../components/cases/CaseTimeline";
import { Badge, StatusBadge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader } from "../components/ui/Card";
import { LoadingState } from "../components/ui/LoadingState";
import { Modal } from "../components/ui/Modal";
import { Textarea } from "../components/ui/Textarea";
import { approveCase, getCase, rejectCase } from "../services/cases";
import type { PublicCase } from "../types/api";

/** Protected administrator case detail and decision view. */
export function AdminCaseDetailsPage(): JSX.Element {
  const { id = "7f4b6c9d-7a65-4b18-b551-e94db6c49a01" } = useParams();
  const [caseItem, setCaseItem] = useState<PublicCase | null>(null);
  const [rejectOpen, setRejectOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    getCase(id).then(setCaseItem);
  }, [id]);

  async function approve(): Promise<void> {
    setIsSubmitting(true);
    await approveCase(id).catch(() => undefined);
    setCaseItem((current) => (current ? { ...current, status: "Approved" } : current));
    setIsSubmitting(false);
  }

  async function reject(): Promise<void> {
    setIsSubmitting(true);
    await rejectCase(id, reason).catch(() => undefined);
    setCaseItem((current) => (current ? { ...current, status: "Rejected" } : current));
    setRejectOpen(false);
    setIsSubmitting(false);
  }

  if (!caseItem) {
    return <LoadingState />;
  }

  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_360px]">
      <section className="grid gap-5">
        <Card>
          <CardHeader className="flex flex-row items-start justify-between gap-3">
            <div>
              <h1 className="text-2xl font-extrabold text-slate-950">{caseItem.referenceNumber}</h1>
              <p className="mt-1 text-slate-600">{caseItem.applicantName}</p>
            </div>
            <StatusBadge status={caseItem.status} />
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-3">
            <div>
              <p className="text-sm font-semibold text-slate-500">Service</p>
              <p className="mt-1 font-bold capitalize text-slate-950">{caseItem.serviceType}</p>
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-500">Documents</p>
              <p className="mt-1 font-bold text-slate-950">{caseItem.documents.length}</p>
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-500">User ID</p>
              <p className="mt-1 break-all font-bold text-slate-950">{caseItem.userId}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <h2 className="font-extrabold text-slate-950">Documents</h2>
          </CardHeader>
          <CardContent className="grid gap-3">
            {caseItem.documents.length === 0 ? (
              <p className="text-sm text-slate-500">No documents uploaded.</p>
            ) : (
              caseItem.documents.map((document) => (
                <div key={document.id} className="flex items-center justify-between gap-3 rounded-lg bg-slate-50 p-3">
                  <span className="font-semibold text-slate-800">{document.fileName}</span>
                  <Badge>Uploaded</Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </section>
      <aside className="grid content-start gap-5">
        <Card>
          <CardHeader>
            <h2 className="font-extrabold text-slate-950">Decision</h2>
          </CardHeader>
          <CardContent className="grid gap-3">
            <Button type="button" isLoading={isSubmitting} onClick={approve}>
              <Check className="h-4 w-4" aria-hidden="true" />
              Approve
            </Button>
            <Button type="button" variant="danger" onClick={() => setRejectOpen(true)}>
              <X className="h-4 w-4" aria-hidden="true" />
              Reject
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <h2 className="font-extrabold text-slate-950">Audit timeline</h2>
          </CardHeader>
          <CardContent>
            <CaseTimeline logs={caseItem.timeline} />
          </CardContent>
        </Card>
      </aside>
      <Modal title="Reject case" isOpen={rejectOpen} onClose={() => setRejectOpen(false)}>
        <div className="grid gap-4">
          <Textarea
            label="Reason"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder="Explain which requirement was not satisfied"
          />
          <Button type="button" variant="danger" isLoading={isSubmitting} onClick={reject}>
            Confirm rejection
          </Button>
        </div>
      </Modal>
    </div>
  );
}
