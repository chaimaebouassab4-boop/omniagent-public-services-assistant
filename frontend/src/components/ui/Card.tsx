import { type HTMLAttributes } from "react";
import { cn } from "../../lib/utils";

/** Panel component for repeated resources and compact dashboard blocks. */
export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>): JSX.Element {
  return (
    <div
      className={cn("rounded-lg border border-[#EAC79F] bg-white shadow-panel", className)}
      {...props}
    />
  );
}

/** Standard card header with consistent spacing. */
export function CardHeader({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>): JSX.Element {
  return <div className={cn("border-b border-border p-5", className)} {...props} />;
}

/** Standard card body with consistent spacing. */
export function CardContent({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>): JSX.Element {
  return <div className={cn("p-5", className)} {...props} />;
}
