import { CheckCircle2, Clock3, XCircle } from "lucide-react";
import { formatDate } from "../../lib/utils";
import type { AuditLog } from "../../types/api";

interface CaseTimelineProps {
  logs: AuditLog[];
}

const iconMap = {
  created: Clock3,
  uploaded: Clock3,
  approved: CheckCircle2,
  rejected: XCircle,
  commented: Clock3
};

/** Timeline of auditable case actions for citizens and admins. */
export function CaseTimeline({ logs }: CaseTimelineProps): JSX.Element {
  return (
    <ol className="space-y-4">
      {logs.map((log) => {
        const Icon = iconMap[log.action];
        return (
          <li key={log.id} className="flex gap-3">
            <span className="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-full bg-slate-100 text-primary">
              <Icon className="h-4 w-4" aria-hidden="true" />
            </span>
            <div>
              <p className="font-semibold capitalize text-slate-950">{log.action}</p>
              <p className="text-sm text-slate-500">{formatDate(log.timestamp)}</p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
