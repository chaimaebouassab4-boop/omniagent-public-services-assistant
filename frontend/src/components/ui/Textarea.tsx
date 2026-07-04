import { forwardRef, type TextareaHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

/** Labelled textarea with accessible error output. */
export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, id, label, error, ...props }, ref) => {
    const inputId = id ?? props.name;
    const errorId = error && inputId ? `${inputId}-error` : undefined;

    return (
      <label className="grid gap-2 text-sm font-medium text-slate-700">
        {label}
        <textarea
          ref={ref}
          id={inputId}
          aria-invalid={Boolean(error)}
          aria-describedby={errorId}
          className={cn(
            "min-h-28 rounded-lg border border-input bg-white px-3 py-2 text-slate-950 shadow-sm transition-colors placeholder:text-slate-400",
            error && "border-civic-rose",
            className
          )}
          {...props}
        />
        {error ? (
          <span id={errorId} className="text-sm font-medium text-civic-rose">
            {error}
          </span>
        ) : null}
      </label>
    );
  }
);

Textarea.displayName = "Textarea";
