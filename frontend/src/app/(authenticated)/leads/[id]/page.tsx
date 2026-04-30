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
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
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

function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) return <Badge variant="outline">—</Badge>;
  if (score >= 70)
    return <Badge variant="default" className="bg-teal-50 text-teal-700 dark:bg-teal-500/10 dark:text-teal-400 text-lg">{score}</Badge>;
  if (score >= 40)
    return <Badge variant="default" className="bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400 text-lg">{score}</Badge>;
  return <Badge variant="outline" className="text-lg">{score}</Badge>;
}

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
    refresh();
  }, [refresh]);

  async function handleAnalyze() {
    setAnalyzing(true);
    try {
      await analyzeLead(id);
      toast.success("Análise concluída");
      await refresh();
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
      <div className="grid gap-4 py-8">
        <div className="bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl shadow-sm p-8 flex flex-col gap-6 animate-pulse max-w-2xl mx-auto">
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
    return <p className="text-center text-muted-foreground py-20">Lead não encontrado</p>;
  }

  // Protege campos opcionais e padroniza nomes
  const analysis = lead.latest_analysis ?? null;
  const temperature = lead.temperature_score ?? lead.temperature ?? null;
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
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">{leadName}</h1>
          {lead.name && <p className="text-muted-foreground">{leadPhone}</p>}
        </div>
        <ScoreBadge score={temperature} />
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-2">
        <Button
          size="sm"
          onClick={handleAnalyze}
          disabled={analyzing || lead.is_processing}
        >
          {analyzing || lead.is_processing ? (
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
              <Badge variant={leadStatus === "converted" ? "default" : leadStatus === "lost" ? "outline" : "default"} className={leadStatus === "converted" ? "bg-teal-50 text-teal-700 dark:bg-teal-500/10 dark:text-teal-400" : leadStatus === "lost" ? undefined : "bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400"}>
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
                <p className="text-muted-foreground font-medium mb-1">Dicas Qualitativas</p>
                <p>{analysis.qualitative_tips}</p>
              </div>
              <Separator />
              <div>
                <p className="text-muted-foreground font-medium mb-1">Resposta Sugerida</p>
                <p className="bg-muted rounded-md p-2 text-xs">{analysis.suggested_reply}</p>
              </div>
              <p className="text-xs text-muted-foreground">
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
              <p className="text-sm text-muted-foreground">
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
            <p className="text-sm text-muted-foreground text-center py-4">
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
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted"
                    }`}
                  >
                    <p className="whitespace-pre-wrap break-words">{msg.content}</p>
                    <p
                      className={`text-xs mt-1 ${
                        msg.direction === "outbound"
                          ? "text-primary-foreground/70"
                          : "text-muted-foreground"
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
