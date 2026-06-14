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
- Monorepo de porte médio: Python 3.11+ (FastAPI, SQLAlchemy async, Alembic), PostgreSQL 16, LiteLLM, Next.js 16 (React, Tailwind, shadcn/ui), Docker Compose, ESLint, TypeScript.
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
  1. `docker compose up -d frontend`
  2. `docker compose exec frontend npm install`
  3. `docker compose exec frontend npm run dev`

### Regra Operacional (Agentes)
- **NUNCA rode `npm run ...` diretamente no host.**
- **SEMPRE execute comandos Node/Frontend via Docker Compose**, por exemplo:
  - `docker compose exec frontend npm run lint`
  - `docker compose exec frontend npx tsc --noEmit`
- Se o container não estiver ativo, suba antes com `docker compose up -d frontend`.
- Caso precise rodar comandos Python, prefira usar o ambiente virtual do projeto no .python-version
- Para rodar testes Python, use o ambiente virtual
- Para subir o serviço backend, use o Docker Compose. Sempre evite rodar o backend diretamente no host para evitar conflitos de dependências.
- Antes de abrir PR, sempre replique os checks do CI exatamente na mesma ordem.
- Jamais instale dependências globalmente no host. Use ambientes virtuais ou Docker para isolar o ambiente de desenvolvimento.
- Sempre que uma lib for adicionada ou removida, atualize o arquivo de dependências (`requirements.txt`, `pyproject.toml`) e rode os comandos de instalação e migração necessários.
- Jamais utilize tag latest para nenhuma dependência, seja de Python, Node ou Docker. Sempre fixe a versão para garantir reprodutibilidade, evitar quebras inesperadas e por segurança.
- NUNCA delete testes unitários ou de integração sem autorização explícita. Se um teste estiver falhando, investigue a causa raiz e corrija o código ou o teste, mas não remova a cobertura de teste.

### Ambiente e Dependências do Frontend
- Para bootstrap ou rebuild do frontend, prefira `docker compose up --build -d` para manter host e container sincronizados.
- Se precisar refazer o ambiente, remova `node_modules`, `.next` e outros caches no host e no container antes de subir novamente com `docker compose up --build -d`.
- Antes de validar fluxos no frontend, confirme que host e container estão sincronizados.

### Lint
- **Python:** `ruff check .` ou `flake8 .` (se configurado)
- **JS/TS:** `docker compose exec frontend npm run lint` (usa ESLint, config em `frontend/eslint.config.mjs`)
- **Auto-fix:** `ruff check . --fix` ou `docker compose exec frontend npm run lint -- --fix`

### Type Checking
- **Python:** `mypy .` (se configurado)
- **TypeScript:** `docker compose exec frontend npm run type-check` ou `docker compose exec frontend npx tsc --noEmit`

### Testes
- **Backend:** `pytest` (unitário/integrado, usa SQLite in-memory para integração)
- **Frontend:** atualmente sem suíte E2E automatizada ativa.
- **Seed E2E:** `frontend/tests/scripts/seed_e2e.py` pode ser usado para povoar dados de validação manual no Integrated Browser.

### CI/CD & Validação
- CI roda a cada push/PR: lint, type-check e testes (veja `.github/instructions/ci.md`).
- Sempre garanta que todos os checks passam antes de fazer merge.
- Se um comando falhar localmente, reproduza e corrija antes de subir.

### Problemas Comuns & Workarounds
- Sempre rode `npm install` antes de buildar o frontend.
- Se ocorrerem erros de banco, garanta que as migrações estão atualizadas (`alembic upgrade head`).
- Se usar dev local, use as versões de Python/Node especificadas.

### Validação de Frontend (Obrigatória para Agentes)
- **Use o Integrated Browser do VS Code** para validar visual e comportamento das páginas (`http://localhost:3000/...`).
- **Após qualquer alteração de frontend, navegue por TODAS as telas alteradas** (incluindo rotas públicas e autenticadas impactadas).
- **Quando a tarefa envolver código em `frontend/` ou integração frontend-backend**, siga o padrão de pastas do projeto em Next.js, valide endpoints alterados e atualize componentes e páginas conforme `.github/rfcs/002-frontend-redesign.md`.
- **Para validar fluxos críticos manualmente**, rode o seed E2E a partir da raiz do projeto para garantir dados consistentes no frontend:
  1. `pwd`
  2. `cd <diretorio-raiz-do-projeto>`
  3. `PYTHONPATH=. python3 frontend/tests/scripts/seed_e2e.py`
- **Credenciais padrão para validação manual no ambiente local:**
  - E-mail: `teste@teste.com`
  - Senha: `123456`
- **Acompanhe logs em paralelo** com Docker Compose durante toda validação de frontend:
  - `docker compose logs -f frontend`
- Para inspeção pontual (sem follow):
  - `docker compose logs --tail=200 frontend`
- Em caso de erro de hidratação/renderização, sempre validar:
  1. Console do Integrated Browser
  2. Logs do serviço frontend (`docker compose logs`)
  3. Se o erro desaparece após reload completo da página
- Após alterações em UI/SSR/CSR, considerar obrigatório revisar logs do `frontend` antes de concluir a tarefa.

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
  - `frontend/tests/`: scripts utilitários de validação/seed
- **Config:**
  - Lint: `frontend/eslint.config.mjs`, `pyproject.toml` ou `.flake8`
  - Type: `tsconfig.json`, `pytest.ini`

## Boas Práticas para Agentes
- **Confie sempre nestas instruções primeiro.** Só pesquise se a informação estiver faltando ou incorreta.
- **Carregue skills relevantes:** Use `.github/skills/` para boas práticas por domínio.
- **Consulte `.github/ARCHITECTURE.md`** para diagramas, fluxos e relações de modelos.
- **Atualize e consulte `memories/`** para decisões persistentes, troubleshooting e convenções.
- **Valide todas as mudanças:** Rode lint, type-check e testes antes de submeter PRs.
- **Documente novos padrões ou workarounds** no arquivo de instrução ou memória apropriado.
- **Não quebre lógica de negócio ou gerenciamento de estado**, seguindo as orientações de frontend neste arquivo.
- **Em tarefas de frontend, não esqueça de validar endpoints após alterações e de atualizar o progresso depois de mudanças relevantes.**

### Índice para os arquivos de contexto

#### Sempre carregar:
- .github/AGENTS.md — Guia para os agentes de IA, suas responsabilidades e limites
- .github/ARCHITECTURE.md — Arquitetura e visão geral do sistema
- .github/PRD.md — PRD completo do produto
- .github/memories/exec-plans/PLAN-INDEX.md — Guia para os arquivos de planos de desenvolvimento em execução, completados e memórias de progresso e aprendizados registrados durante as implementações
- .github/rfcs — Registros de definições dos padrõe do projeto e arquitetura
- .github/skills/ — skills disponíveis no projeto

#### Como decidir o que carregar para o contexto sob demanda:
- Consulte os arquivos *-INDEX.md para saber onde localizar cada arquivo que precisar para contexto

#### Sempre atualizar:
- *-INDEX.md sempre que um novo arquivo, movido ou excluído e houver um arquivo de index para o diretório

## Referência Rápida
- **Backend main:** `app/main.py`
- **Frontend entry:** `frontend/src/app/layout.tsx`
- **Seed script:** `frontend/tests/scripts/seed_e2e.py`
- **Exemplo de ambiente:** `.env.example`
- **Arquitetura:** `.github/ARCHITECTURE.md`
- **Prompts:** `.prompts/`

**Se encontrar erro de build, lint ou teste, consulte o arquivo de instrução relevante e só pesquise no código se a resposta não estiver presente.**
