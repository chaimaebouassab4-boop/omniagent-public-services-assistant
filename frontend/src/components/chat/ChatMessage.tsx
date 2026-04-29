import { AnimatePresence, motion } from "framer-motion";
import { CheckCheck, Clock3, Pencil, Trash2 } from "lucide-react";
import { useState } from "react";
import { cn, formatDate } from "../../lib/utils";
import type { ChatMessage as ChatMessageType } from "../../types/api";

interface ChatMessageProps {
  message: ChatMessageType;
  index: number;
}

/** Animated message bubble with send/read state and micro-interactions. */
export function ChatMessage({ message, index }: ChatMessageProps): JSX.Element {
  const [showActions, setShowActions] = useState(false);
  const isUser = message.sender === "citizen";
  const isAdmin = message.sender === "admin";

  const initial = isUser
    ? { opacity: 0, x: 28, y: 16, scale: 0.96 }
    : isAdmin
      ? { opacity: 0, x: -24, y: 12, rotate: -2 }
      : { opacity: 0, y: 20, scale: 0.96 };

  return (
    <motion.article
      initial={initial}
      animate={{ opacity: 1, x: 0, y: 0, rotate: 0, scale: 1 }}
      transition={{
        type: "spring",
        stiffness: 160,
        damping: 18,
        delay: index * 0.04
      }}
      className={cn("group flex", isUser ? "justify-end" : "justify-start")}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <motion.div
        whileHover={{ scale: 1.01 }}
        className={cn(
          "relative max-w-[82%] rounded-2xl px-4 py-3 shadow-md ring-1 ring-slate-900/5",
          isUser
            ? "rounded-br-sm bg-gradient-to-br from-[#0f3d5e] to-[#0f766e] text-white"
            : "rounded-bl-sm bg-white text-slate-800"
        )}
      >
        <p className="text-[15px] leading-6">{message.body}</p>
        <div
          className={cn(
            "mt-2 flex items-center justify-end gap-1 text-xs",
            isUser ? "text-white/80" : "text-slate-500"
          )}
        >
          <span>{message.pending ? "Sending..." : formatDate(message.createdAt)}</span>
          {isUser ? (
            message.status === "read" ? (
              <CheckCheck className="h-3.5 w-3.5" aria-hidden="true" />
            ) : (
              <Clock3 className="h-3.5 w-3.5" aria-hidden="true" />
            )
          ) : null}
        </div>
        <AnimatePresence>
          {showActions ? (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 6 }}
              className={cn(
                "absolute -bottom-4 flex gap-1 rounded-lg border border-[#d9ccb8] bg-white p-1 shadow-lg",
                isUser ? "right-2" : "left-2"
              )}
            >
              <button
                type="button"
                className="rounded-md p-1.5 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900"
                aria-label="Edit message"
              >
                <Pencil className="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                className="rounded-md p-1.5 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900"
                aria-label="Delete message"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </motion.div>
          ) : null}
        </AnimatePresence>
      </motion.div>
    </motion.article>
  );
}
