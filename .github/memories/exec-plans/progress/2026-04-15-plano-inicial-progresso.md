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

### Fase 7 — Frontend: Dashboard e Interação
- Next.js 16 + TypeScript + Tailwind CSS + shadcn/ui
- Páginas de auth: `/login` e `/register` com seleção de template de funil
- Layout autenticado com sidebar (Dashboard, Leads, Configurações) e header mobile
- Dashboard (`/dashboard`): cards de volumetria (ativos, convertidos, perdidos, temperatura média) + Kanban por etapa do funil
- Lista de leads (`/leads`): tabela com filtros por etapa, busca por nome/telefone, ordenação por temperatura, ações rápidas (analisar, converter, descartar)
- Detalhe do lead (`/leads/[id]`): resumo IA, dicas qualitativas, resposta sugerida, override manual de etapa, histórico de mensagens (chat bubble), botão "Responder" via `wa.me/`
- Configurações (`/settings`): edição do funil com aplicação de templates e adição/remoção de etapas
- Banner de status WhatsApp (soft warning se desconectado) + indicador no sidebar
- Botões "Atualizar Análise" individual e "Analisar Todos" com loading states e tratamento de erro 409
- Confirmação via Dialog para ações de status (convertido/perdido)
- CORS configurado no backend (`CORS_ORIGINS` em Settings)
- API client centralizado em `frontend/src/lib/api.ts`
- AuthContext com JWT persistido em localStorage
- **79 testes acumulados** (backend — sem testes frontend nesta fase)

---

## 📈 Status Atual
- **79 testes passando** (0 falhas)
- Python 3.14.3 / pyenv virtualenv `gestor-leads`
- Backend 100% funcional (fases 0-5)
- Frontend 100% funcional (fase 7)
- CORS configurado no backend
- Próximas fases: 6 (integração WhatsApp real), 8 (hardening/deploy)

## 🐛 Bugs Conhecidos / Débitos Técnicos
- `passlib` incompatível com `bcrypt>=5.0` — fixado pinando `bcrypt==4.2.1`
- SQLAlchemy `default` em `mapped_column` não aplica em construção Python (apenas em INSERT) — testes unitários ajustados
- Análise em lote (`analyze-all`) cria sessões DB independentes por lead — funcional mas pode precisar de ajuste para uso real com PostgreSQL

## 🗺️ Roadmap
- [ ] Fase 6 — Integração WhatsApp (QR Code, Waha/Evolution API)
- [x] Fase 7 — Frontend Next.js (Dashboard, Kanban, detalhes, resposta)
- [ ] Fase 8 — Hardening (rate limit, CORS, logging, deploy)

## Changelog — Redesign Visual Frontend (Fase 7)

- Redesign completo do frontend Next.js seguindo padrão SaaS enterprise minimalista (Nordic, alto contraste, responsivo, suporte nativo a Light/Dark mode).
- Atualização de todos os cards, tabelas, badges, botões e containers para o novo design system (Tailwind + shadcn/ui).
- Inclusão de Skeleton Loaders elegantes para todos os estados de carregamento (substituindo spinners genéricos).
- Toggle de tema (Sol/Lua) minimalista no header da sidebar e header mobile.
- Garantia de preservação total da lógica de negócio, hooks e chamadas de API.
- Nenhuma alteração em endpoints, lógica backend ou contratos de API.
- Nenhum teste backend quebrado (79 testes passando).

### Validação Completa do Frontend (2026-04-19)

- Todos os endpoints principais do frontend foram testados manualmente via `curl` após refatoração e correção de imports/build:
  - `/dashboard`
  - `/leads`
  - `/settings`
  - `/onboarding`
  - `/register`
  - `/login`
- Critério de sucesso: resposta HTTP 200 OK e renderização correta da interface (formulários, tabelas, onboarding, etc).
- Todos os erros de build, dependências e imports foram corrigidos durante o processo.
- Progresso e procedimentos registrados também em `.github/instructions/copilot-instructions.md`.
