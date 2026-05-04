import type { Metadata } from "next";

import { Toaster } from "@/components/ui/sonner";
import { AuthProvider } from "@/lib/auth-context";
import AppWithPreloader from "@/components/ui/AppWithPreloader";
import { ThemeProvider } from "@/components/theme-provider";
import "./globals.css";


export const metadata: Metadata = {
  title: "Gestor de Leads do WhatsApp",
  description: "Gerencie e priorize seus leads do WhatsApp com inteligência artificial",
};




export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <body className="min-h-full flex flex-col h-full antialiased">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <AuthProvider>
            <AppWithPreloader>
              {children}
            </AppWithPreloader>
            <Toaster richColors position="top-right" />
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
