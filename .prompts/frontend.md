Atue como um Engenheiro Front-end Sênior e Especialista em UI/UX focado em produtos B2B (Micro SaaS). 

O nosso frontend atual (Next.js + Tailwind CSS + shadcn/ui) está funcional, porém visualmente amador e engessado. Preciso que você faça um redesign completo da interface, mas com uma regra de ouro: **VOCÊ ESTÁ ESTRITAMENTE PROIBIDO DE QUEBRAR OU ALTERAR A LÓGICA DE NEGÓCIO, GERENCIAMENTO DE ESTADO (Hooks), OU CHAMADAS DE API EXISTENTES.**

A aplicação está rodando localmente via Docker Compose. Acesse e inspecione o frontend para entender a estrutura do DOM e o fluxo de dados.

**Diretriz de Estilo Visual (Estética SaaS Enterprise Moderno / Nordic Minimalist):**
Quero uma interface extremamente limpa, focada em dados, com alto contraste de legibilidade e suporte nativo impecável para Light e Dark Mode. Siga RIGOROSAMENTE este Design System baseado em Tailwind:

- **Background Principal:** - Light: Tons off-white ou cinza muito frios (`bg-slate-50` ou `bg-gray-50`).
  - Dark: Ardósia profundo, não use preto puro (`dark:bg-slate-950` ou `dark:bg-[#0B1120]`).
- **Cards e Containers:** - Light: Fundo puramente branco (`bg-white`), bordas quase invisíveis (`border-slate-100`) e sombras difusas (`shadow-sm`).
  - Dark: Fundo levemente destacado do background (`dark:bg-slate-900`), bordas sutis (`dark:border-slate-800`), sem sombras agressivas.
  - Comum: Cantos arredondados suaves (`rounded-xl` ou `rounded-2xl`).
- **Tipografia (Inter/Geist):** - Light: Títulos em `text-slate-900`, secundários em `text-slate-500`.
  - Dark: Títulos em branco suave (`dark:text-slate-50`), secundários em cinza médio (`dark:text-slate-400`).
- **Cores de Destaque (Accents):** - Tons de "Azul Aço" (Steel Blue) e Turquesa/Teal escuro. 
  - Botões principais: Light (`bg-slate-800` text branco), Dark (`dark:bg-slate-100` text dark) ou usando as variáveis primárias do shadcn atualizadas.
- **Badges de Temperatura do Lead:** - NÃO use vermelho/laranja gritante em nenhum tema. Use uma progressão elegante. 
  - Frio: Light (`bg-slate-100 text-slate-600`), Dark (`dark:bg-slate-800/50 dark:text-slate-300`).
  - Morno: Light (`bg-blue-50 text-blue-600`), Dark (`dark:bg-blue-500/10 dark:text-blue-400`).
  - Quente: Light (`bg-teal-50 text-teal-700`), Dark (`dark:bg-teal-500/10 dark:text-teal-400`).

**Passo a Passo da Execução:**

1. **Inspeção e Planejamento:** Leia o código atual e liste quais componentes do shadcn/ui você vai atualizar. Verifique se o `next-themes` já está configurado. Se não estiver, informe os passos, mas foque primariamente nas classes visuais e variáveis CSS (`globals.css`).
2. **Refatoração Visual:** Atualize as classes do Tailwind (aplicando o prefixo `dark:` onde necessário) mantendo uma excelente gestão de *whitespace* (`p-6`, `gap-4`). Use Grid estruturado para o Dashboard.
3. **Feedback de Estado:** Melhore os estados de carregamento. Onde há processamento de IA (ex: botão "Atualizar Todos"), não use spinners genéricos; aplique Skeleton Loaders elegantes (com suporte a Dark Mode) ou botões com estado de *loading* sutil.
4. **Implementação do Toggle:** Certifique-se de que há um botão elegante e minimalista (ícone de Sol/Lua do Lucide React) no header da aplicação para alternar entre Light e Dark mode.
5. **Preservação de Lógica:** Garanta que todos os `onClick`, `disabled`, travas de *double submit* e mapeamento de dados (ex: volumetria e listas do funil) permaneçam 100% intactos.

Gere o código atualizado arquivo por arquivo, garantindo que o layout reflita um painel financeiro/SaaS de altíssimo padrão, tanto de dia quanto de noite.