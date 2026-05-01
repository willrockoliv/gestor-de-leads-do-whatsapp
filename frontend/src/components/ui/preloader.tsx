import { Loader2Icon } from "lucide-react";

export function Preloader() {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-50 dark:bg-slate-950 transition-colors duration-300"
      aria-busy="true"
      aria-label="Carregando aplicação"
    >
      <div className="flex flex-col items-center gap-4">
        <Loader2Icon className="w-12 h-12 text-slate-800 dark:text-slate-100 animate-spin" />
        <span className="text-slate-500 dark:text-slate-400 text-lg font-medium tracking-wide select-none">
          Carregando...
        </span>
      </div>
    </div>
  );
}

export default Preloader;
