import { motion } from "framer-motion";

/** Three-dot bouncing typing animation for live assistant feedback. */
export function TypingIndicator(): JSX.Element {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      className="inline-flex w-fit items-center gap-2 rounded-2xl rounded-bl-sm bg-white px-4 py-3 shadow-sm ring-1 ring-slate-900/5"
    >
      {[0, 1, 2].map((dot) => (
        <motion.span
          key={dot}
          animate={{ y: [0, -5, 0] }}
          transition={{ duration: 0.7, repeat: Number.POSITIVE_INFINITY, delay: dot * 0.12 }}
          className="h-2.5 w-2.5 rounded-full bg-[#0f766e]/60"
        />
      ))}
      <span className="ml-2 text-xs font-semibold text-slate-500">Kayktb...</span>
    </motion.div>
  );
}
