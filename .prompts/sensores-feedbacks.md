# 🛡️ Instruções para Sensores e Feedbacks (Feedback Loops)

## 1. Linters

- Utilize linters automáticos para cada linguagem do projeto:
  - Python: [ruff](https://github.com/astral-sh/ruff) ou [flake8](https://flake8.pycqa.org/), configurado em `pyproject.toml` ou `.flake8`.
  - TypeScript/JS: [eslint](https://eslint.org/) com regras em `.eslintrc` ou `eslint.config.mjs`.
- Crie um arquivo `.github/instructions/linting.md` com:
  - Como rodar o linter manualmente e via CI.
  - Como corrigir erros automaticamente.
  - Como adicionar regras customizadas.
  - Exemplo de comando:  
    - Python: `ruff check .`  
    - JS: `npm run lint`

## 2. Type Checkers

- Python: [mypy](http://mypy-lang.org/) com configuração em `mypy.ini` ou `pyproject.toml`.
- TypeScript: `tsc --noEmit`
- Documente em `.github/instructions/type-checking.md`:
  - Como rodar o type checker.
  - Como interpretar e corrigir erros.
  - Como adicionar tipos em código legado.

## 3. Testes Automatizados

- Unitários: `pytest` para Python, `jest` ou `vitest` para JS/TS.
- Integração: use SQLite in-memory para backend, e2e para frontend.
- E2E: [Playwright](https://playwright.dev/) ou [Cypress](https://www.cypress.io/) para frontend.
- Crie `.github/instructions/testing.md`:
  - Como rodar todos os testes.
  - Como criar novos testes.
  - Convenções de nomeação e organização.
  - Como rodar testes em CI.
  - Exemplo:  
    - Python: `pytest`  
    - JS: `npm test`  
    - E2E: `npx playwright test`

## 4. Review Agent

- Especifique um agente de revisão (manual ou automatizado) em AGENTS.md:
  - Função: revisar PRs, sugerir melhorias, garantir padrões.
  - Checklist de revisão: cobertura de testes, padrões de código, docs atualizadas, etc.
  - Como acionar o agente (ex: via GitHub Actions, comentário `/review`).

## 5. Integração Contínua (CI)

- Configure workflows em `.github/workflows/` para rodar linters, type checkers e testes em cada push/PR.
- Documente em `.github/instructions/ci.md`:
  - Como funciona o pipeline.
  - Como depurar falhas.
  - Como adicionar novos jobs.

## 6. Sensores de Qualidade e Feedbacks

- Sempre registre falhas, erros e débitos técnicos em progresso.md ou repo.
- Use badges no README para status de build, cobertura, lint, etc.
- Oriente a IA a sempre rodar sensores antes de finalizar uma entrega.

---

## Exemplo de Estrutura

```
.github/
  instructions/
    linting.md
    type-checking.md
    testing.md
    ci.md
  workflows/
    lint.yml
    test.yml
    type-check.yml
  AGENTS.md
```

---

## Exemplo de Conteúdo para `.github/instructions/testing.md`

```markdown
# Guia de Testes

## Como rodar todos os testes
- Backend: `pytest`
- Frontend: `npm test`
- E2E: `npx playwright test`

## Como criar novos testes
- Siga convenções de nomeação: `test_<feature>.py` ou `<feature>.spec.ts`
- Use mocks para dependências externas.
- Testes de integração usam SQLite in-memory.

## CI
- Todos os testes são executados em cada push/PR.
- Corrija falhas antes de dar merge.

## Dicas
- Priorize TDD.
- Sempre cubra casos de erro e borda.
```
