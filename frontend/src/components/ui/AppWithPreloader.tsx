"use client";
import { ReactNode } from "react";
import { useAuth } from "@/lib/auth-context";
import Preloader from "@/components/ui/preloader";

export default function AppWithPreloader({ children }: { children: ReactNode }) {
  const { isLoading } = useAuth();
  return (
    <>
      {isLoading && <Preloader />}
      {children}
    </>
  );
}
