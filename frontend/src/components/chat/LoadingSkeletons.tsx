import { motion } from "framer-motion";

/** Shimmer placeholders displayed before message hydration. */
export function LoadingSkeletons(): JSX.Element {
  return (
    <div className="space-y-3">
      {[1, 2, 3].map((item) => (
        <motion.div
          key={item}
          initial={{ opacity: 0.3 }}
          animate={{ opacity: [0.3, 0.9, 0.3] }}
          transition={{ duration: 1.2, repeat: Number.POSITIVE_INFINITY, delay: item * 0.1 }}
          className="h-16 rounded-2xl bg-gradient-to-r from-slate-100 via-slate-50 to-slate-100"
        />
      ))}
    </div>
  );
}
