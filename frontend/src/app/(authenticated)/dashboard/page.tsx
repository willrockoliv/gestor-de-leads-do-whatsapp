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

function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) return <Badge variant="outline">—</Badge>;
  if (score >= 70) return <Badge className="bg-red-500 hover:bg-red-600">{score}</Badge>;
  if (score >= 40) return <Badge className="bg-yellow-500 hover:bg-yellow-600">{score}</Badge>;
  return <Badge className="bg-blue-500 hover:bg-blue-600">{score}</Badge>;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [leads, setLeads] = useState<LeadListItem[]>([]);
  const [tenant, setTenant] = useState<TenantResponse | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const [s, l, t] = await Promise.all([
        getDashboardStats(),
        getLeads({ page_size: 100 }),
        getTenant(),
      ]);
      setStats(s);
      setLeads(l);
      setTenant(t);
    } catch {
      toast.error("Erro ao carregar dados do dashboard");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleAnalyzeAll() {
    setAnalyzing(true);
    try {
      const res = await analyzeAll();
      toast.success(
        `Análise concluída: ${res.succeeded} sucesso, ${res.failed} falhas de ${res.total} total`
      );
      await refresh();
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(err.message);
      } else {
        toast.error("Erro ao analisar leads");
      }
    } finally {
      setAnalyzing(false);
    }
  }

  // Build funnel stages from tenant config
  const funnelStages: string[] = tenant?.funnel_config
    ? Object.values(tenant.funnel_config)
    : [];

  // Group leads by stage for kanban
  const leadsByStage: Record<string, LeadListItem[]> = {};
  for (const stage of funnelStages) {
    leadsByStage[stage] = [];
  }
  leadsByStage["Sem etapa"] = [];
  for (const lead of leads) {
    const stage = lead.current_stage || "Sem etapa";
    if (!leadsByStage[stage]) leadsByStage[stage] = [];
    leadsByStage[stage].push(lead);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

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
          <Button size="sm" onClick={handleAnalyzeAll} disabled={analyzing}>
            {analyzing ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Thermometer className="mr-2 h-4 w-4" />
            )}
            Analisar Todos
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
          {Object.entries(leadsByStage).map(([stage, stageLeads]) => (
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
                  .sort((a, b) => (b.temperature_score ?? 0) - (a.temperature_score ?? 0))
                  .map((lead) => (
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
          ))}
        </div>
      </div>
    </div>
  );
}
