"use client";

import { useEffect, useState } from "react";
import { getWhatsAppStatus, type WhatsAppStatus } from "@/lib/api";
import { Wifi, WifiOff } from "lucide-react";

export function WhatsAppBanner() {
  const [status, setStatus] = useState<WhatsAppStatus | null>(null);

  useEffect(() => {
    getWhatsAppStatus().then(setStatus).catch(() => {});
    const interval = setInterval(() => {
      getWhatsAppStatus().then(setStatus).catch(() => {});
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  if (!status || status.status === "connected") return null;

  return (
    <div className="flex items-center gap-2 bg-yellow-50 border-b border-yellow-200 px-4 py-2 text-sm text-yellow-800">
      <WifiOff className="h-4 w-4" />
      <span>
        WhatsApp desconectado.{" "}
        {status.message || "Reconecte via QR Code nas configurações."}
      </span>
    </div>
  );
}

export function WhatsAppStatusIndicator() {
  const [status, setStatus] = useState<WhatsAppStatus | null>(null);

  useEffect(() => {
    getWhatsAppStatus().then(setStatus).catch(() => {});
    const interval = setInterval(() => {
      getWhatsAppStatus().then(setStatus).catch(() => {});
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const connected = status?.status === "connected";

  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground">
      {connected ? (
        <Wifi className="h-4 w-4 text-green-500" />
      ) : (
        <WifiOff className="h-4 w-4 text-yellow-500" />
      )}
      <span>{connected ? "Conectado" : "Desconectado"}</span>
    </div>
  );
}
