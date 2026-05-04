import { Flame, Thermometer, Snowflake } from "lucide-react"
import { cn } from "@/lib/utils"

interface TemperatureBadgeProps {
  score: number | null
  className?: string
}

export function TemperatureBadge({ score, className }: TemperatureBadgeProps) {
  if (score === null || score === undefined) {
    return (
      <span className={cn("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 text-slate-500 dark:bg-slate-800/50 dark:text-slate-400", className)}>
        —
      </span>
    )
  }
  if (score >= 70) {
    return (
      <span className={cn("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-teal-50 text-teal-700 dark:bg-teal-500/10 dark:text-teal-400", className)}>
        <Flame className="w-3.5 h-3.5" /> Quente ({score})
      </span>
    )
  }
  if (score >= 40) {
    return (
      <span className={cn("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400", className)}>
        <Thermometer className="w-3.5 h-3.5" /> Morno ({score})
      </span>
    )
  }
  return (
    <span className={cn("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 text-slate-600 dark:bg-slate-800/50 dark:text-slate-300", className)}>
      <Snowflake className="w-3.5 h-3.5" /> Frio ({score})
    </span>
  )
}
