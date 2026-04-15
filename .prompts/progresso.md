# 📊 Progresso do Projeto

## ✅ Fases Concluídas

### Fase 0 — Scaffolding e Infraestrutura Base
- Estrutura de pastas: `app/core/`, `app/models/`, `app/schemas/`, `app/services/`, `app/routers/`, `tests/`
- `requirements.txt` com versões exatas (Python 3.14.3 via pyenv virtualenv `gestor-leads`)
- `Dockerfile` + `docker-compose.yml` (backend + PostgreSQL)
- `app/core/config.py` (pydantic-settings)
- `app/core/database.py` (SQLAlchemy async)
- `tests/conftest.py` (SQLite in-memory, AsyncClient)
- Alembic inicializado
- **1 teste**

### Fase 1 — Modelagem de Dados e Multi-Tenancy
- Models: `Tenant`, `User`, `WhatsAppSession`, `Lead`, `Message`, `Analysis`
- Enums: `LeadStatus`, `MessageDirection`, `SessionStatus`
- Testes unitários e de integração dos models
- **15 testes acumulados**

### Fase 2 — Autenticação e Onboarding
- `POST /auth/register` — cria User + Tenant com funil template
- `POST /auth/login` — JWT
- `GET /auth/me` — dados do usuário autenticado
- `GET /auth/funnel-templates` — templates disponíveis
- `PUT /tenants/me/funnel` — atualiza funil
- `GET /tenants/me` — dados do tenant
- Middleware JWT (`get_current_user`)
- 4 templates de funil pré-definidos (default, serviços, ecommerce, imobiliária)
- **27 testes acumulados**

### Fase 3 — Ingestão de Dados (Webhook do WhatsApp)
- `POST /webhooks/whatsapp` — recebe `message.upsert`
- Validação HMAC de assinatura (skip em dev)
- Service `ingest_message`: cria lead se novo, descarta se converted/lost
- Extração de texto de múltiplos tipos de mensagem (text, image, audio, video, document)
- **48 testes acumulados**

### Fase 4 — Motor de Inteligência (LLM)
- `POST /leads/{id}/analyze` — análise individual com lock
- `POST /leads/analyze-all` — análise em lote com semáforo
- Optimistic Lock via `UPDATE ... WHERE is_processing = false`
- Double-submit retorna HTTP 409
- Anti-Zombie: try/finally libera lock em qualquer cenário
- Watchdog background task (reset locks > 5min)
- Integração agnóstica via `litellm`
- Prompt builder com funil do tenant + histórico de mensagens
- Parser de resposta JSON da LLM com validação Pydantic
- **63 testes acumulados**

### Fase 5 — API do Dashboard (Leitura e Gestão)
- `GET /leads` — lista com filtros (status, stage, score), ordenação, paginação
- `GET /leads/{id}` — detalhe com última análise e tempo de conversa
- `GET /leads/{id}/messages` — histórico paginado
- `PATCH /leads/{id}/status` — alterar para converted/lost
- `PATCH /leads/{id}/stage` — override manual da etapa do funil
- `GET /dashboard/stats` — volumetrias agregadas
- `GET /whatsapp/status` — status da sessão WhatsApp
- **79 testes acumulados**

---

## 📈 Status Atual
- **79 testes passando** (0 falhas)
- Python 3.14.3 / pyenv virtualenv `gestor-leads`
- Backend 100% funcional (fases 0-5)
- Próximas fases: 6 (integração WhatsApp real), 7 (frontend), 8 (hardening/deploy)

## 🐛 Bugs Conhecidos / Débitos Técnicos
- `passlib` incompatível com `bcrypt>=5.0` — fixado pinando `bcrypt==4.2.1`
- SQLAlchemy `default` em `mapped_column` não aplica em construção Python (apenas em INSERT) — testes unitários ajustados
- Análise em lote (`analyze-all`) cria sessões DB independentes por lead — funcional mas pode precisar de ajuste para uso real com PostgreSQL
- Frontend não implementado ainda

## 🗺️ Roadmap
- [ ] Fase 6 — Integração WhatsApp (QR Code, Waha/Evolution API)
- [ ] Fase 7 — Frontend Next.js (Dashboard, Kanban, detalhes, resposta)
- [ ] Fase 8 — Hardening (rate limit, CORS, logging, deploy)
