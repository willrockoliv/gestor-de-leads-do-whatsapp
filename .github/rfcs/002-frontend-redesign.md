# RFC 002 - Redesign Visual do Frontend — SaaS Enterprise Moderno (Nordic Minimalist)

## Sumário

Esta RFC propõe um redesign completo da interface do frontend do produto, atualmente desenvolvido em Next.js, Tailwind CSS e shadcn/ui, com foco em elevar o padrão visual para um nível SaaS Enterprise moderno, seguindo diretrizes de design minimalista nórdico. O objetivo é aprimorar a experiência do usuário, mantendo intacta toda a lógica de negócio, hooks de estado e integrações de API.

## Motivação

O frontend atual é funcional, porém apresenta limitações visuais e de flexibilidade, transmitindo uma imagem amadora. O produto visa o mercado B2B (Micro SaaS), onde a percepção de valor está fortemente atrelada à qualidade visual e usabilidade. Um redesign alinhado a padrões modernos é fundamental para competitividade e retenção de clientes.

## Escopo

- Redesign visual completo dos componentes e páginas do frontend.
- Proibição explícita de alterações na lógica de negócio, hooks de estado e chamadas de API.
- Implementação rigorosa de um design system baseado em Tailwind CSS, conforme especificações abaixo.
- Garantia de suporte nativo e elegante a Light e Dark Mode.
- Melhoria dos estados de carregamento e feedback visual.
- Preservação total das integrações e fluxos existentes.

## Diretrizes de Design

### Paleta e Estética

- **Background Principal:**
  - Light: `bg-slate-50` ou `bg-gray-50`
  - Dark: `dark:bg-slate-950` ou `dark:bg-[#0B1120]` (evitar preto puro)
- **Cards e Containers:**
  - Light: `bg-white`, bordas `border-slate-100`, `shadow-sm`
  - Dark: `dark:bg-slate-900`, bordas `dark:border-slate-800`, sem sombras agressivas
  - Comum: `rounded-xl` ou `rounded-2xl`
- **Tipografia (Inter/Geist):**
  - Light: Títulos `text-slate-900`, secundários `text-slate-500`
  - Dark: Títulos `dark:text-slate-50`, secundários `dark:text-slate-400`
- **Cores de Destaque:**
  - Azul aço e turquesa/teal escuro
  - Botões principais: Light `bg-slate-800` (texto branco), Dark `dark:bg-slate-100` (texto escuro) ou variáveis primárias do shadcn atualizadas
- **Badges de Temperatura do Lead:**
  - Frio: Light `bg-slate-100 text-slate-600`, Dark `dark:bg-slate-800/50 dark:text-slate-300`
  - Morno: Light `bg-blue-50 text-blue-600`, Dark `dark:bg-blue-500/10 dark:text-blue-400`
  - Quente: Light `bg-teal-50 text-teal-700`, Dark `dark:bg-teal-500/10 dark:text-teal-400`
  - Proibido uso de vermelho/laranja gritante

### Experiência e Usabilidade

- Interface limpa, focada em dados, com excelente legibilidade e espaçamento (`p-6`, `gap-4`)
- Uso de Grid estruturado para o Dashboard
- Skeleton Loaders para estados de carregamento, com suporte a Dark Mode
- Botão de toggle (Sol/Lua, Lucide React) minimalista no header para alternância de tema
- Feedback visual sutil em botões de loading, evitando spinners genéricos

## Restrições

- É estritamente proibido alterar:
  - Lógica de negócio
  - Hooks de estado
  - Chamadas de API
  - Mapeamento de dados e integrações
- Todos os eventos (`onClick`, `disabled`, double submit, etc.) devem ser preservados

## Passos de Implementação

1. **Inspeção e Planejamento**
   - Listar componentes do shadcn/ui a serem atualizados
   - Verificar configuração do `next-themes`; se ausente, documentar passos necessários
2. **Refatoração Visual**
   - Atualizar classes Tailwind, aplicando `dark:` conforme necessário
   - Garantir gestão de whitespace e grid estruturado
3. **Feedback de Estado**
   - Implementar Skeleton Loaders e estados de loading elegantes
4. **Toggle de Tema**
   - Garantir presença de toggle minimalista no header
5. **Validação**
   - Garantir que toda lógica e integrações permaneçam intactas

## Critérios de Aceite

- O layout deve refletir um painel financeiro/SaaS de altíssimo padrão, em ambos os temas
- Nenhuma lógica de negócio, hook ou integração deve ser alterada
- Todos os componentes devem seguir rigorosamente o design system proposto
- O frontend deve ser validado via Docker Compose, conforme instruções do projeto
