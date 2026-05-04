import { cn } from "@/lib/utils"

interface TabItem {
  label: string
  count?: number
}

interface SegmentedTabsProps {
  tabs: TabItem[]
  activeTab: string
  onTabChange: (tab: string) => void
  className?: string
}

export function SegmentedTabs({ tabs, activeTab, onTabChange, className }: SegmentedTabsProps) {
  return (
    <div
      className={cn(
        "bg-slate-200/60 dark:bg-[#131C2D] rounded-xl p-1.5 flex overflow-x-auto hide-scrollbar gap-1",
        "border border-slate-200/50 dark:border-slate-800/50 shadow-inner",
        className
      )}
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.label
        return (
          <button
            key={tab.label}
            onClick={() => onTabChange(tab.label)}
            className={cn(
              "relative flex-1 min-w-[100px] flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium",
              "transition-all duration-300 ease-out whitespace-nowrap",
              isActive
                ? "bg-white dark:bg-[#1E293B] text-slate-900 dark:text-slate-50 shadow-sm ring-1 ring-slate-900/5 dark:ring-white/5"
                : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-200/50 dark:hover:bg-slate-800/30"
            )}
          >
            {tab.label}
            {tab.count !== undefined && (
              <span
                className={cn(
                  "px-1.5 py-0.5 rounded-md text-xs",
                  isActive
                    ? "bg-slate-100 dark:bg-slate-700/50 text-slate-600 dark:text-slate-300"
                    : "bg-slate-200/50 dark:bg-slate-800/40 text-slate-400 dark:text-slate-500"
                )}
              >
                {tab.count}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
