"use client";

import { useEffect, useState, useCallback, use } from "react";
import { useRouter } from "next/navigation";
import {
  getLead,
  getMessages,
  getTenant,
  analyzeLead,
  updateLeadStatus,
  updateLeadStage,
  type LeadDetail,
  type MessageItem,
  type TenantResponse,
  ApiError,
} from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { TemperatureBadge } from "@/components/ui/temperature-badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import {
  ArrowLeft,
  Loader2,
  Thermometer,
  MessageSquare,
  ExternalLink,
  CheckCircle2,
  XCircle,
  Clock,
} from "lucide-react";

export default function LeadDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const [lead, setLead] = useState<LeadDetail | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [tenant, setTenant] = useState<TenantResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [statusDialog, setStatusDialog] = useState<"converted" | "lost" | null>(null);

  const funnelStages = tenant?.funnel_config
    ? Object.values(tenant.funnel_config)
    : [];

  const refresh = useCallback(async () => {
    try {
      const [l, m, t] = await Promise.all([
        getLead(id),
        getMessages(id, 1, 100),
        getTenant(),
      ]);
      setLead(l);
      setMessages(m.items);
      setTenant(t);
    } catch {
      toast.error("Erro ao carregar lead");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
  }, [refresh]);

  async function handleAnalyze() {
    setAnalyzing(true);
    try {
      const res = await analyzeLead(id);
      setLead((prev) =>
        prev
          ? {
              ...prev,
              analysis_status: res.analysis_status,
              analysis_error: null,
              is_processing: true,
            }
          : prev
      );
      toast.success("Análise enfileirada");
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        toast.warning("Lead já está sendo processado");
      } else {
        toast.error(err instanceof Error ? err.message : "Erro ao analisar");
      }
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleStatusChange() {
    if (!statusDialog) return;
    try {
      await updateLeadStatus(id, statusDialog);
      toast.success(
        `Lead marcado como ${statusDialog === "converted" ? "convertido" : "perdido"}`
      );
      setStatusDialog(null);
      router.push("/leads");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao alterar status");
    }
  }

  async function handleStageChange(stage: string | null) {
    if (!stage) return;
    try {
      await updateLeadStage(id, stage);
      toast.success(`Etapa alterada para "${stage}"`);
      await refresh();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao alterar etapa");
    }
  }

  function handleReply() {
    if (!lead) return;
    const phone = lead.phone.replace(/\D/g, "");
    const text = lead.latest_analysis?.suggested_reply || "";
    window.open(
      `https://wa.me/${phone}?text=${encodeURIComponent(text)}`,
      "_blank"
    );
  }

  if (loading) {
    return (
      <div className="grid gap-4 py-8 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto">
        <div className="bg-white dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800/60 rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none p-8 flex flex-col gap-6 animate-pulse">
          <div className="h-8 w-1/2 rounded bg-slate-100 dark:bg-slate-800 mb-4" />
          <div className="h-6 w-1/3 rounded bg-slate-100 dark:bg-slate-800 mb-2" />
          <div className="h-4 w-1/4 rounded bg-slate-100 dark:bg-slate-800 mb-6" />
          <div className="h-32 w-full rounded bg-slate-100 dark:bg-slate-800 mb-4" />
          <div className="h-10 w-1/2 rounded bg-slate-100 dark:bg-slate-800" />
        </div>
      </div>
    );
  }

  if (!lead) {
    return <p className="text-center text-slate-500 dark:text-slate-400 py-20">Lead não encontrado</p>;
  }

  // Protege campos opcionais e padroniza nomes
  const analysis = lead.latest_analysis ?? null;
  const temperature = lead.temperature_score ?? null;
  const leadName = lead.name || lead.phone || "—";
  const leadPhone = lead.phone || "—";
  const leadStatus = lead.status || "ativo";
  const leadStage = lead.current_stage || "";
  const conversationTime =
    typeof lead.conversation_time_minutes === "number"
      ? `${Math.round(lead.conversation_time_minutes)} min`
      : "—";
  const createdAt = lead.created_at
    ? new Date(lead.created_at).toLocaleDateString("pt-BR")
    : "—";

  return (
    <div className="space-y-6 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6 bg-slate-50 dark:bg-[#0B1120] min-h-[100vh]">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">{leadName}</h1>
          {lead.name && <p className="text-slate-500 dark:text-slate-400 font-mono">{leadPhone}</p>}
        </div>
        <TemperatureBadge score={temperature} />
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-2">
        <Button
          size="sm"
          onClick={handleAnalyze}
          disabled={
            analyzing ||
            lead.analysis_status === "pending" ||
            lead.analysis_status === "processing" ||
            lead.is_processing
          }
        >
          {analyzing || lead.analysis_status === "pending" || lead.analysis_status === "processing" || lead.is_processing ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Thermometer className="mr-2 h-4 w-4" />
          )}
          Atualizar Análise
        </Button>
        <Button size="sm" variant="outline" onClick={handleReply}>
          <MessageSquare className="mr-2 h-4 w-4" />
          Responder
          <ExternalLink className="ml-1 h-3 w-3" />
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => setStatusDialog("converted")}
        >
          <CheckCircle2 className="mr-2 h-4 w-4 text-green-500" />
          Convertido
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => setStatusDialog("lost")}
        >
          <XCircle className="mr-2 h-4 w-4 text-red-500" />
          Perdido
        </Button>
      </div>

      {/* Lead Info + Stage Override */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Informações</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Status</span>
              <Badge variant={leadStatus === "converted" ? "default" : leadStatus === "lost" ? "outline" : "default"} className={leadStatus === "converted" ? "bg-teal-50 text-teal-700 dark:bg-teal-500/10 dark:text-teal-400" : leadStatus === "lost" ? "bg-slate-100 text-slate-700 dark:bg-slate-800/50 dark:text-slate-300" : "bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400"}>
                {leadStatus === "converted" ? "Convertido" : leadStatus === "lost" ? "Perdido" : "Ativo"}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Etapa do Funil</span>
              <Select
                value={leadStage}
                onValueChange={handleStageChange}
              >
                <SelectTrigger className="w-44 h-8 text-xs">
                  <SelectValue placeholder="Selecionar etapa" />
                </SelectTrigger>
                <SelectContent>
                  {funnelStages.map((s) => (
                    <SelectItem key={s} value={s}>
                      {s}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Tempo de Conversa</span>
              <div className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                <span>
                  {conversationTime}
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Status da Análise</span>
              <Badge variant="outline">{lead.analysis_status}</Badge>
            </div>
            {lead.analysis_status === "failed" && lead.analysis_error ? (
              <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-900/70 dark:bg-red-900/20 dark:text-red-300">
                {lead.analysis_error}
              </div>
            ) : null}
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Criado em</span>
              <span>{createdAt}</span>
            </div>
          </CardContent>
        </Card>

        {/* Analysis Summary */}
        {analysis ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Resumo da IA</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <p>{analysis.conversation_summary}</p>
              <Separator />
              <div>
                <p className="text-teal-600 dark:text-teal-400 font-medium mb-1">Dicas Qualitativas</p>
                <p>{analysis.qualitative_tips}</p>
              </div>
              <Separator />
              <div>
                <p className="text-slate-500 dark:text-slate-400 font-medium mb-1">Resposta Sugerida</p>
                <p className="bg-slate-900 dark:bg-[#0B1120] text-slate-200 dark:text-slate-300 rounded-xl p-3 text-xs italic border border-slate-800 dark:border-slate-800/80">{analysis.suggested_reply}</p>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Última análise: {new Date(analysis.created_at).toLocaleString("pt-BR")}
              </p>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Resumo da IA</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Nenhuma análise realizada. Clique em &quot;Atualizar Análise&quot; para gerar.
              </p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Messages */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <MessageSquare className="h-4 w-4" />
            Histórico de Mensagens ({messages.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {messages.length === 0 ? (
            <p className="text-sm text-slate-500 dark:text-slate-400 text-center py-4">
              Nenhuma mensagem registrada
            </p>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${
                    msg.direction === "outbound" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
                      msg.direction === "outbound"
                        ? "bg-slate-900 dark:bg-teal-600 text-white"
                        : "bg-slate-100 dark:bg-slate-800/60 text-slate-800 dark:text-slate-200"
                    }`}
                  >
                    <p className="whitespace-pre-wrap break-words">{msg.content}</p>
                    <p
                      className={`text-xs mt-1 ${
                        msg.direction === "outbound"
                          ? "text-white/70"
                          : "text-slate-500 dark:text-slate-400"
                      }`}
                    >
                      {new Date(msg.timestamp).toLocaleString("pt-BR")}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Status Dialog */}
      <Dialog
        open={!!statusDialog}
        onOpenChange={(open) => !open && setStatusDialog(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirmar alteração de status</DialogTitle>
            <DialogDescription>
              Deseja marcar o lead{" "}
              <strong>{leadName}</strong> como{" "}
              <strong>
                {statusDialog === "converted" ? "convertido" : "perdido"}
              </strong>
              ? Essa ação encerra o processamento de novas mensagens.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setStatusDialog(null)}>
              Cancelar
            </Button>
            <Button
              variant={statusDialog === "converted" ? "default" : "destructive"}
              onClick={handleStatusChange}
            >
              Confirmar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
