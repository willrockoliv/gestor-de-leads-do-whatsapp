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

### Fase 7 — Frontend: Dashboard e Interação (MVP)
- Next.js 16 + TypeScript + Tailwind CSS + shadcn/ui
- Páginas de auth: `/login` e `/register` com seleção de template de funil
- Layout autenticado com sidebar (Dashboard, Leads, Configurações) e header mobile
- Dashboard: cards de volumetria + Kanban por etapa do funil
- Lista de leads: tabela com filtros, busca, ordenação por temperatura
- Detalhe do lead: resumo IA, resposta sugerida, histórico de mensagens
- Configurações: edição do funil com templates
- CORS configurado no backend
- API client centralizado em `frontend/src/lib/api.ts`
- AuthContext com JWT em localStorage
- **79 testes acumulados** (backend)

### Fase 7B — Redesign Visual Frontend (Nordic Minimalist)

**Design System & Componentes Novos:**
- Sistema de cores Nordic Minimalist:
  - Light: slate-50 background, slate-950 text
  - Dark: #0B1120 background, slate-50 text
  - Accents: teal-500 (primary), blue-500 (secondary)
  - Fontes: Inter/system stack (sem Geist Google Fonts)
- Componentes novos: `temperature-badge.tsx` (indicador semântico hot/warm/cold com ícones), `segmented-tabs.tsx` (filtro com contadores)
- Base components atualizados: button, card, input, dialog para nova linguagem visual
- Skeleton loaders elegantes para todos os estados de carregamento
- Toggle de tema (Sol/Lua) minimalista no header

**Padrões de Layout & Interação:**
- Sliding Master-Detail na dashboard (42% lista / 58% detalhe, animação suave)
- Responsive: collapsa para single-column em mobile
- Documentado em `.github/rfcs/002-frontend-redesign.md`

**Fixes de Hidratação & SSR/CSR:**
- `auth-context.tsx`: inicialização de token em state initializer (sem useEffect)
- `AppWithPreloader.tsx`: remoção de overlay global, alinhamento root fallback
- `globals.css`: remoção de Google Fonts, adição de explicit font stacks e hide-scrollbar utility

**Infraestrutura:**
- Remoção de suite Playwright E2E (deprecada, substituída por validação manual)
- Docker Compose obrigatório para frontend: `docker compose exec frontend npm run ...`
- Validação via Integrated Browser do VS Code em http://localhost:3000
- Manual validation protocol: navegação por todas as telas após mudanças de UI/SSR/CSR
- Credenciais padrão: `teste@teste.com` / `123456`
- Seed E2E: `PYTHONPATH=. python3 frontend/tests/scripts/seed_e2e.py` a partir da raiz

**Validação Completa (2026-04-19 a 2026-04-23):**
- Todas as 7 páginas refatoradas com Nordic Minimalist
- Todos os endpoints principais navegáveis via Integrated Browser
- Hidratação sincronizada (sem mismatches)
- Lint e type-check passando
- 79 testes backend ainda passando (zero regressões)
- Progresso e RFC documentados em `.github/rfcs/002-frontend-redesign.md` e `.github/ARCHITECTURE.md`

---

## 📈 Status Atual
- **79 testes passando** (0 falhas)
- Python 3.14.3 / pyenv virtualenv `gestor-leads`
- Backend 100% funcional (fases 0-5)
- Frontend 100% funcional com Nordic Minimalist visual (fases 7, 7B)
- CORS configurado no backend
- Infraestrutura: Docker Compose obrigatório, validação via Integrated Browser
- Próximas fases: 6 (integração WhatsApp real), 8 (hardening/deploy)

## 🐛 Bugs Conhecidos / Débitos Técnicos
- `passlib` incompatível com `bcrypt>=5.0` — fixado pinando `bcrypt==4.2.1`
- SQLAlchemy `default` em `mapped_column` não aplica em construção Python (apenas em INSERT) — testes unitários ajustados
- Análise em lote (`analyze-all`) cria sessões DB independentes por lead — funcional mas pode precisar de ajuste para uso real com PostgreSQL

## 🗺️ Roadmap
- [ ] Fase 6 — Integração WhatsApp (QR Code, Waha/Evolution API)
- [x] Fase 7 — Frontend Next.js (Dashboard, Kanban, detalhes, resposta)
- [ ] Fase 8 — Hardening (rate limit, CORS, logging, deploy)

## Referências & Documentação

- **RFC 002 — Frontend Redesign:** `.github/rfcs/002-frontend-redesign.md` — Define padrão Nordic Minimalist, Sliding Master-Detail layout, hidratação, manual validation protocol
- **ARCHITECTURE.md:** `.github/ARCHITECTURE.md` — Documenta design system, componentes, validação com Integrated Browser
- **copilot-instructions.md:** `.github/copilot-instructions.md` — Instruções para agentes: Docker Compose obrigatório, manual validation, seed E2E script
- **Progresso & Histórico:** Este arquivo + memórias em `.github/memories/exec-plans/`
