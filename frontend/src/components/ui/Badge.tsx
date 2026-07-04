import { type HTMLAttributes } from "react";
import { cn } from "../../lib/utils";
import type { CaseStatus } from "../../types/api";

const statusStyles: Record<CaseStatus, string> = {
  Submitted: "bg-[#F8EFD8] text-[#111A33]",
  Approved: "bg-[#CFE8CC] text-[#3F7A38]",
  Rejected: "bg-[#FCE8E3] text-[#D96A50]"
};

interface StatusBadgeProps {
  status: CaseStatus;
}

/** Compact semantic badge for case state. */
export function StatusBadge({ status }: StatusBadgeProps): JSX.Element {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2.5 py-1 text-xs font-bold",
        statusStyles[status]
      )}
    >
      {status}
    </span>
  );
}

/** Generic compact label badge. */
export function Badge({
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement>): JSX.Element {
  return (
    <span
      className={cn(
        "inline-flex rounded-full bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-700",
        className
      )}
      {...props}
    />
  );
}
