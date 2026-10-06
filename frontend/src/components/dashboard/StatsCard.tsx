import { ReactNode } from "react";
import { motion } from "framer-motion";

interface Props {
  title: string;
  value: string | number;
  icon: ReactNode;
}

export default function StatsCard({
  title,
  value,
  icon,
}: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      whileHover={{ y: -6, scale: 1.01 }}
      className="rounded-[24px] border border-white/10 bg-slate-900/70 p-5 shadow-[0_20px_45px_rgba(15,23,42,0.25)]"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-400">{title}</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-white">
            {value}
          </h2>
        </div>

        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500/20 to-violet-500/20 text-indigo-200 ring-1 ring-inset ring-indigo-400/30">
          {icon}
        </div>
      </div>
    </motion.div>
  );
}