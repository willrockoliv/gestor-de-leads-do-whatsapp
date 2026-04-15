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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import {
  ArrowLeft,
  Thermometer,
  Loader2,
  MessageSquare,
  CheckCircle2,
  XCircle,
  Clock,
  ExternalLink,
} from "lucide-react";

function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) return <Badge variant="outline">—</Badge>;
  if (score >= 70)
    return <Badge className="bg-red-500 hover:bg-red-600 text-lg px-3 py-1">{score}</Badge>;
  if (score >= 40)
    return <Badge className="bg-yellow-500 hover:bg-yellow-600 text-lg px-3 py-1">{score}</Badge>;
  return <Badge className="bg-blue-500 hover:bg-blue-600 text-lg px-3 py-1">{score}</Badge>;
}

export default function LeadDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
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
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!lead) {
    return <p className="text-center text-muted-foreground py-20">Lead não encontrado</p>;
  }

  const analysis = lead.latest_analysis;

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">{lead.name || lead.phone}</h1>
          {lead.name && <p className="text-muted-foreground">{lead.phone}</p>}
        </div>
        <ScoreBadge score={lead.temperature_score} />
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
              <Badge variant="outline">{lead.status}</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Etapa do Funil</span>
              <Select
                value={lead.current_stage || ""}
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
                  {lead.conversation_time_minutes !== null
                    ? `${Math.round(lead.conversation_time_minutes)} min`
                    : "—"}
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Criado em</span>
              <span>{new Date(lead.created_at).toLocaleDateString("pt-BR")}</span>
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
              <strong>{lead.name || lead.phone}</strong> como{" "}
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
