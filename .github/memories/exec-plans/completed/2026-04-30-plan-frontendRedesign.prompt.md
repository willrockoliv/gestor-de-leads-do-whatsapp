# Plan: Frontend Redesign — Nordic Minimalist Design System

### TL;DR
Refatorar **todas as 7 páginas** do frontend Next.js aplicando o design system "Nordic Minimalist" do prototype lead-dashboard. Refatoração é **100% visual** — nenhuma lógica de negócio ou estado será alterada. Estruturado em 5 fases: setup, componentes base, 3 páginas autenticadas, páginas de auth, validação.

> **Fonte da verdade:** `.prompts/redesign-frontend/lead-dashboard/src/App.jsx`
> Toda decisão visual deve ser extraída e justificada a partir deste arquivo.

> **Atualização contínua:** Este plano deve ser atualizado à medida que cada fase ou item for implementado — marque itens concluídos com ✅, registre desvios ou decisões tomadas durante a implementação e ajuste etapas futuras se necessário.

---

### Steps

#### **FASE 1: Setup do Design System & Infraestrutura** ✅

1. **Estender Tailwind config** (`frontend/tailwind.config.ts`)
   - Adicionar cores: `#0B1120` (navy), Slate completo, Teal/Blue acentos
   - Easing customizado: `cubic-bezier(0.23,1,0.32,1)` para smooth transitions
   - Variações de opacity: `/10`, `/20`, `/30`, `/50`, `/80`, `/95`

2. **Criar componentes design-system** em `frontend/src/components/ui/`:
   - `temperature-badge.tsx` — Icon + cor baseado em valor (🔥/🌡️/❄️)
   - `kpi-card.tsx` — Container com rounded-2xl, shadow, dark mode
   - `lead-item-card.tsx` — Estados unselected/selected/processing
   - `detail-panel.tsx` — Wrapper para painel deslizante
   - `segmented-tabs.tsx` — Tabs customizadas com segmented control style
   - `frosted-header.tsx` — Sticky header com backdrop-blur

3. **Atualizar globals.css** — Remover conflicts, adicionar utilities se necessário

---

#### **FASE 2: Refatorar Componentes Base** *(paralelo com Fase 1)* ✅

Modernizar 8 componentes shadcn/ui existentes:
- **badge.tsx** — Cores (teal/blue/slate), icons suportados
- **button.tsx** — Hover lift effect (`-translate-y-0.5`), teal primary
- **card.tsx** — KPI pattern (rounded-2xl, shadow, dark:bg-slate-900/50)
- **tabs.tsx** → **segmented-tabs** — Novo style com inset shadow
- **input.tsx** — Borders, focus states
- **select.tsx** — Paleta + focus states
- **table.tsx** — Header bg, row hover, borders

---

#### **FASE 3: Refatorar Páginas Autenticadas** ✅ (Dashboard, Leads, Lead Details, Onboarding, Settings)

**3a. Dashboard** — ⭐ Foco principal
- KPI cards modernas com trending badges
- **Sliding Master-Detail**: Left panel (42% desktop, 100% mobile) + Right panel (58% desktop, desliza de fora)
- Segmented tabs para filtrar por stage
- Lead list cards com visual de seleção (border teal, ring, shadow)

**3b. Leads**
- Sticky frosted header
- Segmented tabs + search
- Table modernizada com hover states
- Click para abrir detail panel

**3c. Lead Details** `[id]/`
- Panel deslizante com lead full info
- Summary + AI Tip + Suggested Reply boxes
- Action buttons (teal primary, slate secondary)

**3d. Onboarding**
- Wizard layout com KPI cards
- Template selection com segmented control
- Smooth transitions entre steps

**3e. Settings**
- Seções em cards modernos
- Inline editing com smooth transitions
- Form styling consistente

---

#### **FASE 4: Refatorar Páginas de Autenticação** ✅ (Login, Register)

- **Login** — Card centered, form modernizado, teal CTA
- **Register** — Same pattern + extra fields (business name)
- **Home** — Simples redirect (sem update visual necessário)

---

#### **FASE 5: Validação & Polish** ✅ concluída

1. Audit completo light/dark mode (colors, spacing, shadows, animations)
2. Consolidar protocolo de validação manual no Integrated Browser e logs via Docker Compose
3. Performance check: Lighthouse, animation frame rates (60fps target)
4. Verificar contrast ratios (WCAG AAA)

### Progress Log

- ✅ Adicionado utilitário `hide-scrollbar` em `frontend/src/app/globals.css`.
- ✅ Criados componentes novos: `temperature-badge.tsx` e `segmented-tabs.tsx`.
- ✅ Atualizados componentes base: `button.tsx`, `card.tsx`, `input.tsx`.
- ✅ Implementado padrão **Sliding Master-Detail** no `dashboard/page.tsx` com transição `duration-500 ease-[cubic-bezier(0.23,1,0.32,1)]`.
- ✅ Refatoradas telas autenticadas para o visual Nordic Minimalist: Dashboard, Leads, Lead Details, Settings e Onboarding.
- ✅ Refatoradas telas de autenticação: Login e Register.
- ✅ Testes E2E Playwright antigos removidos por decisão de produto; suíte frontend automatizada descontinuada por ora.
- ✅ Validação obrigatória no Integrated Browser executada nas telas alteradas, com credenciais padrão (`teste@teste.com` / `123456`) e conferência de logs do frontend.
- ✅ `docker compose exec frontend npm run lint` validado com `EXIT_CODE:0`.
- ✅ `docker compose exec frontend npx tsc --noEmit` validado com `EXIT_CODE:0`.
- ✅ Instruções e skills atualizadas para fluxo compose-only e validação manual sem suíte E2E ativa.

---

### Relevant Files

**Config:**
- `frontend/tailwind.config.ts`, `frontend/src/app/globals.css`

**Componentes (6 NEW + 8 UPDATE):**
- **NEW**: temperature-badge, kpi-card, lead-item-card, detail-panel, segmented-tabs, frosted-header
- **UPDATE**: badge, button, card, tabs, input, select, table

**Páginas (5 UPDATE + 2 UPDATE):**
- Autenticadas: dashboard, leads, leads/[id], onboarding, settings
- Auth: login, register

**Testes:**
- `frontend/tests/scripts/seed_e2e.py` (suporte à validação manual)

---

### Verification

1. **Color System** — Paleta correta, temperature badges com icons, shadows aplicados
2. **Layout** — 42/58 split (desktop), full-width (mobile), sliding smooth
3. **Dark Mode** — Todos os `dark:` prefixes, navy #0B1120 (nunca preto), contrast ≥ 4.5:1
4. **Animations** — ease-spring 500ms, button hover lift, tab transitions 300ms, 60fps
5. **Tests** — `npm run lint` ✓, `npx tsc --noEmit` ✓, validação manual no Integrated Browser ✓

---

### Decisions

- ✅ **Incluso**: Visual 100%, dark mode, sliding panels, componentes reutilizáveis, responsive
- ❌ **Excluído**: Lógica de negócio, state management, API calls, auth flow
- 📌 **Componentes reutilizáveis** em TSX para máxima reutilização
- 📌 **Sliding panels**: State local na página, sempre renderizado (facilita animações)

---

### Further Considerations

1. **Componentes reutilizáveis vs. inline Tailwind**: Criar componentes TSX para máxima reutilização ✓
2. **Sliding Panels no Dashboard**: State local na página, painel sempre renderizado (simplifica animation)
3. **Performance da Sliding Animation**: Se houver lag, considerar `will-change: width, opacity` para GPU acceleration
