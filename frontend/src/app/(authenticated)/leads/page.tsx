"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  getLeads,
  getTenant,
  analyzeLead,
  analyzeAll,
  updateLeadStatus,
  type LeadListItem,
  type TenantResponse,
  ApiError,
} from "@/lib/api";


import { Button } from "@/components/ui/button";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { TemperatureBadge } from "@/components/ui/temperature-badge";
import { SegmentedTabs } from "@/components/ui/segmented-tabs";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from "@/components/ui/dialog";
import { toast } from "sonner";
import {
  RefreshCw,
  Loader2,
  Thermometer,
  ArrowUpDown,
  CheckCircle2,
  XCircle
} from "lucide-react";


// O componente LeadsPage deve preservar estado e integrações de API; apenas o visual foi atualizado.

export default function LeadsPage() {
  const [leads, setLeads] = useState<LeadListItem[]>([]);
  const [tenant, setTenant] = useState<TenantResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzingAll, setAnalyzingAll] = useState(false);
  const [analyzingIds, setAnalyzingIds] = useState<Set<string>>(new Set());

  // Filters
  const [stageFilter, setStageFilter] = useState<string>("all");
  const [search, setSearch] = useState("");
  const [sortOrder, setSortOrder] = useState<"desc" | "asc">("desc");

  // Status change dialog
  const [statusDialog, setStatusDialog] = useState<{
    lead: LeadListItem;
    action: "converted" | "lost";
  } | null>(null);

  const funnelStages = tenant?.funnel_config
    ? Object.values(tenant.funnel_config)
    : [];

  const refresh = useCallback(async () => {
    try {
      const [l, t] = await Promise.all([
        getLeads({
          stage: stageFilter !== "all" ? stageFilter : undefined,
          sort_by: "temperature_score",
          order: sortOrder,
          page_size: 100,
        }),
        getTenant(),
      ]);
      setLeads(l);
      setTenant(t);
    } catch {
      toast.error("Erro ao carregar leads");
    } finally {
      setLoading(false);
    }
  }, [stageFilter, sortOrder]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
  }, [refresh]);

  async function handleAnalyzeSingle(leadId: string) {
    setAnalyzingIds((prev) => new Set(prev).add(leadId));
    try {
      await analyzeLead(leadId);
      toast.success("Análise concluída");
      await refresh();
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        toast.warning("Lead já está sendo processado");
      } else {
        toast.error(err instanceof Error ? err.message : "Erro ao analisar");
      }
    } finally {
      setAnalyzingIds((prev) => {
        const n = new Set(prev);
        n.delete(leadId);
        return n;
      });
    }
  }

  async function handleAnalyzeAll() {
    setAnalyzingAll(true);
    try {
      const res = await analyzeAll();
      toast.success(
        `${res.succeeded} sucesso, ${res.failed} falhas de ${res.total} leads`
      );
      await refresh();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao analisar leads");
    } finally {
      setAnalyzingAll(false);
    }
  }

  async function confirmStatusChange() {
    if (!statusDialog) return;
    try {
      await updateLeadStatus(statusDialog.lead.id, statusDialog.action);
      toast.success(
        `Lead marcado como ${statusDialog.action === "converted" ? "convertido" : "perdido"}`
      );
      setStatusDialog(null);
      await refresh();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao alterar status");
    }
  }

  const filteredLeads = leads.filter((l) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      l.phone.includes(q) ||
      (l.name && l.name.toLowerCase().includes(q))
    );
  });

  if (loading) {
    return (
      <div className="grid gap-6 py-10 px-4 sm:px-6 lg:px-8 bg-slate-50 dark:bg-[#0B1120] min-h-[100vh] max-w-7xl mx-auto">
        {[...Array(8)].map((_, i) => (
          <div
            key={i}
            className="bg-white dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800/60 rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none p-6 flex flex-col gap-4 animate-pulse"
          >
            <div className="flex flex-row items-center justify-between pb-2">
              <div className="h-4 w-32 rounded bg-slate-200 dark:bg-slate-800" />
              <div className="h-5 w-5 rounded-full bg-slate-200 dark:bg-slate-800" />
            </div>
            <div className="h-6 w-40 rounded bg-slate-200 dark:bg-slate-800" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-8 px-4 sm:px-6 lg:px-8 py-8 bg-slate-50 dark:bg-[#0B1120] min-h-[100vh] max-w-7xl mx-auto">
      <div className="flex items-center justify-between gap-4 mb-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">Leads</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Gerencie a fila com foco nos contatos mais quentes.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={refresh}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Atualizar
          </Button>
          <Button size="sm" onClick={handleAnalyzeAll} disabled={analyzingAll} className="relative flex items-center justify-center min-w-[140px]">
            {analyzingAll ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Thermometer className="mr-2 h-4 w-4" />
            )}
            Analisar Todos
          </Button>
        </div>
      </div>

      <SegmentedTabs
        tabs={[
          { label: "Todos", count: leads.length },
          ...funnelStages.map((s) => ({ label: s, count: leads.filter((l) => l.current_stage === s).length }))
        ]}
        activeTab={stageFilter === "all" ? "Todos" : stageFilter}
        onTabChange={(tab) => setStageFilter(tab === "Todos" ? "all" : tab)}
      />

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-2">
        <Input
          placeholder="Buscar por nome ou telefone..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full sm:w-80"
        />
        <Select value={stageFilter} onValueChange={(v) => v && setStageFilter(v)}>
          <SelectTrigger className="w-full sm:w-48">
            <SelectValue placeholder="Etapa" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas as etapas</SelectItem>
            {funnelStages.map((s) => (
              <SelectItem key={s} value={s}>
                {s}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setSortOrder((o) => (o === "desc" ? "asc" : "desc"))}
        >
          <ArrowUpDown className="mr-2 h-4 w-4" />
          Temperatura {sortOrder === "desc" ? "↓" : "↑"}
        </Button>
      </div>

      {/* Table */}
      <div className="rounded-2xl border border-slate-100 dark:border-slate-800/60 bg-white dark:bg-slate-900/50 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none overflow-x-auto backdrop-blur-sm">
        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50 dark:bg-[#131C2D] hover:bg-slate-50 dark:hover:bg-[#131C2D]">
              <TableHead className="text-slate-700 dark:text-slate-200">Nome / Telefone</TableHead>
              <TableHead className="text-slate-700 dark:text-slate-200">Etapa</TableHead>
              <TableHead className="text-slate-700 dark:text-slate-200">Temperatura</TableHead>
              <TableHead className="text-slate-700 dark:text-slate-200">Tempo de Conversa</TableHead>
              <TableHead className="text-right text-slate-700 dark:text-slate-200">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredLeads.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                  Nenhum lead encontrado
                </TableCell>
              </TableRow>
            ) : (
              filteredLeads.map((lead) => (
                <TableRow key={lead.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/30 transition-colors">
                  <TableCell>
                    <Link
                      href={`/leads/${lead.id}`}
                      className="font-medium text-slate-900 dark:text-slate-50 hover:underline"
                    >
                      {lead.name || lead.phone}
                    </Link>
                    {lead.name && (
                      <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">{lead.phone}</p>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {lead.current_stage || "Sem etapa"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <TemperatureBadge score={lead.temperature_score} />
                  </TableCell>
                  <TableCell>
                    {lead.conversation_time_minutes !== null
                      ? `${Math.round(lead.conversation_time_minutes)} min`
                      : "—"}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Analisar"
                        disabled={lead.is_processing || analyzingIds.has(lead.id)}
                        onClick={() => handleAnalyzeSingle(lead.id)}
                      >
                        {lead.is_processing || analyzingIds.has(lead.id) ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Thermometer className="h-4 w-4" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Marcar como convertido"
                        onClick={() =>
                          setStatusDialog({ lead, action: "converted" })
                        }
                      >
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Marcar como perdido"
                        onClick={() =>
                          setStatusDialog({ lead, action: "lost" })
                        }
                      >
                        <XCircle className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Status Change Dialog */}
      <Dialog
        open={!!statusDialog}
        onOpenChange={(open) => !open && setStatusDialog(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirmar alteração de status</DialogTitle>
            <DialogDescription>
              Deseja marcar o lead{" "}
              <strong>{statusDialog?.lead.name || statusDialog?.lead.phone}</strong>{" "}
              como{" "}
              <strong>
                {statusDialog?.action === "converted" ? "convertido" : "perdido"}
              </strong>
              ? Essa ação encerra o processamento de novas mensagens deste contato.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setStatusDialog(null)}>
              Cancelar
            </Button>
            <Button
              variant={
                statusDialog?.action === "converted" ? "default" : "destructive"
              }
              onClick={confirmStatusChange}
            >
              Confirmar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
