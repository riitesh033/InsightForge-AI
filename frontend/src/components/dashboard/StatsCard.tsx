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
      initial={{
        opacity: 0,
        y: 20,
      }}
      animate={{
        opacity: 1,
        y: 0,
      }}
      transition={{
        duration: 0.4,
      }}
      whileHover={{
        y: -5,
        scale: 1.02,
      }}
      className="rounded-2xl border bg-card p-6 shadow-sm"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">
            {title}
          </p>

          <h2 className="mt-2 text-3xl font-bold">
            {value}
          </h2>
        </div>

        <div className="rounded-xl bg-primary/10 p-3">
          {icon}
        </div>
      </div>
    </motion.div>
  );
}