import { useEffect, useState } from "react";
import { CaseTable } from "../components/cases/CaseTable";
import { CaseTimeline } from "../components/cases/CaseTimeline";
import { Card, CardContent, CardHeader } from "../components/ui/Card";
import { LoadingState } from "../components/ui/LoadingState";
import { listCases } from "../services/cases";
import type { PublicCase } from "../types/api";

/** Citizen-facing case tracking screen with status table and timeline. */
export function CasesPage(): JSX.Element {
  const [cases, setCases] = useState<PublicCase[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    listCases()
      .then(setCases)
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return <LoadingState />;
  }

  const selected = cases[0];

  return (
    <div className="grid gap-5">
      <div>
        <h1 className="text-3xl font-extrabold text-slate-950">Case tracking</h1>
        <p className="mt-2 text-slate-600">Review current status, documents, and timeline events.</p>
      </div>
      <Card>
        <CardHeader>
          <h2 className="font-extrabold text-slate-950">Your cases</h2>
        </CardHeader>
        <CardContent className="p-0">
          <CaseTable cases={cases} />
        </CardContent>
      </Card>
      {selected ? (
        <Card>
          <CardHeader>
            <h2 className="font-extrabold text-slate-950">{selected.referenceNumber} timeline</h2>
          </CardHeader>
          <CardContent>
            <CaseTimeline logs={selected.timeline} />
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
