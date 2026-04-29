import { AlertCircle } from "lucide-react";
import { Button } from "./Button";

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

/** Route-level error message with an optional retry action. */
export function ErrorState({ message, onRetry }: ErrorStateProps): JSX.Element {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-5 text-red-900">
      <div className="flex items-start gap-3">
        <AlertCircle className="mt-0.5 h-5 w-5" aria-hidden="true" />
        <div>
          <h2 className="font-bold">Something went wrong</h2>
          <p className="mt-1 text-sm">{message}</p>
          {onRetry ? (
            <Button className="mt-4" variant="outline" type="button" onClick={onRetry}>
              Retry
            </Button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
