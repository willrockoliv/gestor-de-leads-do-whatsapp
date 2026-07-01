"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Image from "next/image";
import {
  connectWhatsApp,
  getWhatsAppQRCode,
  getWhatsAppStatus,
  type WhatsAppStatus,
} from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, RefreshCw, Smartphone, Wifi, WifiOff } from "lucide-react";
import { toast } from "sonner";

interface WhatsAppConnectionCardProps {
  title?: string;
  description?: string;
  autoConnect?: boolean;
  hideActionButtons?: boolean;
  hideQrRefreshButton?: boolean;
}

export default function WhatsAppConnectionCard({
  title = "Conecte seu WhatsApp",
  description = "Conecte seu número para começar a receber e classificar os leads automaticamente.",
  autoConnect = false,
  hideActionButtons = false,
  hideQrRefreshButton = false,
}: WhatsAppConnectionCardProps) {
  const [status, setStatus] = useState<WhatsAppStatus | null>(null);
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [loadingQr, setLoadingQr] = useState(false);

  const qrCodeSrc = useMemo(() => {
    if (!qrCode) return null;
    return qrCode.startsWith("data:image") ? qrCode : `data:image/png;base64,${qrCode}`;
  }, [qrCode]);

  const fetchStatus = useCallback(async () => {
    try {
      const currentStatus = await getWhatsAppStatus();
      setStatus(currentStatus);
      if (currentStatus.status === "connected") {
        setQrCode(null);
      }
    } catch {
      toast.error("Não foi possível consultar o status do WhatsApp");
    } finally {
      setLoadingStatus(false);
    }
  }, []);

  const fetchQrCode = useCallback(async () => {
    setLoadingQr(true);
    try {
      const qrResponse = await getWhatsAppQRCode();
      if (qrResponse.qr_code) {
        setQrCode(qrResponse.qr_code);
      }
      if (qrResponse.phone) {
        setStatus((prev) => ({
          status: "connected",
          connected_since: prev?.connected_since ?? null,
          phone: qrResponse.phone,
        }));
      }
    } catch {
      toast.error("Não foi possível carregar o QR Code");
    } finally {
      setLoadingQr(false);
    }
  }, []);

  const handleConnect = useCallback(async () => {
    setConnecting(true);
    try {
      await connectWhatsApp();
      await fetchStatus();
      await fetchQrCode();
      toast.success("Sessão iniciada. Escaneie o QR Code para conectar.");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Erro ao iniciar conexão do WhatsApp");
    } finally {
      setConnecting(false);
    }
  }, [fetchQrCode, fetchStatus]);

  useEffect(() => {
    const initialTimeout = window.setTimeout(() => {
      void fetchStatus();
    }, 0);

    const intervalId = window.setInterval(() => {
      void fetchStatus();
    }, 15000);

    return () => {
      window.clearTimeout(initialTimeout);
      window.clearInterval(intervalId);
    };
  }, [fetchStatus]);

  useEffect(() => {
    if (!autoConnect || loadingStatus || status?.status === "connected") {
      return;
    }

    const connectTimeout = window.setTimeout(() => {
      void handleConnect();
    }, 0);

    return () => {
      window.clearTimeout(connectTimeout);
    };
  }, [autoConnect, handleConnect, loadingStatus, status?.status]);

  async function handleRefreshQr() {
    await fetchStatus();
    await fetchQrCode();
  }

  const isConnected = status?.status === "connected";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Smartphone className="h-5 w-5" />
          {title}
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {loadingStatus ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Carregando status da conexão...
          </div>
        ) : (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            {isConnected ? (
              <Wifi className="h-4 w-4 text-green-500" />
            ) : (
              <WifiOff className="h-4 w-4 text-yellow-500" />
            )}
            <span>
              {isConnected
                ? `WhatsApp conectado${status?.phone ? ` (${status.phone})` : ""}`
                : "WhatsApp ainda não conectado"}
            </span>
          </div>
        )}

        {!isConnected && qrCodeSrc ? (
          <div className="space-y-3 rounded-xl border border-slate-200 dark:border-slate-800 p-4">
            <p className="text-sm text-slate-700 dark:text-slate-300">
              Escaneie o QR Code com o WhatsApp no seu celular.
            </p>
            <div className="mx-auto w-full max-w-[240px] rounded-md bg-white p-3">
              <Image
                src={qrCodeSrc}
                alt="QR Code para conectar WhatsApp"
                width={240}
                height={240}
                className="h-full w-full"
                unoptimized
              />
            </div>
            {!hideQrRefreshButton ? (
              <Button variant="outline" size="sm" onClick={handleRefreshQr} disabled={loadingQr}>
                {loadingQr ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="mr-2 h-4 w-4" />
                )}
                Atualizar QR Code
              </Button>
            ) : null}
          </div>
        ) : null}

        {!hideActionButtons ? (
          <div className="flex flex-wrap gap-2">
            <Button onClick={handleConnect} disabled={connecting}>
              {connecting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              {isConnected ? "Reconectar WhatsApp" : "Conectar WhatsApp"}
            </Button>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
