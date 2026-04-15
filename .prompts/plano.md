# 📋 Plano de Implementação — Gestor de Leads do WhatsApp

Baseado no PRD em `prd.md`. Cada fase entrega valor incremental e testável.

---

## Fase 0 — Scaffolding e Infraestrutura Base

**Objetivo:** Projeto rodando localmente com Docker, CI verde e estrutura de pastas definida.

| # | Tarefa | RFs/RNFs |
|---|--------|----------|
| 0.1 | Criar estrutura do backend FastAPI (`app/`, `app/models/`, `app/schemas/`, `app/services/`, `app/routers/`, `app/core/`) | — |
| 0.2 | Configurar `pyproject.toml` / `requirements.txt` com dependências iniciais (fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, alembic, pydantic-settings, litellm, pytest, pytest-asyncio, httpx) | — |
| 0.3 | Criar `Dockerfile` e `docker-compose.yml` (backend + PostgreSQL + volume de hot-reload) | — |
| 0.4 | Configurar Alembic para migrations async com PostgreSQL | — |
| 0.5 | Criar `app/core/config.py` (Settings via pydantic-settings: DATABASE_URL, LLM_API_KEY, WHATSAPP_WEBHOOK_SECRET) | — |
| 0.6 | Criar `app/core/database.py` (engine async, SessionLocal, Base declarativa) | — |
| 0.7 | Configurar `tests/conftest.py` com fixtures (AsyncClient, SQLite in-memory, override de deps) | — |
| 0.8 | Scaffold do frontend Next.js com Tailwind CSS e shadcn/ui em `frontend/` | — |

**Critério de Saída:** `docker compose up` sobe backend + DB; `pytest tests/ -v` passa; frontend roda em `localhost:3000`.

---

## Fase 1 — Modelagem de Dados e Multi-Tenancy

**Objetivo:** Tabelas criadas, migrations funcionando, CRUD básico de tenant/usuário.

| # | Tarefa | RFs/RNFs |
|---|--------|----------|
| 1.1 | Model `Tenant` (id, name, funnel_config JSON, created_at) | RF02 |
| 1.2 | Model `User` (id, tenant_id FK, email, hashed_password, created_at) | — |
| 1.3 | Model `WhatsAppSession` (id, tenant_id FK, status enum [connected, disconnected], connected_at) | RF01 |
| 1.4 | Model `Lead` (id, tenant_id FK, phone, name, status enum [active, converted, lost], current_stage, temperature_score, is_processing, processing_started_at, created_at, updated_at) | RF04, RF06, RF14 |
| 1.5 | Model `Message` (id, lead_id FK, direction enum [inbound, outbound], content text, timestamp) | RF04 |
| 1.6 | Model `Analysis` (id, lead_id FK, temperature_score, current_stage, conversation_summary, qualitative_tips, suggested_reply, created_at) | RF07 |
| 1.7 | Gerar migration inicial via Alembic e aplicar | — |
| 1.8 | Testes unitários dos models e relacionamentos | — |

**Critério de Saída:** `alembic upgrade head` cria todas as tabelas; testes de model passam.

---

## Fase 2 — Autenticação e Onboarding

**Objetivo:** Usuário se cadastra, faz login (JWT) e configura o tenant com funil inicial.

| # | Tarefa | RFs/RNFs |
|---|--------|----------|
| 2.1 | Router `POST /auth/register` — cria User + Tenant, retorna JWT | RF02 |
| 2.2 | Router `POST /auth/login` — autentica e retorna JWT | — |
| 2.3 | Middleware de autenticação JWT (dependency `get_current_user`) | RNF03 |
| 2.4 | Router `PUT /tenants/me/funnel` — atualiza funnel_config JSON | RF02 |
| 2.5 | Templates de funil pré-definidos (service com 3-4 opções padrão) | RF02 |
| 2.6 | Testes de integração HTTP para auth e onboarding | — |

**Critério de Saída:** Fluxo register → login → configurar funil funcional e testado.

---

## Fase 3 — Ingestão de Dados (Webhook do WhatsApp)

**Objetivo:** Mensagens do WhatsApp são recebidas, validadas e persistidas.

| # | Tarefa | RFs/RNFs |
|---|--------|----------|
| 3.1 | Router `POST /webhooks/whatsapp` — recebe evento `message.upsert` | RF03 |
| 3.2 | Validação de assinatura/secret do webhook (header HMAC) | RF03, RNF03 |
| 3.3 | Service `ingest_message` — lógica: se lead não existe cria com status `active`; se lead `converted`/`lost` descarta; persiste Message | RF04 |
| 3.4 | Schema Pydantic para payload do webhook (compatível com Waha/Evolution API) | RF03 |
| 3.5 | Testes unitários do service `ingest_message` (cenários: novo lead, lead ativo, lead descartado) | — |
| 3.6 | Testes de integração do endpoint webhook | — |

**Critério de Saída:** Webhook recebe payload simulado → lead e mensagem persistidos; payloads de leads inativos são descartados.

---

## Fase 4 — Motor de Inteligência (LLM)

**Objetivo:** Análise de lead via LLM com controle de concorrência robusto.

| # | Tarefa | RFs/RNFs |
|---|--------|----------|
| 4.1 | Service `analyze_lead` — monta prompt com: funil do tenant, histórico de mensagens, instruções de output JSON | RF07 |
| 4.2 | Integração com `litellm` para chamada agnóstica à LLM | RF07 |
| 4.3 | Parsing e validação do JSON de resposta da LLM (schema Pydantic) | RF07 |
| 4.4 | Optimistic Lock: `acquire_lock` (UPDATE ... WHERE is_processing = false RETURNING id) | RF06, RF06.1 |
| 4.5 | Anti-Zombie: try/finally para liberar lock em qualquer cenário | RF06.2 |
| 4.6 | Router `POST /leads/{id}/analyze` — análise individual com lock | RF05, RF06.1 |
| 4.7 | Router `POST /leads/analyze-all` — dispara análise em lote (asyncio.gather com semáforo) | RF05 |
| 4.8 | Persistir resultado em `Analysis` e atualizar `Lead.temperature_score` e `Lead.current_stage` | RF07 |
| 4.9 | Background task: Watchdog de timeout (leads com `is_processing=true` há >5min → reset + log) | RF06.3 |
| 4.10 | Testes unitários com mock da LLM (resposta válida, resposta inválida, timeout) | — |
| 4.11 | Testes de integração: lock, double-submit 409, zombie reset | — |

**Critério de Saída:** Análise individual e em lote funcionam; double-submit retorna 409; zombie lock é liberado automaticamente.

---

## Fase 5 — API do Dashboard (Leitura e Gestão)

**Objetivo:** Todos os endpoints necessários para o frontend consumir.

| # | Tarefa | RFs/RNFs |
|---|--------|----------|
| 5.1 | Router `GET /leads` — lista leads ativos do tenant com filtros (stage, score range), ordenação por score desc, paginação | RF09, RF10, RNF04 |
| 5.2 | Router `GET /leads/{id}` — detalhe do lead com última análise e tempo de conversa calculado | RF11, RF12 |
| 5.3 | Router `GET /leads/{id}/messages` — histórico de mensagens paginado | RF12 |
| 5.4 | Router `PATCH /leads/{id}/status` — altera status para converted/lost (human override) | RF14 |
| 5.5 | Router `PATCH /leads/{id}/stage` — override manual da etapa do funil | §4.2 Controle Soberano |
| 5.6 | Router `GET /dashboard/stats` — volumetrias agregadas (leads por etapa, por status, média de score) | RF10, RNF04 |
| 5.7 | Router `GET /whatsapp/status` — retorna status da sessão WhatsApp do tenant | RNF01 |
| 5.8 | Testes de integração para todos os endpoints | — |

**Critério de Saída:** Todos os endpoints retornam dados corretos; queries otimizadas com índices adequados.

---

## Fase 6 — Integração WhatsApp (QR Code e Status)

**Objetivo:** Conexão real com WhatsApp via Waha/Evolution API.

| # | Tarefa | RFs/RNFs |
|---|--------|----------|
| 6.1 | Adicionar Waha (ou Evolution API) ao `docker-compose.yml` | — |
| 6.2 | Service `whatsapp_session` — criar sessão, obter QR code, verificar status | RF01 |
| 6.3 | Router `POST /whatsapp/connect` — inicia sessão e retorna QR code | RF01 |
| 6.4 | Router `GET /whatsapp/qrcode` — retorna QR code atual | RF01 |
| 6.5 | Configurar webhook da API WhatsApp apontando para `POST /webhooks/whatsapp` | RF03 |
| 6.6 | Teste end-to-end com sessão simulada | — |

**Critério de Saída:** QR code gerado, sessão conectável, webhook recebendo mensagens reais.

---

## Fase 7 — Frontend: Dashboard e Interação

**Objetivo:** Interface completa e funcional consumindo a API.

| # | Tarefa | RFs/RNFs |
|---|--------|----------|
| 7.1 | Páginas de auth (login/register) com formulários shadcn/ui | RF02 |
| 7.2 | Layout autenticado com sidebar (Dashboard, Leads, Configurações) | — |
| 7.3 | Tela de Onboarding — QR Code + configuração de funil | RF01, RF02 |
| 7.4 | Dashboard principal — cards de volumetria + visão Kanban por etapa do funil | RF09, RF10 |
| 7.5 | Lista de leads com ordenação por temperatura, filtros por etapa e busca | RF09, RF10 |
| 7.6 | Detalhe do lead — resumo IA, dicas qualitativas, tempo de conversa, histórico de mensagens | RF11, RF12 |
| 7.7 | Botão "Atualizar Análise" individual + "Atualizar Todos" com loading states e tratamento de erro/409 | RF05, RF08 |
| 7.8 | Botão "Responder" com redirect `wa.me/{phone}?text={suggested_reply}` | RF13 |
| 7.9 | Ações de status: marcar como convertido/descartado com confirmação | RF14 |
| 7.10 | Override manual da etapa do funil (dropdown) | §4.2 |
| 7.11 | Banner de status da conexão WhatsApp (soft warning se desconectado) | RNF01 |
| 7.12 | Tela de configurações — edição do funil JSON | RF02 |

**Critério de Saída:** Fluxo completo do usuário funcional: onboarding → dashboard → análise → resposta.

---

## Fase 8 — Hardening e Preparação para Produção

**Objetivo:** Segurança, observabilidade e deploy.

| # | Tarefa | RFs/RNFs |
|---|--------|----------|
| 8.1 | Rate limiting no webhook e endpoints de análise | RNF02, RNF03 |
| 8.2 | CORS configurado corretamente (domínio da Vercel) | — |
| 8.3 | Logging estruturado (JSON logs com contexto de tenant/lead) | RF06.3 |
| 8.4 | Health check endpoint (`GET /health`) | — |
| 8.5 | Variáveis de ambiente documentadas em `.env.example` | — |
| 8.6 | Docker Compose de produção (sem hot-reload, multi-stage build) | — |
| 8.7 | Deploy do backend (EC2/ECS/Render) | — |
| 8.8 | Deploy do frontend (Vercel) | — |
| 8.9 | Smoke test end-to-end em ambiente de staging | — |

**Critério de Saída:** Sistema rodando em produção com logs, rate limit e monitoramento básico.

---

## Ordem de Execução Recomendada

```
Fase 0 → Fase 1 → Fase 2 → Fase 3 → Fase 4 → Fase 5 → Fase 6 → Fase 7 → Fase 8
         ├─────────────────── Backend ──────────────────┤
                                                         ├── Integração ──┤
                                                                          ├─ Frontend ─┤
```

As fases 0–5 são puramente backend e podem ser implementadas e testadas sem frontend.
A fase 6 requer o serviço WhatsApp (Waha/Evolution) rodando.
A fase 7 (frontend) pode iniciar em paralelo a partir da fase 5, quando a API estiver estável.

---

## Dependências Externas

| Dependência | Quando necessária |
|---|---|
| PostgreSQL | Fase 0 (via Docker) |
| Waha ou Evolution API | Fase 6 |
| Chave de API LLM (OpenAI/Anthropic/Google) | Fase 4 |
| Domínio + Vercel | Fase 8 |
