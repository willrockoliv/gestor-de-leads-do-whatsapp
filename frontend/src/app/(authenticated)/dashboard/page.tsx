"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  getDashboardStats,
  getLeads,
  getTenant,
  analyzeAll,
  type DashboardStats,
  type LeadListItem,
  type TenantResponse,
  ApiError,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import {
  Users,
  CheckCircle2,
  XCircle,
  Thermometer,
  RefreshCw,
  Loader2,
} from "lucide-react";
import { useOnboardingGuard } from "../onboarding/guard";

function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) return <Badge variant="outline">—</Badge>;
  if (score >= 70) return <Badge variant="default">Quente</Badge>; // "success" não existe
  if (score >= 40) return <Badge variant="outline">Morno</Badge>; // "warning" não existe
  return <Badge variant="secondary">Frio</Badge>;
}

export default function DashboardPage() {
  useOnboardingGuard();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [leads, setLeads] = useState<LeadListItem[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [leadsByStage, setLeadsByStage] = useState<Record<string, LeadListItem[]>>({});
  const [funnelStages, setFunnelStages] = useState<string[]>([]);

  const refresh = useCallback(async () => {
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
      // Agrupa leads por etapa
      const grouped: Record<string, LeadListItem[]> = {};
      for (const l of leadsData) {
        const stageKey = l.current_stage ?? "Sem etapa";
        if (!grouped[stageKey]) grouped[stageKey] = [];
        grouped[stageKey].push(l);
      }
      // Garante todas as etapas do funil como colunas, mesmo vazias
      for (const stage of stages) {
        if (!grouped[stage]) grouped[stage] = [];
      }
      setLeadsByStage(grouped);
    } catch (err) {
      toast.error("Erro ao carregar dados do dashboard");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleAnalyzeAll = async () => {
    setAnalyzing(true);
    try {
      await analyzeAll();
      toast.success("Análise concluída!");
      await refresh();
    } catch (err) {
      toast.error("Erro ao analisar todos os leads");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title + Actions */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={refresh}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Atualizar
          </Button>
          <Button
            size="sm"
            onClick={handleAnalyzeAll}
            disabled={analyzing}
            className="relative flex items-center justify-center min-w-[140px] bg-slate-800 text-white dark:bg-slate-100 dark:text-slate-900 hover:bg-slate-700 dark:hover:bg-slate-200 focus-visible:ring-2 focus-visible:ring-slate-400 dark:focus-visible:ring-slate-600"
          >
            {analyzing ? (
              <span className="absolute left-4 flex items-center">
                <Loader2 className="h-4 w-4 animate-spin text-slate-300 dark:text-slate-500" />
              </span>
            ) : (
              <span className="absolute left-4 flex items-center">
                <Thermometer className="h-4 w-4 text-slate-200 dark:text-slate-700" />
              </span>
            )}
            <span className={analyzing ? "opacity-60" : ""}>Analisar Todos</span>
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Leads Ativos</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_active}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Convertidos</CardTitle>
              <CheckCircle2 className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_converted}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Perdidos</CardTitle>
              <XCircle className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_lost}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Temperatura Média</CardTitle>
              <Thermometer className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats.avg_temperature !== null ? stats.avg_temperature : "—"}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Kanban */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Funil de Vendas</h2>
        <div className="flex gap-4 overflow-x-auto pb-4">
          {funnelStages.map((stage) => {
            const stageLeads = leadsByStage[stage] || [];
            return (
              <div
                key={stage}
                className="flex-shrink-0 w-72 rounded-lg border bg-muted/30"
              >
                <div className="flex items-center justify-between border-b px-3 py-2">
                  <h3 className="text-sm font-semibold">{stage}</h3>
                  <Badge variant="secondary">{stageLeads.length}</Badge>
                </div>
                <div className="space-y-2 p-2 max-h-[60vh] overflow-y-auto">
                  {stageLeads
                    .sort((a: LeadListItem, b: LeadListItem) => (b.temperature_score ?? 0) - (a.temperature_score ?? 0))
                    .map((lead: LeadListItem) => (
                      <Link key={lead.id} href={`/leads/${lead.id}`}>
                        <Card className="cursor-pointer transition-shadow hover:shadow-md">
                          <CardContent className="p-3 space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-medium text-sm truncate">
                                {lead.name || lead.phone}
                              </span>
                              <ScoreBadge score={lead.temperature_score} />
                            </div>
                            <p className="text-xs text-muted-foreground">{lead.phone}</p>
                            {lead.is_processing && (
                              <div className="flex items-center gap-1 text-xs text-blue-500">
                                <Loader2 className="h-3 w-3 animate-spin" />
                                Processando...
                              </div>
                            )}
                            {lead.conversation_time_minutes !== null && (
                              <p className="text-xs text-muted-foreground">
                                ⏱ {Math.round(lead.conversation_time_minutes)} min de conversa
                              </p>
                            )}
                          </CardContent>
                        </Card>
                      </Link>
                    ))}
                  {stageLeads.length === 0 && (
                    <p className="text-xs text-muted-foreground text-center py-4">
                      Nenhum lead nesta etapa
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
