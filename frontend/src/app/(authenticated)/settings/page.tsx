"use client";

import { useEffect, useState } from "react";
import {
  getTenant,
  updateFunnel,
  getFunnelTemplates,
  type TenantResponse,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { Loader2, Plus, Trash2, Save } from "lucide-react";

interface FunnelTemplate {
  name: string;
  funnel_config: Record<string, string>;
}

export default function SettingsPage() {
  const [tenant, setTenant] = useState<TenantResponse | null>(null);
  const [funnelEntries, setFunnelEntries] = useState<Array<[string, string]>>([]);
  const [templates, setTemplates] = useState<Record<string, FunnelTemplate>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    Promise.all([getTenant(), getFunnelTemplates()])
      .then(([t, tmpl]) => {
        setTenant(t);
        setFunnelEntries(Object.entries(t.funnel_config));
        setTemplates(tmpl);
      })
      .catch(() => toast.error("Erro ao carregar configurações"))
      .finally(() => setLoading(false));
  }, []);

  function addStage() {
    const nextKey = `etapa_${funnelEntries.length + 1}`;
    setFunnelEntries([...funnelEntries, [nextKey, ""]]);
  }

  function removeStage(idx: number) {
    setFunnelEntries(funnelEntries.filter((_, i) => i !== idx));
  }

  function updateStageValue(idx: number, value: string) {
    setFunnelEntries(
      funnelEntries.map((entry, i) => (i === idx ? [entry[0], value] : entry))
    );
  }

  async function handleSave() {
    const config: Record<string, string> = {};
    funnelEntries.forEach(([, value], idx) => {
      config[`etapa_${idx + 1}`] = value;
    });

    setSaving(true);
    try {
      const updated = await updateFunnel(config);
      setTenant(updated);
      setFunnelEntries(Object.entries(updated.funnel_config));
      toast.success("Funil atualizado com sucesso");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao salvar");
    } finally {
      setSaving(false);
    }
  }

  function applyTemplate(key: string) {
    const tmpl = templates[key];
    if (tmpl) {
      setFunnelEntries(Object.entries(tmpl.funnel_config));
      toast.info(`Template "${tmpl.name}" aplicado. Salve para confirmar.`);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold">Configurações</h1>

      {/* Business Info */}
      <Card>
        <CardHeader>
          <CardTitle>Negócio</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm">
            <span className="text-muted-foreground">Nome: </span>
            {tenant?.name}
          </p>
        </CardContent>
      </Card>

      {/* Funnel Config */}
      <Card>
        <CardHeader>
          <CardTitle>Funil de Vendas</CardTitle>
          <CardDescription>
            Configure as etapas do seu funil. A IA usará essas etapas para classificar os leads.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Templates */}
          {Object.keys(templates).length > 0 && (
            <>
              <div>
                <Label className="text-sm text-muted-foreground mb-2 block">
                  Aplicar template:
                </Label>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(templates).map(([key, tmpl]) => (
                    <Button
                      key={key}
                      variant="outline"
                      size="sm"
                      onClick={() => applyTemplate(key)}
                    >
                      {tmpl.name}
                    </Button>
                  ))}
                </div>
              </div>
              <Separator />
            </>
          )}

          {/* Stages */}
          <div className="space-y-3">
            {funnelEntries.map(([, value], idx) => (
              <div key={idx} className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground w-20 shrink-0">
                  Etapa {idx + 1}
                </span>
                <Input
                  value={value}
                  onChange={(e) => updateStageValue(idx, e.target.value)}
                  placeholder={`Nome da etapa ${idx + 1}`}
                />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => removeStage(idx)}
                  disabled={funnelEntries.length <= 1}
                >
                  <Trash2 className="h-4 w-4 text-red-500" />
                </Button>
              </div>
            ))}
          </div>

          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={addStage}>
              <Plus className="mr-2 h-4 w-4" />
              Adicionar Etapa
            </Button>
            <Button size="sm" onClick={handleSave} disabled={saving}>
              {saving ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Save className="mr-2 h-4 w-4" />
              )}
              Salvar Funil
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
