import { motion } from "framer-motion";
import { CheckCircle2, Clock3 } from "lucide-react";
import { cn } from "../../lib/utils";

interface ProgressStep {
  title: string;
  description: string;
  completed: boolean;
}

interface ProgressTimelineProps {
  steps: ProgressStep[];
}

/** Animated timeline for case progress states in sidebar. */
export function ProgressTimeline({ steps }: ProgressTimelineProps): JSX.Element {
  return (
    <motion.ol
      initial="hidden"
      animate="show"
      variants={{
        hidden: { opacity: 0 },
        show: { opacity: 1, transition: { staggerChildren: 0.12 } }
      }}
      className="space-y-3"
    >
      {steps.map((step) => (
        <motion.li
          key={step.title}
          variants={{ hidden: { opacity: 0, x: -12 }, show: { opacity: 1, x: 0 } }}
          className="flex gap-3 rounded-lg bg-[#fff8ef] p-3"
        >
          <motion.span
            animate={step.completed ? { scale: [0.8, 1.06, 1] } : { scale: [1, 1.05, 1] }}
            transition={{ duration: 0.55 }}
            className={cn(
              "mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-full",
              step.completed ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"
            )}
          >
            {step.completed ? (
              <CheckCircle2 className="h-4.5 w-4.5" />
            ) : (
              <Clock3 className="h-4.5 w-4.5 animate-pulse" />
            )}
          </motion.span>
          <div>
            <p className="text-sm font-bold text-slate-800">{step.title}</p>
            <p className="text-xs text-slate-500">{step.description}</p>
          </div>
        </motion.li>
      ))}
    </motion.ol>
  );
}
