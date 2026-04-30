# 📚 Estrutura Otimizada de Orquestração e Documentação para Copilot Chat Agent

## 1. Arquivos Orquestradores

Crie/atualize arquivos-guia que funcionam como “índices” ou “gateways” para as demais instruções/contextos. Eles devem:

- Explicar a função de cada arquivo de contexto (instructions, skills, memories, RFCs, diagramas, etc.).
- Orientar a IA sobre quando e como carregar cada arquivo, evitando leituras desnecessárias.
- Listar arquivos que devem ser lidos sempre (core) e arquivos que só devem ser lidos sob demanda (por domínio ou contexto).

Sugestão de arquivos orquestradores:

- `.github/instructions/CONTEXT-INDEX.md` (ou README.md dentro de instructions/)
- `.github/skills/SKILLS-INDEX.md`
- `memories/CONTEXT-INDEX.md` (para memórias persistentes)
- `.github/ARCHITECTURE.md` (índice de documentação arquitetural, RFCs e diagramas)

---

## 2. Documentação de Estrutura e Arquitetura

- Crie `.github/ARCHITECTURE.md` como arquivo central de arquitetura.
- Inclua diagramas Mermaid para fluxos, dependências, relacionamentos entre módulos, entidades e serviços.
- Para decisões importantes, use RFCs em `.github/rfcs/` (ex: `.github/rfcs/001-nome-da-decisao.md`).
- Sempre relacione diagramas e RFCs no arquivo de arquitetura para facilitar navegação.
- Exemplo de índice em ARCHITECTURE.md:

```markdown
# Arquitetura do Projeto

## Diagramas
- [Diagrama de Módulos](#diagrama-de-módulos)
- [Fluxo de Autenticação](#fluxo-de-autenticação)
- [Relacionamento de Entidades](#relacionamento-de-entidades)

## RFCs
- [001 - Padrão de Serviços](rfcs/001-padrao-servicos.md)
- [002 - Estratégia de Deploy](rfcs/002-estrategia-deploy.md)

## Dependências
- Listagem e explicação das dependências principais do projeto.
```

---

## 3. Instruções Guia (Orquestração de Contexto)

- No arquivo orquestrador (ex: CONTEXT-INDEX.md), explique:
  - Quais arquivos são sempre lidos (core: PRD, plano, progresso, copilot-instructions).
  - Quais arquivos são carregados sob demanda (skills, RFCs, diagramas, memories específicas).
  - Como a IA deve decidir qual skill/instruction carregar (ex: “Se a tarefa envolver autenticação, leia também skills/autenticacao/SKILL.md”).
  - Como manter o contexto enxuto e relevante.

---

## 4. Atualização de Arquivos-Chave

- Liste explicitamente, em todos arquivos orquestradores, quais arquivos devem ser atualizados sempre que houver mudanças em:
  - Estrutura de pastas/módulos
  - Novos fluxos implementados
  - Mudanças em dependências ou integrações
  - Novas decisões arquiteturais (RFCs)
  - Novos diagramas ou alterações em fluxos existentes

---

## 5. Exemplo de Estrutura Recomendada

```
.github/
  instructions/
    CONTEXT-INDEX.md
    copilot-instructions.md
    <outras instructions>
  skills/
    SKILLS-INDEX.md
    <domínio>/
      SKILL.md
  ARCHITECTURE.md
  rfcs/
    001-nome-da-decisao.md
memories/
  repo/
    CONTEXT-INDEX.md
    <memórias específicas>
.prompts/
  prd.md
  plano.md
  progresso.md
```

---

## 6. Exemplo de Conteúdo para CONTEXT-INDEX.md

```markdown
# Índice de Contexto para Copilot Chat Agent

## Sempre carregar:
- .prompts/prd.md
- .prompts/plano.md
- .prompts/progresso.md
- .github/instructions/copilot-instructions.md

## Carregar sob demanda:
- .github/skills/SKILLS-INDEX.md (guia para skills por domínio)
- .github/ARCHITECTURE.md (estrutura, diagramas, RFCs)
- memories/CONTEXT-INDEX.md (memórias persistentes relevantes)
- Arquivos de skills específicos conforme domínio da tarefa

## Como decidir:
- Consulte SKILLS-INDEX.md para saber qual skill carregar.
- Consulte ARCHITECTURE.md para diagramas, fluxos e decisões arquiteturais.
- Consulte memories/CONTEXT-INDEX.md para fatos persistentes.

## Sempre atualizar:
- Este índice ao criar/remover arquivos de contexto.
- ARCHITECTURE.md ao alterar estrutura, fluxos ou dependências.
- SKILLS-INDEX.md ao criar/remover skills.
```

---

## 7. Boas Práticas

- Sempre documente mudanças estruturais e arquiteturais.
- Atualize índices/orquestradores imediatamente após alterações.
- Prefira diagramas Mermaid para facilitar entendimento visual.
- Use RFCs para decisões importantes e relacione-as no índice.
- Mantenha instruções e skills curtas, modulares e bem referenciadas.
