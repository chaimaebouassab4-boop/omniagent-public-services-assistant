import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

/** Labelled text input with validation messaging. */
export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, id, label, error, ...props }, ref) => {
    const inputId = id ?? props.name;
    const errorId = error && inputId ? `${inputId}-error` : undefined;

    return (
      <label className="grid w-full gap-2 text-sm font-medium text-slate-700">
        {label}
        <input
          ref={ref}
          id={inputId}
          aria-invalid={Boolean(error)}
          aria-describedby={errorId}
          className={cn(
            "h-11 w-full rounded-lg border border-input bg-white px-3 text-slate-950 shadow-sm transition-colors placeholder:text-slate-400",
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

Input.displayName = "Input";
