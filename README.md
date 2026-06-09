# Gestor de Leads do WhatsApp

## Estrutura de Contexto para Copilot Chat Agent

Este projeto está otimizado para desenvolvimento assistido por IA (Copilot Chat Agent), com contexto modularizado e instruções específicas por domínio.

### Estrutura Recomendada

```
.github/
	instructions/
		copilot-instructions.md
		<outros arquivos de instructions por domínio>
	skills/
		<nome-da-skill>/
			SKILL.md
	AGENTS.md
memories/
	repo/
		<notas e convenções específicas do repositório>
.prompts/
	prd.md
	plano.md
	progresso.md
	frontend.md
```

### Como usar e atualizar instruções/skills/memórias

- **Leia sempre** os arquivos de contexto obrigatórios antes de iniciar tarefas.
- **Carregue apenas as skills relevantes** para a tarefa em questão.
- **Atualize** as skills e instructions sempre que fluxos mudarem ou bugs recorrentes forem identificados.
- **Registre decisões, padrões e troubleshooting** em `memories/` de forma breve e objetiva.
- **Documente agentes customizados** em `.github/AGENTS.md`.

### Para novos contribuidores

1. Leia o PRD, plano e progresso em `.prompts/`.
2. Consulte `copilot-instructions.md` para convenções globais.
3. Use as skills em `.github/skills/` conforme o domínio da tarefa.
4. Consulte e atualize memórias em `memories/`.
5. Siga o fluxo de validação e registro de progresso descrito nas instruções.

---

Consulte sempre os arquivos de instrução e memórias para garantir contexto atualizado e evitar retrabalho.
# 📱 Gestor de Leads do WhatsApp

Micro SaaS de triagem de leads via WhatsApp. O sistema escuta mensagens via WebSocket, usa LLM para classificar a "temperatura" do lead, gerar resumos e sugerir respostas — permitindo que o vendedor foque nas oportunidades com maior intenção de compra.

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.14 · FastAPI · SQLAlchemy async |
| Banco de Dados | PostgreSQL 16 |
| IA | LiteLLM (OpenAI, Anthropic, Google) |
| WhatsApp | Waha / Evolution API (WebSocket) |
| Frontend | Next.js 16 · React · Tailwind CSS · shadcn/ui |
| Infra | Docker Compose · pyenv |

## Pré-requisitos

- [pyenv](https://github.com/pyenv/pyenv) com Python 3.14.3
- Docker e Docker Compose
- Chave de API de LLM (OpenAI, Anthropic ou Google) — necessária apenas para análise de leads

## Início Rápido

### Com Docker (recomendado)

```bash
# 1. Clonar e entrar no projeto
git clone <repo-url> && cd gestor-de-leads-do-whatsapp

# 2. Copiar variáveis de ambiente
cp .env.example .env
# Editar .env com suas chaves (SECRET_KEY, LLM_API_KEY, etc.)

# 3. Subir tudo (backend + PostgreSQL + frontend)
docker compose up --build -d
# Backend em localhost:8000, Frontend em localhost:3000
```

### Desenvolvimento local (sem Docker)

```bash
# 1. Criar virtualenv e ativar
pyenv virtualenv 3.14.3 gestor-leads
pyenv local gestor-leads

# 2. Instalar dependências do backend
pip install -r requirements.txt

# 3. Rodar testes
pytest tests/ -v

# 4. Frontend (em outro terminal)
cd frontend && npm install && npm run dev
```

## Variáveis de Ambiente

| Variável | Descrição | Default |
|----------|-----------|---------|
| `DATABASE_URL` | URL de conexão PostgreSQL (async) | `postgresql+asyncpg://postgres:postgres@db:5432/leads` |
| `SECRET_KEY` | Chave para assinatura JWT | `dev-secret-change-in-production` |
| `LLM_API_KEY` | Chave da API de LLM | — |
| `LLM_MODEL` | Modelo a usar via LiteLLM | `gpt-4o-mini` |
| `WHATSAPP_WEBHOOK_SECRET` | Secret HMAC do webhook | — |
| `WHATSAPP_API_URL` | URL da API WhatsApp | `http://waha:3000` |
| `WHATSAPP_API_PORT` | Porta da API WhatsApp | `3000` |
| `WHATSAPP_API_KEY` | Chave de autenticação do WAHA (`X-Api-Key`) | — |
| `WHATSAPP_PROVIDER` | Provider WhatsApp selecionado na factory | `waha` |
| `WHATSAPP_WEBHOOK_URL` | URL pública usada pelo WAHA para envio de eventos | — |
| `WHATSAPP_WEBHOOK_HMAC_KEY` | Chave HMAC usada pelo WAHA em `X-Webhook-Hmac` | — |
| `CORS_ORIGINS` | Origens permitidas (JSON list) | `["http://localhost:3000"]` |
| `DEBUG` | Modo debug | `false` |
| `NEXT_PUBLIC_API_URL` | URL da API (frontend) | `http://localhost:8000` |

### Security Headers (backend)

As variáveis abaixo controlam os headers de segurança enviados pela API.

| Variável | Descrição | Default |
|----------|-----------|---------|
| `SECURITY_CSP` | Política CSP da API (`Content-Security-Policy`) | `default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'` |
| `SECURITY_REFERRER_POLICY` | Header `Referrer-Policy` | `no-referrer` |
| `SECURITY_PERMISSIONS_POLICY` | Header `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` |
| `SECURITY_HSTS_MAX_AGE` | Valor base do `Strict-Transport-Security` em segundos | `31536000` |
| `SECURITY_HSTS_INCLUDE_SUBDOMAINS` | Adiciona `includeSubDomains` no HSTS | `true` |
| `SECURITY_HSTS_PRELOAD` | Adiciona `preload` no HSTS | `false` |

Recomendação por ambiente:
- Desenvolvimento local (sem TLS): mantenha defaults e avalie HSTS conforme necessidade do browser local.
- Produção (com HTTPS): mantenha HSTS ativo e só habilite `SECURITY_HSTS_PRELOAD=true` após validação formal do domínio para preload.

## Estrutura do Projeto

```
app/
├── core/           # Config, database, segurança (JWT)
├── models/         # SQLAlchemy models (Tenant, User, Lead, Message, Analysis)
├── providers/      # Contratos/factory/adapters de providers externos (ex: WhatsApp)
├── schemas/        # Pydantic schemas (request/response)
├── services/       # Lógica de negócio (auth, webhook, analysis, funnel)
├── routers/        # Endpoints FastAPI
│   ├── auth.py          # POST /auth/register, /auth/login, GET /auth/me
│   ├── tenants.py       # PUT /tenants/me/funnel, GET /tenants/me
│   ├── webhooks.py      # POST /webhooks/whatsapp
│   ├── analysis.py      # POST /leads/{id}/analyze, /leads/analyze-all
│   └── dashboard.py     # GET /leads, /leads/{id}, /dashboard/stats, etc.
└── main.py         # App FastAPI + watchdog background task
tests/              # pytest + pytest-asyncio (SQLite in-memory)
alembic/            # Migrations
frontend/           # Next.js 16 + TypeScript + Tailwind + shadcn/ui
├── src/app/             # App Router pages
│   ├── login/           # Página de login
│   ├── register/        # Página de cadastro
│   └── (authenticated)/ # Layout autenticado
│       ├── dashboard/   # Dashboard com Kanban
│       ├── leads/       # Lista e detalhe de leads
│       └── settings/    # Configuração do funil
├── src/components/      # Componentes reutilizáveis
└── src/lib/             # API client, auth context, utils
```

## API — Endpoints Principais

### Auth
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/auth/register` | Cria usuário + tenant, retorna JWT |
| POST | `/auth/login` | Autentica, retorna JWT |
| GET | `/auth/me` | Dados do usuário autenticado |
| GET | `/auth/funnel-templates` | Templates de funil disponíveis |

### Tenant
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/tenants/me` | Dados do tenant |
| PUT | `/tenants/me/funnel` | Atualiza configuração do funil |

### Webhook
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/webhooks/whatsapp` | Recebe eventos do WAHA com validação HMAC |

### WhatsApp Session
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/whatsapp/connect` | Cria/inicia sessão WhatsApp do tenant |
| GET | `/whatsapp/qrcode` | Retorna QR code atual da sessão |
| GET | `/whatsapp/status` | Retorna status da sessão e telefone conectado |

### Troubleshooting WhatsApp

- Provider não inicializa:
	- verifique `WHATSAPP_PROVIDER` no `.env` (valor atual suportado: `waha`).
	- se usar valor não suportado, a API retorna erro de configuração ao resolver dependency.
- QR code não aparece:
	- valide se `WHATSAPP_API_URL` e `WHATSAPP_API_KEY` estão corretos para o backend.
	- confira se o WAHA está online e respondendo em `/api/server/status`.
	- em WAHA CORE, apenas sessão `default` é suportada; múltiplos tenants podem conflitar.
- Webhook não recebe mensagens:
	- confirme `WHATSAPP_WEBHOOK_URL` acessível pelo container WAHA.
	- valide se o evento inclui `session`/`instance` e se a sessão existe no banco.
	- confirme se `WHATSAPP_WEBHOOK_HMAC_KEY` (quando habilitado) está igual nos dois lados.

### Análise (LLM)
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/leads/{id}/analyze` | Análise individual (com lock) |
| POST | `/leads/analyze-all` | Análise em lote dos leads ativos |

### Dashboard
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/leads` | Lista leads com filtros, ordenação e paginação |
| GET | `/leads/{id}` | Detalhe do lead + última análise + tempo de conversa |
| GET | `/leads/{id}/messages` | Histórico de mensagens paginado |
| PATCH | `/leads/{id}/status` | Alterar status (converted/lost) |
| PATCH | `/leads/{id}/stage` | Override manual da etapa do funil |
| GET | `/dashboard/stats` | Volumetrias agregadas |
| GET | `/whatsapp/status` | Status da sessão WhatsApp |
| GET | `/health` | Health check |

## Testes

```bash
# Rodar todos os testes
pytest tests/ -v

# Rodar testes de um módulo específico
pytest tests/test_auth.py -v
 
# Popular o banco com dados de teste para o frontend (seed E2E)
PYTHONPATH=. python3 frontend/tests/scripts/seed_e2e.py
# (Execute este comando a partir da raiz do projeto para evitar erro de importação do módulo app)

# Rodar testes Playwright do frontend
cd frontend
npx playwright test
# (Os testes Playwright devem ser executados dentro da pasta frontend/)
```

**79 testes** cobrindo: models, auth, webhook, análise LLM (com mock), dashboard, locks de concorrência e watchdog anti-zombie.

## Roadmap

- [x] Fase 0 — Scaffolding e infraestrutura
- [x] Fase 1 — Modelagem de dados
- [x] Fase 2 — Autenticação e onboarding
- [x] Fase 3 — Ingestão de dados (webhook)
- [x] Fase 4 — Motor de inteligência (LLM)
- [x] Fase 5 — API do dashboard
- [ ] Fase 6 — Integração WhatsApp (QR Code, Waha/Evolution API)
- [x] Fase 7 — Frontend Next.js
- [ ] Fase 8 — Hardening e deploy

## Licença

Projeto privado.
