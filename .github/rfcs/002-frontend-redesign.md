# RFC 002 - Redesign Visual do Frontend — SaaS Enterprise Moderno (Nordic Minimalist)

## Status

Implementada e adotada como referência do frontend atual.

## Sumário

Esta RFC registra o redesign completo da interface do frontend do produto, desenvolvido em Next.js, Tailwind CSS e shadcn/ui, com foco em elevar o padrão visual para um nível SaaS Enterprise moderno, seguindo diretrizes de design minimalista nórdico. O resultado consolidado aprimora a experiência do usuário, preserva a lógica de negócio e formaliza o design system e o protocolo de validação hoje vigentes.

## Motivação

O frontend anterior era funcional, porém apresentava limitações visuais, inconsistências tipográficas e fragilidade na experiência de carregamento/hidratação, transmitindo uma imagem aquém do posicionamento do produto. Como o sistema atende o mercado B2B (Micro SaaS), a percepção de valor está diretamente ligada à qualidade visual, previsibilidade de navegação e clareza de informação.

## Escopo

- Redesign visual completo das páginas públicas e autenticadas do frontend.
- Consolidação do design system Nordic Minimalist a partir do protótipo em `.prompts/redesign-frontend/lead-dashboard/src/App.jsx`.
- Padronização visual de superfícies, botões, inputs, badges de temperatura e tabs segmentadas.
- Garantia de suporte consistente a Light e Dark Mode, evitando preto puro no tema escuro.
- Melhoria dos estados de carregamento e eliminação de divergências SSR/CSR observadas durante hidratação.
- Preservação das integrações e fluxos existentes, com exceção de ajustes técnicos pontuais de bootstrap/hidratação sem impacto nas regras de negócio.
- Padronização do fluxo de validação frontend via Docker Compose, Integrated Browser e análise de logs.
- Descontinuação da suíte E2E Playwright legada; validação frontend atualmente é manual.

## Diretrizes de Design

### Paleta e Estética

- **Background Principal:**
  - Light: `bg-slate-50`
  - Dark: `dark:bg-[#0B1120]` (evitar preto puro)
- **Cards e Containers:**
  - Light: `bg-white`, `border-slate-100`
  - Dark: `dark:bg-slate-900/50`, `dark:border-slate-800/60`
  - Comum: `rounded-2xl`, `shadow-[0_8px_30px_rgb(0,0,0,0.04)]`, `dark:shadow-none`, `backdrop-blur-sm`
- **Tipografia (stack explícita):**
  - Sans: `"Segoe UI", "Inter", "SF Pro Text", "Helvetica Neue", Arial, sans-serif`
  - Mono: `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace`
  - Light: Títulos `text-slate-900`, secundários `text-slate-500`
  - Dark: Títulos `dark:text-slate-50`, secundários `dark:text-slate-400`
- **Cores de Destaque:**
  - Azul aço e turquesa/teal escuro
  - Botões principais: Light `bg-slate-900 text-white`, Dark `dark:bg-teal-600 dark:text-white`
  - Botões secundários/outline: superfícies brancas/slate com borda sutil e hover controlado
- **Badges de Temperatura do Lead:**
  - Frio: Light `bg-slate-100 text-slate-600`, Dark `dark:bg-slate-800/50 dark:text-slate-300`
  - Morno: Light `bg-blue-50 text-blue-600`, Dark `dark:bg-blue-500/10 dark:text-blue-400`
  - Quente: Light `bg-teal-50 text-teal-700`, Dark `dark:bg-teal-500/10 dark:text-teal-400`
  - Proibido uso de vermelho/laranja gritante
- **Componentes Semânticos Consolidados:**
  - `temperature-badge.tsx` para score/temperatura
  - `segmented-tabs.tsx` para filtros e mudança de contexto

### Experiência e Usabilidade

- Interface limpa, focada em dados, com excelente legibilidade e espaçamento (`p-6`, `gap-4`)
- Dashboard com KPIs no topo e padrão `Sliding Master-Detail` para lista e detalhe
- Leads com filtros segmentados, busca destacada e tabela modernizada
- Skeleton Loaders para estados de carregamento, com suporte a Dark Mode
- Toggle de tema minimalista no shell autenticado
- Feedback visual sutil em botões e painéis de loading
- Utilitário `hide-scrollbar` para áreas de overflow horizontal sem ruído visual

### Padrão de Layout Dinâmico

- Em telas com lista + detalhe, o padrão oficial é `Sliding Master-Detail`, e não grid estático.
- Container principal: `flex flex-col lg:flex-row items-start w-full relative`
- Curva de animação: `transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)]`
- Painel esquerdo:
  - sem item selecionado: `w-full`
  - com item selecionado: `lg:w-[42%] lg:pr-6`
- Painel direito:
  - sem item selecionado: `w-0 opacity-0 max-h-0`
  - com item selecionado: `lg:w-[58%] opacity-100 max-h-[3000px]`
- O painel de detalhe deve permitir toggle de fechamento pelo mesmo item ou por botão explícito de fechar.

## Restrições

- É estritamente proibido alterar:
  - Lógica de negócio
  - Chamadas de API
  - Mapeamento de dados e integrações
- Hooks de estado só podem sofrer ajustes técnicos de hidratação/bootstrap client-side quando necessários para eliminar divergência SSR/CSR, sem alterar regras de negócio, permissões, contratos de API ou fluxos funcionais.
- Todos os eventos (`onClick`, `disabled`, double submit, etc.) devem ser preservados

## Implementação Consolidada

- Páginas atualizadas:
  - `frontend/src/app/page.tsx`
  - `frontend/src/app/(authenticated)/dashboard/page.tsx`
  - `frontend/src/app/(authenticated)/leads/page.tsx`
  - `frontend/src/app/(authenticated)/leads/[id]/page.tsx`
  - `frontend/src/app/(authenticated)/onboarding/page.tsx`
  - `frontend/src/app/(authenticated)/settings/page.tsx`
  - `frontend/src/app/login/page.tsx`
  - `frontend/src/app/register/page.tsx`
- Shell e base visual ajustados:
  - `frontend/src/app/layout.tsx`
  - `frontend/src/app/(authenticated)/layout.tsx`
  - `frontend/src/app/globals.css`
  - `frontend/src/components/theme-toggle.tsx`
  - `frontend/src/components/ui/button.tsx`
  - `frontend/src/components/ui/card.tsx`
  - `frontend/src/components/ui/input.tsx`
  - `frontend/src/components/ui/AppWithPreloader.tsx`
  - `frontend/src/lib/auth-context.tsx`
- Componentes novos consolidados:
  - `frontend/src/components/ui/temperature-badge.tsx`
  - `frontend/src/components/ui/segmented-tabs.tsx`

## Passos de Implementação

1. **Fonte da Verdade Visual**
   - Toda nova decisão visual deve partir do protótipo `lead-dashboard/src/App.jsx`.
2. **Refatoração Visual Controlada**
   - Atualizar classes Tailwind e componentes base, preservando fluxos funcionais.
3. **Compatibilidade SSR/CSR**
   - Tratar divergências de hidratação como parte do escopo técnico do redesign.
4. **Validação Manual Obrigatória**
   - Navegar por todas as telas alteradas no Integrated Browser.
   - Validar com `teste@teste.com` / `123456` quando necessário.
   - Acompanhar `docker compose logs -f frontend` durante a inspeção.
5. **Validação Técnica**
   - Executar `docker compose exec frontend npm run lint`.
   - Executar `docker compose exec frontend npx tsc --noEmit`.

## Estratégia de Testes

- Não existe suíte E2E automatizada ativa no frontend neste momento.
- Os testes Playwright legados foram removidos por estarem acoplados ao frontend anterior.
- O script `frontend/tests/scripts/seed_e2e.py` permanece como utilitário para popular dados de validação manual.

## Critérios de Aceite

- O layout deve refletir um painel financeiro/SaaS de altíssimo padrão, em ambos os temas
- Nenhuma regra de negócio, integração ou contrato de API deve ser alterado
- Todos os componentes alterados devem seguir o design system consolidado nesta RFC
- O frontend deve ser validado via Docker Compose, conforme instruções do projeto
- A validação deve incluir Integrated Browser, inspeção de logs do frontend e checagem de lint/type-check
