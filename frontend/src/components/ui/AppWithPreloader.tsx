"use client";
import { ReactNode } from "react";

export default function AppWithPreloader({ children }: { children: ReactNode }) {
  // Avoid SSR/CSR markup divergence from global overlays during hydration.
  return <>{children}</>;
}
