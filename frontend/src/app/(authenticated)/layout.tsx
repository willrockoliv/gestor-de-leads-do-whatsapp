"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { WhatsAppBanner, WhatsAppStatusIndicator } from "@/components/whatsapp-banner";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  LayoutDashboard,
  Users,
  Settings,
  LogOut,
  Sun,
  Moon,
} from "lucide-react";
import ThemeToggle from "@/components/theme-toggle";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/leads", label: "Leads", icon: Users },
  { href: "/settings", label: "Configurações", icon: Settings },
];

export default function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-muted-foreground">Carregando...</p>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="hidden w-64 flex-col border-r bg-slate-50 dark:bg-slate-950 border-slate-100 dark:border-slate-800 md:flex rounded-r-2xl shadow-sm">
        <div className="flex h-14 items-center border-b border-slate-100 dark:border-slate-800 px-4 justify-between">
          <Link href="/dashboard" className="font-semibold text-lg text-slate-900 dark:text-slate-50">
            📱 Gestor de Leads
          </Link>
          <ThemeToggle />
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {navItems.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground ${
                pathname === href || pathname.startsWith(href + "/")
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground"
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}
        </nav>
        <div className="border-t p-3 space-y-3">
          <WhatsAppStatusIndicator />
          <Separator />
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground truncate">{user.email}</span>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => {
                logout();
                router.push("/login");
              }}
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </aside>
          {/* Main content */}
          <div className="flex flex-1 flex-col">
            {/* Mobile header */}
            <header className="flex h-14 items-center justify-between border-b px-4 md:hidden">
              <Link href="/dashboard" className="font-semibold">
                📱 Gestor de Leads
              </Link>
              <nav className="flex items-center gap-2">
                {navItems.map(({ href, icon: Icon }) => (
                  <Link
                    key={href}
                    href={href}
                    className={`rounded-md p-2 ${
                      pathname === href || pathname.startsWith(href + "/")
                        ? "bg-accent"
                        : ""
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                  </Link>
                ))}
                <ThemeToggle />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => {
                    logout();
                    router.push("/login");
                  }}
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              </nav>
            </header>
            <WhatsAppBanner />
            <main className="flex-1 overflow-auto p-4 md:p-6">{children}</main>
          </div>
        </div>
      );
    }
