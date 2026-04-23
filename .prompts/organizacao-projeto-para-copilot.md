# 🧠 Prompt para Organização de Projeto Otimizado para Copilot Chat Agent

## Objetivo

Analisar o projeto e criar/organizar todos os arquivos de contexto (instructions, skills, etc.) necessários para potencializar o desenvolvimento assistido por IA, seguindo as melhores práticas do GitHub Copilot Chat Agent (VS Code), com foco em:

- Reduzir o uso de tokens/contexto por interação
- Modularizar conhecimento e instruções
- Facilitar manutenção e evolução do repositório
- Garantir que a LLM sempre tenha contexto relevante e atualizado

---

## 1. Análise Inicial

- Leia os arquivos existentes: PRD (prd.md), plano (plano.md), progresso (progresso.md), e quaisquer instruções já presentes.
- Identifique domínios, fluxos principais, padrões de arquitetura e convenções do projeto.

---

## 2. Estrutura Recomendada

Crie/atualize os seguintes arquivos e pastas na raiz do repositório:

```
.github/
  instructions/
    copilot-instructions.md
    <outros arquivos de instructions por domínio ou contexto>
  skills/
    <nome-da-skill>/
      SKILL.md
      <outros arquivos auxiliares>
  AGENTS.md
  README.md
memories/
  repo/
    <notas e convenções específicas do repositório>
  <outros arquivos de memória persistente, se necessário>
```

---

## 3. Conteúdo dos Arquivos

### 3.1. copilot-instructions.md

- Descreva as convenções globais do projeto (estrutura, dependências, testes, validação, etc.).
- Liste arquivos de contexto obrigatórios (PRD, plano, progresso).
- Explique como e quando atualizar cada arquivo.
- Dê exemplos de fluxos de trabalho ideais para a LLM.
- Oriente sobre como validar e registrar progresso.

### 3.2. Skills (`.github/skills/<nome-da-skill>/SKILL.md`)

- Crie uma skill para cada domínio relevante (ex: autenticação, integração, frontend, testes, etc.).
- Cada `SKILL.md` deve conter:
  - Descrição do domínio e quando a skill deve ser carregada.
  - Padrões, exemplos e armadilhas comuns.
  - Como dividir instruções para evitar contexto desnecessário.
  - Links para arquivos de instrução ou memória relevantes.

### 3.3. `AGENTS.md`

- Liste agentes customizados (se houver), suas funções e quando invocá-los.
- Explique como criar novos agentes e boas práticas para prompts autônomos.

### 3.4. `memories/repo/`

- Armazene convenções, decisões arquiteturais, padrões de commit, dicas de troubleshooting e lições aprendidas.
- Mantenha arquivos curtos e objetivos para facilitar o carregamento automático.

### 3.5. README.md (atualização)

- Explique a estrutura de contexto do projeto.
- Oriente novos contribuidores sobre como usar e atualizar as instruções/skills/memórias.

---

## 4. Boas Práticas para Otimização de Tokens

- Separe instruções por domínio/contexto para evitar carregar tudo em cada interação.
- Use arquivos de memória para fatos persistentes e históricos, evitando repetições.
- Prefira instruções curtas, tópicos e listas ao invés de textos longos.
- Atualize skills e instructions sempre que fluxos mudarem ou bugs recorrentes forem identificados.
- Documente exemplos de prompts eficazes e ineficazes.

---

## 5. Exemplo de Conteúdo para copilot-instructions.md

```markdown
# Copilot Instructions

## Contexto do Projeto
- Sempre leia `.prompts/prd.md`, `.prompts/plano.md` e `.prompts/progresso.md` antes de iniciar tarefas.
- Siga as convenções de dependências, testes e validação descritas abaixo.

## Convenções
- Dependências: sempre atualize `requirements.txt` após instalar libs.
- Testes: use pytest, siga TDD, rode todos os testes após mudanças.
- Frontend: valide endpoints via curl após alterações.
- Documentação: atualize README e progresso após cada entrega.

## Skills
- Carregue skills específicas conforme o domínio da tarefa.
- Skills disponíveis: autenticação, frontend, integração, testes, etc.

## Memória
- Use arquivos em `memories/repo/` para registrar decisões e padrões.
```

---

## 6. Exemplo de Conteúdo para uma Skill (`skills/frontend/SKILL.md`)

```markdown
# Skill: Frontend

## Quando usar
- Sempre que a tarefa envolver código em `frontend/` ou integração frontend-backend.

## Padrões
- Use Next.js, siga o padrão de pastas do projeto.
- Valide endpoints via curl (ver instruções globais).
- Atualize componentes e páginas conforme especificação em `.prompts/frontend.md`.

## Armadilhas comuns
- Esquecer de validar endpoints após alterações.
- Não atualizar o progresso após mudanças relevantes.

## Links úteis
- [copilot-instructions.md](../instructions/copilot-instructions.md)
- [memories/repo/frontend-validation.md](../../memories/repo/frontend-validation.md)
```

---

## 7. Checklist Final

- [ ] Todos os arquivos de instructions criados/atualizados
- [ ] Skills separadas por domínio
- [ ] AGENTS.md documentado
- [ ] Memórias organizadas e enxutas
- [ ] README atualizado com instruções para contribuidores
