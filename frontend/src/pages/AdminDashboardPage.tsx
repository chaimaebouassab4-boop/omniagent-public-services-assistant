import { CheckCircle2, Clock3, FileWarning } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { CaseTable } from "../components/cases/CaseTable";
import { Card, CardContent, CardHeader } from "../components/ui/Card";
import { listCases } from "../services/cases";
import type { PublicCase } from "../types/api";

/** Protected admin dashboard with metrics and review queue. */
export function AdminDashboardPage(): JSX.Element {
  const [cases, setCases] = useState<PublicCase[]>([]);

  useEffect(() => {
    listCases().then(setCases);
  }, []);

  const metrics = useMemo(
    () => [
      {
        label: "Submitted",
        value: cases.filter((item) => item.status === "Submitted").length,
        icon: Clock3,
        color: "text-civic-amber"
      },
      {
        label: "Approved",
        value: cases.filter((item) => item.status === "Approved").length,
        icon: CheckCircle2,
        color: "text-civic-teal"
      },
      {
        label: "Rejected",
        value: cases.filter((item) => item.status === "Rejected").length,
        icon: FileWarning,
        color: "text-civic-rose"
      }
    ],
    [cases]
  );

  return (
    <div className="grid gap-5">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-950">Admin dashboard</h1>
          <p className="mt-2 text-slate-600">Review submitted cases and monitor processing workload.</p>
        </div>
      </div>
      <section className="grid gap-4 md:grid-cols-3" aria-label="Case metrics">
        {metrics.map((metric) => (
          <Card key={metric.label}>
            <CardContent className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-slate-500">{metric.label}</p>
                <p className="mt-2 text-3xl font-extrabold text-slate-950">{metric.value}</p>
              </div>
              <metric.icon className={`h-8 w-8 ${metric.color}`} aria-hidden="true" />
            </CardContent>
          </Card>
        ))}
      </section>
      <Card>
        <CardHeader>
          <h2 className="font-extrabold text-slate-950">Review queue</h2>
        </CardHeader>
        <CardContent className="p-0">
          <CaseTable cases={cases} admin />
        </CardContent>
      </Card>
    </div>
  );
}
