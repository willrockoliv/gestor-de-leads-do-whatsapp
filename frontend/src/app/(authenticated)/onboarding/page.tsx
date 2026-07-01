"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getFunnelTemplates, updateFunnel, getTenant, type TenantResponse, type FunnelTemplateMap } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import WhatsAppConnectionCard from "@/components/whatsapp-connection-card";
import { toast } from "sonner";

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [templates, setTemplates] = useState<FunnelTemplateMap>({});
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [tenant, setTenant] = useState<TenantResponse | null>(null);

  useEffect(() => {
    Promise.all([getFunnelTemplates(), getTenant()])
      .then(([tmpl, t]) => {
        setTemplates(tmpl);
        setTenant(t);
      })
      .catch(() => toast.error("Erro ao carregar onboarding"))
      .finally(() => setLoading(false));
  }, []);

  function isNamedTemplate(
    value: unknown
  ): value is { name: string; funnel_config: Record<string, string> } {
    if (!value || typeof value !== "object") return false;
    const candidate = value as { name?: unknown; funnel_config?: unknown };
    return (
      typeof candidate.name === "string" &&
      !!candidate.funnel_config &&
      typeof candidate.funnel_config === "object" &&
      !Array.isArray(candidate.funnel_config)
    );
  }

  function isStageMap(value: unknown): value is Record<string, string> {
    if (!value || typeof value !== "object" || Array.isArray(value)) return false;
    return Object.values(value).every((item) => typeof item === "string");
  }

  function handleSelectTemplate(key: string) {
    setSelected(key);
  }

  async function handleApplyTemplate() {
    if (!selected) return;
    setSaving(true);
    try {
      // Suporte para ambos formatos de template
      let funnelConfig: Record<string, string> | undefined = undefined;
      const tmpl = templates[selected];
      if (isNamedTemplate(tmpl)) {
        funnelConfig = tmpl.funnel_config;
      } else if (isStageMap(tmpl)) {
        funnelConfig = tmpl;
      }
      if (!funnelConfig) {
        toast.error("Template inválido");
        setSaving(false);
        return;
      }
      await updateFunnel(funnelConfig);
      toast.success("Template aplicado!");
      if (tenant?.id) {
        localStorage.setItem(`onboarding_done_${tenant.id}`, "1");
      }
      router.push("/dashboard");
    } catch {
      toast.error("Erro ao aplicar template");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <div className="p-8 text-center text-slate-500 dark:text-slate-400">Carregando...</div>;
  }

  // Etapa 0: Boas-vindas
  if (step === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-[#0B1120] p-4">
        <Card className="w-full max-w-lg">
          <CardHeader>
            <CardTitle className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">Bem-vindo(a) ao Gestor de Leads!</CardTitle>
            <CardDescription>
              Antes de começar, conecte seu WhatsApp e personalize seu funil de vendas.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <Button onClick={() => setStep(1)} className="w-full">Começar onboarding</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Etapa 1: Conexão com WhatsApp
  if (step === 1) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-[#0B1120] p-4">
        <div className="w-full max-w-2xl space-y-4">
          <WhatsAppConnectionCard
            autoConnect
            hideActionButtons
            hideQrRefreshButton
            description="Estamos gerando seu QR Code automaticamente. Escaneie com o WhatsApp no celular ou siga para o próximo passo para configurar o funil."
          />
          <div className="flex gap-2">
            <Button onClick={() => setStep(0)} variant="outline">Voltar</Button>
            <Button onClick={() => setStep(2)}>Continuar para funil</Button>
          </div>
        </div>
      </div>
    );
  }

  // Etapa 2: Seleção de template
  if (step === 2) {
    // Suporte para resposta do backend como Record<string, string> ou Record<string, { name, funnel_config }>
    const templateEntries = Object.entries(templates);
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-[#0B1120] p-4">
        <Card className="w-full max-w-lg">
          <CardHeader>
            <CardTitle className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">Escolha um Template de Funil</CardTitle>
            <CardDescription>Veja as etapas de cada template antes de aplicar.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-4">
              {templateEntries.length === 0 && (
                <div className="text-center text-slate-500 dark:text-slate-400">Nenhum template disponível.</div>
              )}
              {templateEntries.map(([key, tmpl]) => {
                // Suporte para formato antigo (direto) e novo (objeto)
                let name = key;
                let funnelConfig: Record<string, string> | undefined = undefined;
                if (isNamedTemplate(tmpl)) {
                  name = tmpl.name || key;
                  funnelConfig = tmpl.funnel_config;
                } else if (isStageMap(tmpl)) {
                  funnelConfig = tmpl;
                }
                return (
                  <div
                    key={key}
                    className={`rounded-2xl p-4 cursor-pointer transition-all border ${
                      selected === key
                        ? "bg-white dark:bg-slate-900 border-teal-500/40 dark:border-teal-500/40 shadow-md ring-1 ring-teal-500/10 dark:ring-teal-500/20"
                        : "bg-white/60 dark:bg-slate-900/40 border-slate-200 dark:border-slate-800/60 hover:border-slate-300 dark:hover:border-slate-700 shadow-sm"
                    }`}
                    onClick={() => handleSelectTemplate(key)}
                  >
                    <div className="font-semibold mb-2 text-slate-900 dark:text-slate-50">{name}</div>
                    <ol className="list-decimal ml-6 text-sm text-slate-500 dark:text-slate-400">
                      {funnelConfig ? Object.values(funnelConfig).map((etapa, idx) => (
                        <li key={idx}>{etapa}</li>
                      )) : <li>Configuração de etapas não encontrada</li>}
                    </ol>
                  </div>
                );
              })}
            </div>
            <Separator className="my-4" />
            <div className="flex gap-2">
              <Button onClick={() => setStep(1)} variant="outline">Voltar</Button>
              <Button onClick={handleApplyTemplate} disabled={!selected || saving}>
                {saving ? "Aplicando..." : "Aplicar e Começar"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return null;
}
