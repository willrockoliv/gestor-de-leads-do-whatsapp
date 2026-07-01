"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import {
  getLeads,
  getTenant,
  analyzeLead,
  analyzeAll,
  getAnalyzeStatus,
  getLeadAnalyzeStatus,
  updateLeadStatus,
  type AnalysisStatus,
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
  const [trackedPollingIds, setTrackedPollingIds] = useState<Set<string>>(new Set());
  const [pollAllStatuses, setPollAllStatuses] = useState(false);
  const failedNotifiedIdsRef = useRef<Set<string>>(new Set());

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

  useEffect(() => {
    const leadIdsInProgress = leads
      .filter(
        (lead) =>
          lead.analysis_status === "pending" ||
          lead.analysis_status === "processing" ||
          lead.is_processing
      )
      .map((lead) => lead.id);

    if (
      !pollAllStatuses &&
      trackedPollingIds.size === 0 &&
      leadIdsInProgress.length === 0
    ) {
      return;
    }

    let isCancelled = false;

    async function runPollingCycle() {
      try {
        const idsToTrack = Array.from(
          new Set([...trackedPollingIds, ...leadIdsInProgress])
        );
        const status = await getAnalyzeStatus(pollAllStatuses ? undefined : idsToTrack);
        if (isCancelled) {
          return;
        }

        const pendingIds = status.pending_ids ?? [];
        const processingIds = status.processing_ids ?? [];
        const completedIds = status.completed_ids ?? [];
        const failedIds = status.failed_ids ?? [];

        const statusById = new Map<string, AnalysisStatus>();
        pendingIds.forEach((id) => statusById.set(id, "pending"));
        processingIds.forEach((id) => statusById.set(id, "processing"));
        completedIds.forEach((id) => statusById.set(id, "completed"));
        failedIds.forEach((id) => statusById.set(id, "failed"));

        setLeads((prev) =>
          prev.map((lead) => {
            const nextStatus = statusById.get(lead.id);
            if (!nextStatus) {
              return lead;
            }

            if (nextStatus === lead.analysis_status && !lead.is_processing) {
              return lead;
            }

            if (nextStatus === "pending" || nextStatus === "processing") {
              return {
                ...lead,
                analysis_status: nextStatus,
                analysis_error: null,
                is_processing: true,
              };
            }

            return {
              ...lead,
              analysis_status: nextStatus,
              analysis_error: nextStatus === "completed" ? null : lead.analysis_error,
              is_processing: false,
            };
          })
        );

        if (failedIds.length > 0) {
          const failedDetails = await Promise.all(
            failedIds
              .filter((id) => !failedNotifiedIdsRef.current.has(id))
              .map(async (id) => {
                try {
                  const detail = await getLeadAnalyzeStatus(id);
                  return detail;
                } catch {
                  return null;
                }
              })
          );

          if (!isCancelled) {
            failedDetails.forEach((detail) => {
              if (!detail) {
                return;
              }
              failedNotifiedIdsRef.current.add(detail.lead_id);
              setLeads((prev) =>
                prev.map((lead) =>
                  lead.id === detail.lead_id
                    ? {
                        ...lead,
                        analysis_status: detail.analysis_status,
                        analysis_error: detail.analysis_error,
                        is_processing: false,
                      }
                    : lead
                )
              );
              toast.error(`Falha na análise de um lead${detail.analysis_error ? `: ${detail.analysis_error}` : ""}`);
            });
          }
        }

        const inProgressIds = new Set<string>([
          ...pendingIds,
          ...processingIds,
        ]);

        if (pollAllStatuses && inProgressIds.size === 0) {
          setPollAllStatuses(false);
        }

        if (!pollAllStatuses) {
          setTrackedPollingIds((prev) => {
            const next = new Set<string>();
            prev.forEach((id) => {
              if (inProgressIds.has(id)) {
                next.add(id);
              }
            });
            return next;
          });
        }
      } catch {
        if (!isCancelled) {
          toast.error("Erro ao consultar status de análise");
        }
      }
    }

    runPollingCycle();
    const intervalId = window.setInterval(runPollingCycle, 4000);

    return () => {
      isCancelled = true;
      window.clearInterval(intervalId);
    };
  }, [leads, pollAllStatuses, trackedPollingIds]);

  async function handleAnalyzeSingle(leadId: string) {
    setAnalyzingIds((prev) => new Set(prev).add(leadId));
    try {
      const res = await analyzeLead(leadId);
      setTrackedPollingIds((prev) => new Set(prev).add(leadId));
      setLeads((prev) =>
        prev.map((lead) =>
          lead.id === leadId
            ? {
                ...lead,
                analysis_status: res.analysis_status,
                analysis_error: null,
                is_processing: true,
              }
            : lead
        )
      );
      toast.success("Análise enfileirada");
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
      if (res.total_enqueued > 0) {
        if ((res.lead_ids ?? []).length === 0) {
          setPollAllStatuses(true);
        } else {
          setTrackedPollingIds((prev) => {
            const next = new Set(prev);
            (res.lead_ids ?? []).forEach((id) => next.add(id));
            return next;
          });
        }
      }
      if (res.total_enqueued > 0) {
        setLeads((prev) => {
          const enqueuedIds = new Set(res.lead_ids ?? []);
          return prev.map((lead) =>
            enqueuedIds.size === 0 || enqueuedIds.has(lead.id)
              ? {
                  ...lead,
                  analysis_status: "pending",
                  analysis_error: null,
                  is_processing: true,
                }
              : lead
          );
        });
      }
      toast.success(`${res.total_enqueued} lead(s) enfileirado(s) para análise`);
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
                    {lead.analysis_status === "pending" || lead.analysis_status === "processing" ? (
                      <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">Análise em andamento</p>
                    ) : null}
                    {lead.analysis_status === "completed" ? (
                      <p className="text-xs text-green-600 dark:text-green-400 mt-1">Análise concluída</p>
                    ) : null}
                    {lead.analysis_status === "failed" && lead.analysis_error ? (
                      <p className="text-xs text-red-600 dark:text-red-400 mt-1 line-clamp-2">{lead.analysis_error}</p>
                    ) : null}
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
                        disabled={
                          lead.analysis_status === "pending" ||
                          lead.analysis_status === "processing" ||
                          lead.is_processing ||
                          analyzingIds.has(lead.id)
                        }
                        onClick={() => handleAnalyzeSingle(lead.id)}
                      >
                        {lead.analysis_status === "pending" || lead.analysis_status === "processing" || lead.is_processing || analyzingIds.has(lead.id) ? (
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
