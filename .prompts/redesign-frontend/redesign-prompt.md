Atue como um Engenheiro Front-end Sênior e Especialista em UI/UX focado em produtos B2B (Micro SaaS Enterprise).

Eu forneci a você o arquivo `App.jsx` (ou o código fonte do novo Dashboard). Este arquivo contém o nosso **novo Design System** ("Nordic Minimalist / Slate & Steel") já implementado, validado e com suporte nativo a Light/Dark Mode.

Sua missão é refatorar o restante do nosso frontend (Next.js, Tailwind CSS, shadcn/ui) para que TODO o sistema fique visualmente idêntico à estética, espaçamento e comportamentos mecânicos criados no `App.jsx`.

⚠️ **REGRA DE OURO INQUEBRÁVEL:** ⚠️
VOCÊ ESTÁ ESTRITAMENTE PROIBIDO DE QUEBRAR OU ALTERAR A LÓGICA DE NEGÓCIO, GERENCIAMENTO DE ESTADO (Hooks como `useState`, `useEffect`), FUNÇÕES DE FETCH OU INTEGRAÇÕES DE API EXISTENTES nos arquivos que você for refatorar. O foco é ÚNICA E EXCLUSIVAMENTE a camada de apresentação (HTML, classes Tailwind e animações CSS).

---

### 🔍 1. Engenharia Reversa do `App.jsx` (Sua Fonte da Verdade)
Antes de alterar qualquer código, analise o `App.jsx` fornecido e extraia os seguintes padrões que você **DEVE** replicar:

* **Paleta Base:** O uso de `bg-slate-50` para fundos no Light mode e `dark:bg-[#0B1120]` no Dark mode (azul-noite muito escuro, NUNCA preto puro).
* **Superfícies (Cards):** O padrão exato de `bg-white dark:bg-slate-900/50 rounded-2xl border border-slate-100 dark:border-slate-800/60 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none backdrop-blur-sm`.
* **Cores Semânticas:** O estilo dos títulos (ex: `text-slate-900 dark:text-slate-50`) e as cores de *badges* semânticas em tons suaves (ex: `bg-teal-50 text-teal-700 dark:bg-teal-500/10 dark:text-teal-400` para sucesso/quente). NUNCA use vermelho/laranja gritante.
* **Segmented Control (Tabs):** A estrutura de abas para filtros (`bg-slate-200/60 dark:bg-[#131C2D] p-1.5 flex...`) deve ser o padrão para qualquer menu de abas do sistema.

---

### 🚀 2. O Padrão "Sliding Master-Detail" (Layout Dinâmico)
Em telas onde houver uma Lista e uma visualização de Detalhes (como a tela de leads), você **NÃO DEVE** usar Grid estático. Você **DEVE** usar o padrão Flex dinâmico com transições suaves que extraí do `App.jsx`:

1. **Container Principal:** `flex flex-col lg:flex-row items-start w-full relative`
2. **Curva de Animação:** Use uma classe customizada como `transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)]` em ambos os painéis.
3. **Painel da Esquerda (Lista):** - Quando não houver item selecionado, ele deve ocupar 100% da largura (`w-full`). 
   - Quando um item estiver selecionado, ele deve encolher suavemente (ex: `lg:w-[42%] lg:pr-6`).
4. **Painel da Direita (Detalhes):** - Quando não houver item selecionado, ele deve ser escondido suavemente (`w-0 opacity-0 max-h-0`). 
   - Quando um item for selecionado, ele desliza preenchendo o resto da tela (`lg:w-[58%] opacity-100 max-h-[3000px]`). É fundamental usar um *Inner Wrapper* de largura fixa para o conteúdo interno não "esmagar" durante a transição de *width*.
5. **Ações de Toggle:** Os itens da lista devem funcionar como *toggle* (clicar no mesmo item fecha o painel). O painel de detalhes deve ter um botão de Fechar (ícone "X") no cabeçalho.

---

### 🛠️ 3. Plano de Execução

1.  **Analise a Tela Atual:** Eu indicarei qual arquivo quero refatorar.
2.  **Preserve a Lógica:** Identifique e isole todos os hooks e states originais.
3.  **Aplique o Design System & Animações:** Reescreva a marcação JSX aplicando os tokens extraídos e garantindo que listas com detalhes ganhem o comportamento de "Sliding Panels".
4.  **Dark Mode Checklist:** Certifique-se de que cada nova classe adicionada possui sua contraparte `dark:` rigorosamente mapeada para a paleta do `App.jsx`.

Por favor, confirme que entendeu o comportamento do layout dinâmico e aguarde eu enviar o primeiro arquivo a ser refatorado.