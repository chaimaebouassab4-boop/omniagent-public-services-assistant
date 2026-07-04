/** Consistent loading placeholder for route-level data fetches. */
export function LoadingState(): JSX.Element {
  return (
    <div className="grid min-h-64 place-items-center rounded-lg border border-dashed border-border bg-white">
      <div className="text-center">
        <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-primary" />
        <p className="mt-3 text-sm font-semibold text-slate-600">Loading case data</p>
      </div>
    </div>
  );
}
