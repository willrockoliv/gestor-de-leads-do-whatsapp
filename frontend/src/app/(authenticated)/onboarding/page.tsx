"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getFunnelTemplates, updateFunnel, getTenant } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";

interface FunnelTemplate {
  name: string;
  funnel_config: Record<string, string>;
}

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [templates, setTemplates] = useState<Record<string, FunnelTemplate>>({});
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [tenant, setTenant] = useState<any>(null);

  useEffect(() => {
    Promise.all([getFunnelTemplates(), getTenant()])
      .then(([tmpl, t]) => {
        setTemplates(tmpl);
        setTenant(t);
      })
      .catch(() => toast.error("Erro ao carregar onboarding"))
      .finally(() => setLoading(false));
  }, []);

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
      if (typeof tmpl === "object" && tmpl !== null && "funnel_config" in tmpl) {
        funnelConfig = tmpl.funnel_config;
      } else if (typeof tmpl === "object" && tmpl !== null) {
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
    } catch (err) {
      toast.error("Erro ao aplicar template");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <div className="p-8 text-center">Carregando...</div>;
  }

  // Etapa 0: Boas-vindas
  if (step === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
        <Card className="w-full max-w-lg">
          <CardHeader>
            <CardTitle>Bem-vindo(a) ao Gestor de Leads!</CardTitle>
            <CardDescription>
              Antes de começar, personalize seu funil de vendas. Você pode escolher um template pronto ou configurar depois.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <Button onClick={() => setStep(1)} className="w-full">Escolher Template</Button>
            <Button
              variant="outline"
              onClick={() => {
                if (tenant?.id) {
                  localStorage.setItem(`onboarding_done_${tenant.id}`, "1");
                }
                router.push("/dashboard");
              }}
            >
              Configurar depois
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Etapa 1: Seleção de template
  if (step === 1) {
    // Suporte para resposta do backend como Record<string, string> ou Record<string, { name, funnel_config }>
    const templateEntries = Object.entries(templates);
    return (
      <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
        <Card className="w-full max-w-lg">
          <CardHeader>
            <CardTitle>Escolha um Template de Funil</CardTitle>
            <CardDescription>Veja as etapas de cada template antes de aplicar.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-4">
              {templateEntries.length === 0 && (
                <div className="text-center text-muted-foreground">Nenhum template disponível.</div>
              )}
              {templateEntries.map(([key, tmpl]) => {
                // Suporte para formato antigo (direto) e novo (objeto)
                let name = key;
                let funnelConfig: Record<string, string> | undefined = undefined;
                if (typeof tmpl === "object" && tmpl !== null && "funnel_config" in tmpl) {
                  name = tmpl.name || key;
                  funnelConfig = tmpl.funnel_config;
                } else if (typeof tmpl === "object" && tmpl !== null) {
                  funnelConfig = tmpl;
                }
                return (
                  <div key={key} className={`border rounded p-4 cursor-pointer ${selected === key ? 'border-primary bg-muted' : 'border-muted-foreground'}`} onClick={() => handleSelectTemplate(key)}>
                    <div className="font-semibold mb-2">{name}</div>
                    <ol className="list-decimal ml-6 text-sm text-muted-foreground">
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
              <Button onClick={() => setStep(0)} variant="outline">Voltar</Button>
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
