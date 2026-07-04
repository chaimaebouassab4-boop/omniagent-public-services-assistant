import { Link } from "react-router-dom";
import { formatDate } from "../../lib/utils";
import type { PublicCase } from "../../types/api";
import { StatusBadge } from "../ui/Badge";
import { Button } from "../ui/Button";

interface CaseTableProps {
  cases: PublicCase[];
  admin?: boolean;
}

/** Responsive case table used by citizen tracking and admin review screens. */
export function CaseTable({ cases, admin = false }: CaseTableProps): JSX.Element {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[760px] border-collapse text-left text-sm">
        <thead>
          <tr className="border-b border-border text-xs uppercase tracking-wide text-slate-500">
            <th className="px-4 py-3">Reference</th>
            <th className="px-4 py-3">Applicant</th>
            <th className="px-4 py-3">Service</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Updated</th>
            <th className="px-4 py-3">Action</th>
          </tr>
        </thead>
        <tbody>
          {cases.map((item) => (
            <tr key={item.id} className="border-b border-border last:border-0">
              <td className="px-4 py-4 font-bold text-slate-950">{item.referenceNumber}</td>
              <td className="px-4 py-4 text-slate-700">{item.applicantName}</td>
              <td className="px-4 py-4 capitalize text-slate-700">{item.serviceType}</td>
              <td className="px-4 py-4">
                <StatusBadge status={item.status} />
              </td>
              <td className="px-4 py-4 text-slate-600">{formatDate(item.updatedAt)}</td>
              <td className="px-4 py-4">
                <Link to={admin ? `/admin/case/${item.id}` : `/upload/${item.id}`}>
                  <Button type="button" variant="outline" size="sm">
                    Open
                  </Button>
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
