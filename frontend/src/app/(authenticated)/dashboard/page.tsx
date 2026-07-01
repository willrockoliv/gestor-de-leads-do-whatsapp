"use client";

import { useEffect, useState, useCallback, useMemo, useRef } from "react";

import Link from "next/link";
import {
  getDashboardStats,
  getLeads,
  getLead,
  getTenant,
  analyzeAll,
  getAnalyzeStatus,
  getLeadAnalyzeStatus,
  type AnalysisStatus,
  type DashboardStats,
  type LeadListItem,
  type LeadDetail,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import {
  Users,
  CheckCircle2,
  Thermometer,
  RefreshCw,
  Loader2,
  MessageCircle,
  Clock,
  LayoutList,
  X,
  Sparkles,
  ArrowRight,
  AlertCircle,
  Send,
  Flame,
} from "lucide-react";
import { useOnboardingGuard } from "../onboarding/guard";
import { TemperatureBadge } from "@/components/ui/temperature-badge";
import { SegmentedTabs } from "@/components/ui/segmented-tabs";

export default function DashboardPage() {
  useOnboardingGuard();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [leads, setLeads] = useState<LeadListItem[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [showAnalyzeAllStatus, setShowAnalyzeAllStatus] = useState(false);
  const [analyzeAllRequestedTotal, setAnalyzeAllRequestedTotal] = useState(0);
  const [analyzeAllTrackedIds, setAnalyzeAllTrackedIds] = useState<Set<string>>(new Set());
  const [globalAnalyzeCounts, setGlobalAnalyzeCounts] = useState({
    pending: 0,
    processing: 0,
    completed: 0,
    failed: 0,
  });
  const [funnelStages, setFunnelStages] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [trackedPollingIds, setTrackedPollingIds] = useState<Set<string>>(new Set());
  const [pollAllStatuses, setPollAllStatuses] = useState(false);
  const failedNotifiedIdsRef = useRef<Set<string>>(new Set());
  // Sliding panel UI state
  const [selectedLeadId, setSelectedLeadId] = useState<string | null>(null);
  const [selectedLeadDetail, setSelectedLeadDetail] = useState<LeadDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [activeStage, setActiveStage] = useState<string>("Todos");

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [statsData, leadsData, tenantData] = await Promise.all([
        getDashboardStats(),
        getLeads(),
        getTenant(),
      ]);
      setStats(statsData);
      setLeads(leadsData);
      // Etapas do funil
      const stages = tenantData?.funnel_config ? Object.values(tenantData.funnel_config) : [];
      setFunnelStages(stages);
    } catch {
      toast.error("Erro ao carregar dados do dashboard");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
  }, [refresh]);

  const handleAnalyzeAll = async () => {
    setAnalyzing(true);
    try {
      const res = await analyzeAll();
      setShowAnalyzeAllStatus(true);
      setAnalyzeAllRequestedTotal(res.total_enqueued);
      if (res.total_enqueued === 0) {
        setAnalyzeAllTrackedIds(new Set());
      }
      if (res.total_enqueued > 0) {
        if ((res.lead_ids ?? []).length === 0) {
          setAnalyzeAllTrackedIds(new Set());
          setPollAllStatuses(true);
        } else {
          setAnalyzeAllTrackedIds(new Set(res.lead_ids ?? []));
          setTrackedPollingIds((prev) => {
            const next = new Set(prev);
            (res.lead_ids ?? []).forEach((id) => next.add(id));
            return next;
          });
        }
        const enqueuedIds = new Set(res.lead_ids ?? []);
        setLeads((prev) =>
          prev.map((lead) =>
            enqueuedIds.size === 0 || enqueuedIds.has(lead.id)
              ? {
                  ...lead,
                  analysis_status: "pending",
                  analysis_error: null,
                  is_processing: true,
                }
              : lead
          )
        );
      }
      toast.success(`${res.total_enqueued} lead(s) enfileirado(s) para análise`);
    } catch {
      toast.error("Erro ao analisar todos os leads");
    } finally {
      setAnalyzing(false);
    }
  };

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

        setGlobalAnalyzeCounts({
          pending: status.counts.pending,
          processing: status.counts.processing,
          completed: status.counts.completed,
          failed: status.counts.failed,
        });

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
              is_processing: false,
            };
          })
        );

        const newFailedIds = failedIds.filter(
          (id) => !failedNotifiedIdsRef.current.has(id)
        );
        if (newFailedIds.length > 0) {
          const failedDetails = await Promise.all(
            newFailedIds.map(async (leadId) => {
              try {
                return await getLeadAnalyzeStatus(leadId);
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

  // Fetch lead detail when selected
  useEffect(() => {
    if (!selectedLeadId) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSelectedLeadDetail(null);
      return;
    }
    setLoadingDetail(true);
    getLead(selectedLeadId)
      .then(setSelectedLeadDetail)
      .catch(() => toast.error("Erro ao carregar detalhes do lead"))
      .finally(() => setLoadingDetail(false));
  }, [selectedLeadId]);

  // Filter leads by active stage, sorted by temperature
  const filteredLeads = useMemo(() => {
    let filtered = leads;
    if (activeStage !== "Todos") {
      filtered = leads.filter((l) => l.current_stage === activeStage);
    }
    return filtered.sort((a, b) => (b.temperature_score ?? 0) - (a.temperature_score ?? 0));
  }, [leads, activeStage]);

  // Close panel if selected lead disappears after filter
  useEffect(() => {
    if (selectedLeadId && !filteredLeads.find((l) => l.id === selectedLeadId)) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSelectedLeadId(null);
    }
  }, [filteredLeads, selectedLeadId]);

  // Segmented tabs data
  const stageTabs = useMemo(() => {
    const tabs = [{ label: "Todos", count: leads.length }];
    funnelStages.forEach((s) => {
      tabs.push({ label: s, count: leads.filter((l) => l.current_stage === s).length });
    });
    return tabs;
  }, [leads, funnelStages]);

  const easeTransition = "transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)]";

  const hasOngoingAnalysis = useMemo(
    () =>
      leads.some(
        (lead) =>
          lead.analysis_status === "pending" ||
          lead.analysis_status === "processing" ||
          lead.is_processing
      ),
    [leads]
  );

  const analyzeAllStatus = useMemo(() => {
    if (!showAnalyzeAllStatus && !hasOngoingAnalysis) {
      return null;
    }

    if (analyzeAllTrackedIds.size > 0) {
      const trackedLeads = leads.filter((lead) => analyzeAllTrackedIds.has(lead.id));
      const pending = trackedLeads.filter(
        (lead) =>
          lead.analysis_status === "pending" ||
          lead.analysis_status === "processing" ||
          lead.is_processing
      ).length;
      const success = trackedLeads.filter((lead) => lead.analysis_status === "completed").length;
      const failed = trackedLeads.filter((lead) => lead.analysis_status === "failed").length;
      const total = Math.max(analyzeAllRequestedTotal, trackedLeads.length);

      return { pending, success, failed, total };
    }

    const pending = globalAnalyzeCounts.pending + globalAnalyzeCounts.processing;
    const success = globalAnalyzeCounts.completed;
    const failed = globalAnalyzeCounts.failed;
    const total = Math.max(analyzeAllRequestedTotal, pending + success + failed);

    return { pending, success, failed, total };
  }, [
    analyzeAllRequestedTotal,
    analyzeAllTrackedIds,
    hasOngoingAnalysis,
    globalAnalyzeCounts,
    leads,
    showAnalyzeAllStatus,
  ]);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0B1120]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">
              Caixa de Entrada
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Gerencie e priorize seus leads com inteligência.
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={refresh} disabled={loading || analyzing}>
              {loading ? <Loader2 className="animate-spin h-4 w-4" /> : <RefreshCw className="h-4 w-4" />}
              Atualizar
            </Button>
            <Button size="sm" onClick={handleAnalyzeAll} disabled={analyzing}>
              {analyzing ? <Loader2 className="animate-spin h-4 w-4" /> : <Thermometer className="h-4 w-4" />}
              {analyzing ? "Analisando..." : "Analisar Todos"}
            </Button>
          </div>
        </div>

        {analyzeAllStatus ? (
          <div className="rounded-xl border border-slate-200 dark:border-slate-800/60 bg-white dark:bg-slate-900/50 px-4 py-3 shadow-[0_6px_20px_rgb(0,0,0,0.04)] dark:shadow-none">
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <p className="font-medium text-slate-700 dark:text-slate-200">
                Status da análise em lote
              </p>
              <span className="inline-flex items-center rounded-full border border-blue-200 bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700 dark:border-blue-500/40 dark:bg-blue-500/10 dark:text-blue-300">
                Pendente: {analyzeAllStatus.pending}
              </span>
              <span className="inline-flex items-center rounded-full border border-green-200 bg-green-50 px-2 py-0.5 text-xs font-medium text-green-700 dark:border-green-500/40 dark:bg-green-500/10 dark:text-green-300">
                Sucesso: {analyzeAllStatus.success}
              </span>
              <span className="inline-flex items-center rounded-full border border-red-200 bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-300">
                Falha: {analyzeAllStatus.failed}
              </span>
              <span className="text-slate-500 dark:text-slate-400">
                Total: {analyzeAllStatus.total}
              </span>
            </div>
          </div>
        ) : null}

        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {loading
            ? Array.from({ length: 4 }).map((_, i) => (
                <div
                  key={i}
                  className="bg-white dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-100 dark:border-slate-800/60 animate-pulse"
                >
                  <div className="h-4 w-28 bg-slate-200 dark:bg-slate-800 rounded mb-4" />
                  <div className="h-8 w-16 bg-slate-200 dark:bg-slate-800 rounded" />
                </div>
              ))
            : stats && (
                <>
                  <div className="bg-white dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-100 dark:border-slate-800/60 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none backdrop-blur-sm">
                    <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-4">
                      <span className="text-sm font-medium">Leads Ativos</span>
                      <Users className="w-4 h-4" />
                    </div>
                    <span className="text-3xl font-semibold text-slate-900 dark:text-slate-50">{stats.total_active}</span>
                  </div>
                  <div className="bg-white dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-100 dark:border-slate-800/60 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none backdrop-blur-sm">
                    <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-4">
                      <span className="text-sm font-medium">Prioridade Alta</span>
                      <Flame className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                    </div>
                    <span className="text-3xl font-semibold text-slate-900 dark:text-slate-50">
                      {leads.filter((l) => (l.temperature_score ?? 0) >= 70).length}
                    </span>
                  </div>
                  <div className="bg-white dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-100 dark:border-slate-800/60 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none backdrop-blur-sm">
                    <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-4">
                      <span className="text-sm font-medium">Convertidos</span>
                      <CheckCircle2 className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                    </div>
                    <span className="text-3xl font-semibold text-slate-900 dark:text-slate-50">{stats.total_converted}</span>
                  </div>
                  <div className="bg-white dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-100 dark:border-slate-800/60 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none backdrop-blur-sm">
                    <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-4">
                      <span className="text-sm font-medium">Temperatura Média</span>
                      <Thermometer className="w-4 h-4" />
                    </div>
                    <span className="text-3xl font-semibold text-slate-900 dark:text-slate-50">
                      {stats.avg_temperature !== null ? stats.avg_temperature : "—"}
                    </span>
                  </div>
                </>
              )}
        </div>

        {/* Sliding Master-Detail Layout */}
        <div className="flex flex-col lg:flex-row items-start w-full relative">

          {/* LEFT PANEL: Leads List */}
          <div
            className={`${easeTransition} flex flex-col gap-4 flex-shrink-0 ${
              selectedLeadId ? "w-full lg:w-[42%] lg:pr-6" : "w-full"
            }`}
          >
            <SegmentedTabs
              tabs={stageTabs}
              activeTab={activeStage}
              onTabChange={setActiveStage}
            />

            <div className="flex flex-col gap-3 mt-1">
              {loading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <div
                    key={i}
                    className="bg-white/60 dark:bg-slate-900/40 rounded-2xl border border-slate-200 dark:border-slate-800/60 p-5 animate-pulse"
                  >
                    <div className="h-4 w-32 bg-slate-200 dark:bg-slate-800 rounded mb-3" />
                    <div className="h-3 w-24 bg-slate-200 dark:bg-slate-800 rounded" />
                  </div>
                ))
              ) : filteredLeads.length > 0 ? (
                filteredLeads.map((lead) => (
                  <button
                    key={lead.id}
                    onClick={() =>
                      setSelectedLeadId(selectedLeadId === lead.id ? null : lead.id)
                    }
                    className={`text-left p-5 rounded-2xl border transition-all duration-300 transform origin-top ${
                      selectedLeadId === lead.id
                        ? "bg-white dark:bg-slate-900 border-teal-500/40 dark:border-teal-500/40 shadow-md ring-1 ring-teal-500/10 dark:ring-teal-500/20"
                        : "bg-white/60 dark:bg-slate-900/40 border-slate-200 dark:border-slate-800/60 hover:border-slate-300 dark:hover:border-slate-700 shadow-sm hover:shadow dark:hover:bg-slate-900/80"
                    }`}
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3
                          className={`font-semibold transition-colors ${
                            selectedLeadId === lead.id
                              ? "text-teal-700 dark:text-teal-400"
                              : "text-slate-900 dark:text-slate-50"
                          }`}
                        >
                          {lead.name || lead.phone}
                        </h3>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 font-mono">
                          {lead.phone}
                        </p>
                      </div>
                      <TemperatureBadge score={lead.temperature_score} />
                    </div>
                    <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 pt-3 border-t border-slate-100 dark:border-slate-800/60">
                      <span
                        className={`flex items-center gap-1.5 px-2 py-1 rounded-md font-medium transition-colors ${
                          selectedLeadId === lead.id
                            ? "bg-teal-50 dark:bg-teal-500/10 text-teal-700 dark:text-teal-400"
                            : "bg-slate-100 dark:bg-slate-800/50 text-slate-600 dark:text-slate-400"
                        }`}
                      >
                        <LayoutList className="w-3.5 h-3.5 opacity-70" />
                        {lead.current_stage ?? "Sem etapa"}
                      </span>
                      {lead.conversation_time_minutes !== null && (
                        <span className="flex items-center gap-1.5 font-medium">
                          <Clock className="w-3.5 h-3.5" />
                          {Math.round(lead.conversation_time_minutes)} min
                        </span>
                      )}
                      {(lead.analysis_status === "pending" || lead.analysis_status === "processing" || lead.is_processing) && (
                        <span className="flex items-center gap-1.5 text-blue-500">
                          <Loader2 className="w-3.5 h-3.5 animate-spin" /> Processando
                        </span>
                      )}
                      {lead.analysis_status === "failed" && (
                        <span className="flex items-center gap-1.5 text-red-500">
                          <AlertCircle className="w-3.5 h-3.5" /> Falhou
                        </span>
                      )}
                    </div>
                  </button>
                ))
              ) : (
                <div className="text-center py-16 px-4 border border-dashed border-slate-300 dark:border-slate-800 rounded-2xl bg-white/30 dark:bg-slate-900/20">
                  <LayoutList className="w-10 h-10 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
                  <p className="text-slate-500 dark:text-slate-400 font-medium">Nenhum lead nesta etapa.</p>
                </div>
              )}
            </div>
          </div>

          {/* RIGHT PANEL: Lead Details (Slides in) */}
          <div
            className={`${easeTransition} min-w-0 overflow-hidden lg:pl-2 ${
              selectedLeadId
                ? "w-full lg:w-[58%] opacity-100 max-h-[3000px] mt-6 lg:mt-0"
                : "w-0 opacity-0 max-h-0 lg:max-h-[3000px] m-0 p-0"
            }`}
          >
            <div className="w-full max-w-full lg:max-w-[700px] xl:max-w-[800px] pb-8">
              {selectedLeadDetail && (
                <div className="bg-white dark:bg-slate-900/95 rounded-2xl border border-slate-200 dark:border-slate-800/80 shadow-xl dark:shadow-[0_8px_30px_rgb(0,0,0,0.2)] overflow-hidden flex flex-col">

                  {/* Detail Header */}
                  <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-900/50">
                    <div>
                      <h2 className="text-xl font-bold text-slate-900 dark:text-slate-50 tracking-tight">
                        {selectedLeadDetail.name || selectedLeadDetail.phone}
                      </h2>
                      <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 font-mono">
                        {selectedLeadDetail.phone}
                      </p>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right hidden sm:block">
                        <p className="text-[10px] text-slate-400 uppercase tracking-wider font-bold mb-1">Score</p>
                        <TemperatureBadge score={selectedLeadDetail.temperature_score} />
                      </div>
                      <div className="flex items-center gap-2 border-l border-slate-200 dark:border-slate-700 pl-4">
                        <Link
                          href={`/leads/${selectedLeadDetail.id}`}
                          className="p-2 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-800 hover:shadow-sm transition-all"
                          title="Ver página completa"
                        >
                          <ArrowRight className="w-4 h-4" />
                        </Link>
                        <button
                          onClick={() => setSelectedLeadId(null)}
                          className="p-2 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                          title="Fechar detalhes"
                        >
                          <X className="w-5 h-5" />
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Detail Content */}
                  <div className="p-6 md:p-8 flex flex-col gap-6 relative">
                    {loadingDetail && (
                      <div className="absolute inset-0 z-10 bg-white/70 dark:bg-[#0B1120]/60 backdrop-blur-sm flex items-center justify-center rounded-2xl">
                        <div className="flex flex-col items-center gap-4 bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-xl border border-slate-100 dark:border-slate-700">
                          <Loader2 className="w-8 h-8 animate-spin text-teal-600 dark:text-teal-400" />
                          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Carregando análise...</span>
                        </div>
                      </div>
                    )}

                    {selectedLeadDetail.latest_analysis ? (
                      <>
                        <div className="space-y-2">
                          <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 flex items-center gap-2 uppercase tracking-widest">
                            <MessageCircle className="w-4 h-4" /> Resumo da Conversa
                          </h3>
                          <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed bg-slate-50 dark:bg-slate-800/30 p-5 rounded-xl border border-slate-100 dark:border-slate-800/50 shadow-sm">
                            {selectedLeadDetail.latest_analysis.conversation_summary}
                          </p>
                        </div>

                        <div className="space-y-2">
                          <h3 className="text-xs font-bold text-teal-600 dark:text-teal-400 flex items-center gap-2 uppercase tracking-widest">
                            <Sparkles className="w-4 h-4" /> Dica Estratégica
                          </h3>
                          <div className="flex items-start gap-3 bg-teal-50/80 dark:bg-teal-900/20 p-5 rounded-xl border border-teal-100 dark:border-teal-500/20 shadow-sm">
                            <AlertCircle className="w-5 h-5 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
                            <p className="text-teal-900 dark:text-teal-100 text-sm leading-relaxed">
                              {selectedLeadDetail.latest_analysis.qualitative_tips}
                            </p>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 flex items-center gap-2 uppercase tracking-widest">
                            <Send className="w-4 h-4" /> Sugestão de Resposta
                          </h3>
                          <div className="bg-slate-900 dark:bg-[#0B1120] p-5 rounded-xl border border-slate-800 dark:border-slate-800/80 shadow-inner">
                            <p className="text-slate-200 dark:text-slate-300 text-sm leading-relaxed font-medium italic">
                              &quot;{selectedLeadDetail.latest_analysis.suggested_reply}&quot;
                            </p>
                          </div>
                        </div>
                      </>
                    ) : (
                      <div className="text-center py-10">
                        <Sparkles className="w-10 h-10 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
                        <p className="text-slate-500 dark:text-slate-400 font-medium text-sm">
                          Nenhuma análise disponível ainda.
                        </p>
                        <p className="text-slate-400 dark:text-slate-500 text-xs mt-1">
                          Use &quot;Analisar Todos&quot; para gerar insights com IA.
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Action Footer */}
                  <div className="p-6 bg-slate-50 dark:bg-slate-900/50 border-t border-slate-100 dark:border-slate-800 flex justify-end">
                    <Link
                      href={`/leads/${selectedLeadDetail.id}`}
                      className="inline-flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white dark:bg-teal-600 dark:hover:bg-teal-500 dark:text-white px-6 py-3 rounded-xl text-sm font-semibold shadow-sm transition-all hover:shadow-md hover:-translate-y-0.5"
                    >
                      Ver Lead Completo <ArrowRight className="w-4 h-4" />
                    </Link>
                  </div>

                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
