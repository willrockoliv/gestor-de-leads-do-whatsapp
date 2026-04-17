// OnboardingGuard: redireciona usuário para onboarding se necessário
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getTenant } from "@/lib/api";

export function useOnboardingGuard() {
  const router = useRouter();
  useEffect(() => {
    getTenant().then((tenant) => {
      // Só redireciona se nunca passou pelo onboarding
      if (
        tenant?.id &&
        !localStorage.getItem(`onboarding_done_${tenant.id}`) &&
        (!tenant.funnel_config || Object.values(tenant.funnel_config).every((v) => !v || v.toLowerCase().includes("etapa")))
      ) {
        router.replace("/onboarding");
      }
    });
  }, [router]);
}
