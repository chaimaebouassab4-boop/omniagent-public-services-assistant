import { motion } from "framer-motion";
import { Send } from "lucide-react";
import { useMemo, useState } from "react";
import { cn } from "../../lib/utils";

interface ChatInputProps {
  onSend: (value: string) => void;
  disabled?: boolean;
}

const MAX_CHARS = 320;

/** Auto-growing input with animated focus, meter, and send interactions. */
export function ChatInput({ onSend, disabled = false }: ChatInputProps): JSX.Element {
  const [value, setValue] = useState("");
  const [focused, setFocused] = useState(false);
  const ratio = Math.min(value.length / MAX_CHARS, 1);
  const canSend = value.trim().length > 0 && !disabled;

  const rows = useMemo(() => Math.min(Math.max(value.split("\n").length, 1), 4), [value]);

  function submit(): void {
    const cleaned = value.trim();
    if (!cleaned || disabled) {
      return;
    }
    onSend(cleaned);
    setValue("");
  }

  return (
    <motion.div
      animate={{
        boxShadow: focused ? "0 10px 26px rgba(15, 61, 94, 0.16)" : "0 4px 12px rgba(15, 23, 42, 0.08)"
      }}
      className="rounded-2xl border border-[#d9ccb8] bg-white p-2"
    >
      <div className="flex items-end gap-2">
        <textarea
          value={value}
          rows={rows}
          maxLength={MAX_CHARS}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              submit();
            }
          }}
          aria-label="Message"
          placeholder="Sowwel b Darija / العربية / Français..."
          className={cn(
            "max-h-40 min-h-[52px] w-full resize-none rounded-xl border-0 px-3 py-3 text-sm text-slate-900 outline-none",
            "placeholder:text-slate-400"
          )}
        />
        <motion.button
          type="button"
          disabled={!canSend}
          whileHover={canSend ? { scale: 1.06 } : undefined}
          whileTap={canSend ? { scale: 0.96 } : undefined}
          onClick={submit}
          aria-label="Send"
          className={cn(
            "grid h-11 w-11 shrink-0 place-items-center rounded-xl transition-colors",
            canSend ? "bg-[#0f3d5e] text-white" : "bg-slate-200 text-slate-400"
          )}
        >
          <Send className="h-4.5 w-4.5" />
        </motion.button>
      </div>
      <div className="mt-1.5 flex items-center justify-between px-1">
        <div className="h-1.5 w-28 overflow-hidden rounded-full bg-slate-100">
          <motion.div
            animate={{ width: `${ratio * 100}%` }}
            className={cn(
              "h-full rounded-full",
              ratio > 0.85 ? "bg-amber-500" : "bg-[#0f766e]"
            )}
          />
        </div>
        <span className="text-xs font-semibold text-slate-500">
          {value.length}/{MAX_CHARS}
        </span>
      </div>
    </motion.div>
  );
}
