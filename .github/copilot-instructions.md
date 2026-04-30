---
name: Copilot Agent Instructions
description: Instruções persistentes para LLMs que trabalham neste workspace. Este arquivo é lido automaticamente pelo GitHub Copilot como contexto em toda interação. 
applyTo: "**/*"
---

# Instruções de Onboarding para o Copilot Cloud Agent

## Visão Geral

**Propósito do Repositório:**
- Micro SaaS para triagem e gestão de leads do WhatsApp. Escuta mensagens do WhatsApp, usa LLMs para classificar a temperatura do lead, gerar resumos e sugerir respostas, ajudando o time de vendas a focar nas melhores oportunidades.

**Stack & Tamanho:**
- Monorepo de porte médio: Python 3.11+ (FastAPI, SQLAlchemy async, Alembic), PostgreSQL 16, LiteLLM, Next.js 16 (React, Tailwind, shadcn/ui), Docker Compose, Playwright, ESLint, TypeScript.
- Backend: `/app/`  |  Frontend: `/frontend/`  |  Testes: `/tests/`, `/frontend/tests/`

**Arquivos-chave na raiz:**
- `Dockerfile`, `docker-compose.yml`, `entrypoint.sh`, `requirements.txt`, `pytest.ini`, `.env.example`, `.python-version`, `.github/`, `.prompts/`, `README.md`

## Instruções de Build, Execução e Validação

### Configuração de Ambiente
- **Python:** Use Python 3.11+ (veja `.python-version`).
- **Node:** Use Node 20+ para o frontend.
- **Banco de Dados:** PostgreSQL 16 (provisionado automaticamente pelo Docker Compose).
- **Ambiente:** Copie `.env.example` para `.env` e preencha os segredos necessários.

### Bootstrap & Execução (Recomendado: Docker Compose)
1. `docker-compose up --build`  
   - Sobe backend (FastAPI), frontend (Next.js) e banco PostgreSQL.
   - Backend: http://localhost:8000  |  Frontend: http://localhost:3000
2. Para popular dados de teste: `docker-compose exec backend python3 frontend/tests/scripts/seed_e2e.py`

### Dev Local Manual (Avançado)
- Backend: 
  1. `python3 -m venv .venv && source .venv/bin/activate`
  2. `pip install -r requirements.txt`
  3. `alembic upgrade head` (migrações)
  4. `uvicorn app.main:app --reload`
- Frontend:
  1. `cd frontend`
  2. `npm install`
  3. `npm run dev`

### Lint
- **Python:** `ruff check .` ou `flake8 .` (se configurado)
- **JS/TS:** `npm run lint` (usa ESLint, config em `frontend/eslint.config.mjs`)
- **Auto-fix:** `ruff check . --fix` ou `npm run lint -- --fix`

### Type Checking
- **Python:** `mypy .` (se configurado)
- **TypeScript:** `npm run type-check` ou `tsc --noEmit`

### Testes
- **Backend:** `pytest` (unitário/integrado, usa SQLite in-memory para integração)
- **Frontend:** `npm run test:e2e` (Playwright, veja `frontend/tests/`)
- **Seed E2E:** Rode `frontend/tests/scripts/seed_e2e.py` antes dos testes E2E.

### CI/CD & Validação
- CI roda a cada push/PR: lint, type-check e testes (veja `.github/instructions/ci.md`).
- Sempre garanta que todos os checks passam antes de fazer merge.
- Se um comando falhar localmente, reproduza e corrija antes de subir.

### Problemas Comuns & Workarounds
- Sempre rode `npm install` antes de buildar o frontend.
- Se ocorrerem erros de banco, garanta que as migrações estão atualizadas (`alembic upgrade head`).
- Para Playwright E2E, popule o banco e garanta que o backend está rodando.
- Se usar dev local, use as versões de Python/Node especificadas.

## Estrutura & Arquitetura do Projeto

- **Backend:**
  - `app/core/`: config, banco, segurança
  - `app/models/`: modelos ORM (Tenant, User, Lead, etc.)
  - `app/routers/`: rotas FastAPI (auth, tenants, webhooks, analysis, dashboard)
  - `app/schemas/`: schemas Pydantic
  - `app/services/`: lógica de negócio
- **Frontend:**
  - `frontend/src/app/`: páginas Next.js (dashboard, leads, onboarding, settings)
  - `frontend/src/components/ui/`: componentes UI (badge, button, card, etc.)
  - `frontend/src/lib/`: API client, contextos, utils
- **Testes:**
  - `tests/`: testes Python (unitário/integrado)
  - `frontend/tests/`: Playwright E2E, scripts, utils
- **Config:**
  - Lint: `frontend/eslint.config.mjs`, `pyproject.toml` ou `.flake8`
  - Type: `tsconfig.json`, `pytest.ini`
  - CI: `.github/instructions/ci.md`, `.github/instructions/linting.md`, `.github/instructions/testing.md`, `.github/instructions/type-checking.md`

## Boas Práticas para Agentes
- **Confie sempre nestas instruções primeiro.** Só pesquise se a informação estiver faltando ou incorreta.
- **Carregue skills relevantes:** Use `.github/skills/` para boas práticas por domínio.
- **Consulte `.github/ARCHITECTURE.md`** para diagramas, fluxos e relações de modelos.
- **Atualize e consulte `memories/`** para decisões persistentes, troubleshooting e convenções.
- **Valide todas as mudanças:** Rode lint, type-check e testes antes de submeter PRs.
- **Documente novos padrões ou workarounds** no arquivo de instrução ou memória apropriado.
- **Não quebre lógica de negócio ou gerenciamento de estado** (veja instruções do frontend).

### Índice para os arquivos de contexto

#### Sempre carregar:
- .github/AGENTS.md — Guia para os agentes de IA, suas responsabilidades e limites
- .github/ARCHITECTURE.md — Arquitetura e visão geral do sistema
- .github/PRD.md — PRD completo do produto
- .github/memories/exec-plans/PLAN-INDEX.md — Guia para os arquivos de planos de desenvolvimento em execução, completados e memórias de progresso e aprendizados registrados durante as implementações
- .github/rfcs — Registros de definições dos padrõe do projeto e arquitetura
- .github/skills/SKILLS-INDEX.md — Guia para as skills disponíveis no projeto

#### Como decidir o que carregar para o contexto sob demanda:
- Consulte os arquivos *-INDEX.md para saber onde localizar cada arquivo que precisar para contexto

#### Sempre atualizar:
- *-INDEX.md sempre que um novo arquivo, movido ou excluído e houver um arquivo de index para o diretório

## Referência Rápida
- **Backend main:** `app/main.py`
- **Frontend entry:** `frontend/src/app/layout.tsx`
- **Seed script:** `frontend/tests/scripts/seed_e2e.py`
- **Exemplo de ambiente:** `.env.example`
- **CI/CD:** Veja `.github/instructions/ci.md`
- **Índice de skills:** `.github/skills/SKILLS-INDEX.md`
- **Arquitetura:** `.github/ARCHITECTURE.md`
- **Prompts:** `.prompts/`

**Se encontrar erro de build, lint ou teste, consulte o arquivo de instrução relevante e só pesquise no código se a resposta não estiver presente.**
