import * as React from "react"
import { Input as InputPrimitive } from "@base-ui/react/input"

import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <InputPrimitive
      type={type}
      data-slot="input"
      className={cn(
        "h-9 w-full min-w-0 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900/50 px-3 py-1.5 text-sm text-slate-900 dark:text-slate-50 transition-colors outline-none placeholder:text-slate-400 dark:placeholder:text-slate-500 focus-visible:border-teal-500 focus-visible:ring-2 focus-visible:ring-teal-500/20 dark:focus-visible:ring-teal-500/20 disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-2 aria-invalid:ring-destructive/20 dark:aria-invalid:border-destructive/50 dark:aria-invalid:ring-destructive/40 file:inline-flex file:h-6 file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground",
        className
      )}
      {...props}
    />
  )
}

export { Input }
