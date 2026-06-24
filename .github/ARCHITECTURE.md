# Arquitetura e Contexto do Gestor de Leads do WhatsApp

## 1. Visão Geral

- **Propósito:** Micro SaaS para triagem e gestão de leads via WhatsApp, usando LLM para classificar leads, gerar resumos e sugerir respostas, focando vendedores nas melhores oportunidades.
- **Stack:**
  - **Backend:** Python 3.11+, FastAPI, SQLAlchemy async, PostgreSQL, LiteLLM
  - **Frontend:** Next.js 16, React 19, Tailwind CSS, shadcn/ui, next-themes
  - **Infra:** Docker Compose

## 2. Estrutura de Pastas

```text
app/
    core/              # Configuração, database, segurança
    models/            # Modelos ORM (Tenant, User, Lead, Message, Analysis, WhatsAppSession)
    providers/         # Contratos/factory/adapters de integrações externas (WhatsApp, etc.)
    routers/           # Rotas FastAPI (auth, tenants, whatsapp, webhooks, analysis, dashboard)
    schemas/           # Schemas Pydantic (validação e resposta)
    services/          # Lógica de negócio (análise, auth, webhooks, sessão WhatsApp, funil)
frontend/
    src/app/           # Páginas Next.js (dashboard, leads, onboarding, settings, login, register)
    src/components/    # Componentes de aplicação e UI
    src/components/ui/ # Base visual shadcn/ui + componentes customizados do design system
    src/lib/           # API client, contextos, utilitários
    tests/             # Scripts utilitários de seed/validação manual
tests/                 # Testes backend unitários e integração (pytest)
.github/
    AGENTS.md          # Guia de comportamento dos agentes
    copilot-instructions.md
    memories/          # Decisões, padrões, troubleshooting, planos de execução
    rfcs/              # Mudanças formais e padrões arquiteturais
    skills/            # Skills por domínio
.prompts/
    frontend.md
    redesign-frontend/
```

## 3. Backend

### 3.1 Modelos Principais

- **Tenant:** Empresa/usuário, com configuração de funil.
- **User:** Usuário autenticado, vinculado a um tenant.
- **WhatsAppSession:** Sessão de conexão com WhatsApp.
- **Lead:** Lead captado, com status, etapa, score, lock de processamento.
- **Message:** Mensagens trocadas com o lead.
- **Analysis:** Resultado da análise da LLM (score, etapa, resumo, dicas, sugestão de resposta).

### 3.2 Rotas e Serviços

- **Auth:** Registro, login, JWT, multi-tenant.
- **Tenants:** CRUD e configuração de funil dinâmico.
- **Webhooks:** Recebe eventos do WhatsApp, cria leads e armazena mensagens.
- **WhatsApp Session:**
    - `/whatsapp/connect`: inicia/recupera sessão do tenant (provider-agnóstico).
    - `/whatsapp/qrcode`: retorna QR code atual para conexão.
    - `/whatsapp/status`: sincroniza e retorna estado da sessão.
    - `WhatsAppSessionService`: orchestration agnóstico a provider.
    - `app/providers/whatsapp/`: contrato (`interface.py`), factory (`factory.py`), adapters WAHA (`waha.py`) e Evolution API (`evolution.py`).
- **Analysis:**
    - `/leads/{id}/analyze`: análise individual de lead com lock otimista, chamada LLM, parsing e persistência.
    - `/leads/analyze-all`: análise em lote com controle de concorrência (semaphore para chamadas LLM).
    - Endpoints de análise protegidos por rate limit por tenant/rota para evitar abuso de custo e saturação de chamadas LLM.
- **Dashboard:** listagem, filtros, estatísticas e detalhamento de leads.

Tarefas em background no ciclo de vida da API:
- **Watchdog de análise:** reseta locks presos (`is_processing`) periodicamente.
- **Sync de sessão WhatsApp:** sincroniza status das sessões no provider para manter consistência do estado local.
- **Logging estruturado:** logs da API podem ser emitidos em JSON (`LOG_JSON=true`) para observabilidade em ambiente dev.

### 3.3 Concorrência e Locks

- **is_processing:** coluna booleana no Lead para evitar double submit.
- **Watchdog:** reseta locks travados há mais de 5 minutos.
- **Sync de sessão WhatsApp:** loop periódico para reconciliar status (`PENDING`, `QR_CODE_READY`, `CONNECTED`, etc.) entre provider e banco local.
- **Validação:** respostas da LLM validadas via Pydantic.

## 4. Frontend

### 4.1 Páginas Principais

- **Dashboard:** KPIs, priorização visual de leads e padrão `Sliding Master-Detail` para lista + detalhe.
- **Leads:** lista detalhada, análise individual/lote, alteração de status e filtros segmentados.
- **Lead Detail:** detalhe do lead, histórico de mensagens, análises da LLM e alteração manual de etapa/status.
- **Onboarding:** seleção de template de funil e configuração inicial.
- **Settings:** edição do funil e aplicação de templates.
- **Auth Pages:** login, cadastro e redirecionamento inicial com tratamento de hidratação.

### 4.2 Design System e Componentes UI

- Base visual derivada de shadcn/ui com redesign formalizado em [RFC 002](rfcs/002-frontend-redesign.md).
- Componentes-base atualizados: `button`, `card`, `input`, `table`, `select`, `dialog`.
- Componentes customizados relevantes:
  - `temperature-badge.tsx`
  - `segmented-tabs.tsx`
  - `preloader.tsx`
  - `AppWithPreloader.tsx`
- Tema com `next-themes`, suporte a light/dark e tokens globais em `frontend/src/app/globals.css`.

### 4.3 API Client

- `frontend/src/lib/api.ts` centraliza autenticação, CRUD de leads, análise, configuração de funil e utilitários de request.
- Usa JWT salvo no `localStorage`.
- `frontend/src/lib/auth-context.tsx` faz bootstrap client-side do token e resolve o estado autenticado.

### 4.4 Validação Atual de Frontend

- Não existe suíte E2E automatizada ativa no frontend neste momento.
- `frontend/tests/` contém scripts utilitários para seed e validação manual.
- Validação obrigatória de frontend:
  - execução via Docker Compose
  - navegação no Integrated Browser do VS Code
  - inspeção de logs com `docker compose logs -f frontend`
  - checagem técnica com lint e type-check

## 5. Convenções para IA

- **Leia primeiro:** `.github/AGENTS.md`, `.github/copilot-instructions.md`, este arquivo e as RFCs relevantes.
- **Frontend:** seguir [RFC 002](rfcs/002-frontend-redesign.md) para decisões visuais e de validação.
- **Skills:** carregar skills relevantes de `.github/skills/` conforme o domínio.
- **Memória:** usar `.github/memories/` para registrar decisões, padrões, troubleshooting e planos.
- **Planos de execução:** consultar `.github/memories/exec-plans/PLAN-INDEX.md`.
- **Documentação:** atualizar RFCs, arquitetura e memórias quando o comportamento real do sistema mudar.

## 6. Fluxos Críticos

- **Onboarding:** cadastro → seleção de template de funil → início da operação.
- **Ingestão:** webhook recebe mensagem → cria lead se novo → armazena mensagem.
- **Integração WhatsApp (Provider-agnóstica):** usuário inicia conexão → backend cria sessão no provider ativo (WAHA ou Evolution) → frontend busca QR code → provider envia eventos via webhook → backend valida HMAC e persiste mensagens.
- **Seleção de Provider:** backend resolve provider via `WHATSAPP_PROVIDER` (`waha` ou `evolution`) na factory, sem alterar endpoints públicos.
- **Análise:** botão de análise → lock otimista → chamada LLM → parsing → persistência → unlock.
- **Dashboard:** exibe leads priorizados, agrupamento visual por contexto comercial e KPIs.
- **Gestão Manual:** usuário pode alterar etapa/status manualmente, sobrescrevendo inferência da IA.
- **Autenticação Frontend:** token em `localStorage` → `auth-context` resolve sessão → layout autenticado protege rotas.

## 7. Diagramas

### Diagrama de Módulos

```mermaid
flowchart TD
    subgraph Backend
        A[API FastAPI] --> B[Services]
        B --> C[Models/ORM]
        B --> D[LLM Integration]
        A --> E[Webhooks]
    end
    subgraph Frontend
        F[Next.js App]
        F --> G[Pages and Components]
        F --> H[API Client and Auth Context]
    end
    A <--> F
```

### Fluxo de Autenticação

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    User->>Frontend: Preenche cadastro/login
    Frontend->>Backend: POST /auth/register ou /auth/login
    Backend-->>Frontend: JWT Token
    Frontend->>Frontend: Salva token no localStorage
    Frontend->>Backend: Requisições autenticadas com JWT
    Backend-->>Frontend: Dados protegidos
```

### Relacionamento de Entidades

```mermaid
erDiagram
    TENANT ||--o{ USER : possui
    TENANT ||--o{ LEAD : possui
    LEAD ||--o{ MESSAGE : possui
    LEAD ||--o{ ANALYSIS : possui
    TENANT ||--o{ WHATSAPP_SESSION : possui
    USER }o--|| TENANT : pertence
```

### Providers WhatsApp (Arquitetura Desacoplada)

```mermaid
flowchart TD
    classDef app fill:#2e7d32,stroke:#1b5e20,color:#fff
    classDef factory fill:#e65100,stroke:#bf360c,color:#fff
    classDef adapter fill:#1565c0,stroke:#0d47a1,color:#fff
    classDef protocol fill:#6a1b9a,stroke:#4a148c,color:#fff

    subgraph Routers["Routers"]
        R1[whatsapp.py]:::app
        R2[webhooks.py]:::app
    end

    SVC[WhatsAppSessionService]:::app
    FAC["Factory<br/>get_whatsapp_provider<br/>WHATSAPP_PROVIDER = waha | evolution"]:::factory
    WAHA["WahaWhatsAppProvider<br/>waha.py"]:::adapter
    EVO["EvolutionWhatsAppProvider<br/>evolution.py"]:::adapter
    PROTO["WhatsAppProvider Protocol<br/>interface.py"]:::protocol

    Routers -->|"Depends"| FAC
    SVC -->|"provider param"| FAC
    FAC --> WAHA
    FAC --> EVO
    WAHA -->|implements| PROTO
    EVO -->|implements| PROTO
```

**Protocol `WhatsAppProvider`** define o contrato agnóstico:
- `resolve_session_id(tenant_id)` — gera session_id para tenant
- `create_session(db, tenant_id, session_id)` — cria sessão no provider
- `fetch_qr_code(session_id)` — obtém QR code
- `fetch_session_status(session_id)` — consulta status
- `stop_session(session_id)` — encerra sessão
- `normalize_webhook_payload(payload)` — normaliza webhook para formato interno

**Providers suportados:**
| Provider | Config (`WHATSAPP_PROVIDER`) | Multi-tenant | Session ID Format |
|----------|:---:|:---:|---|
| WAHA | `waha` | CORE: 1 sessão (`default`), PLUS: múltiplas | `default` ou `tenant-{uuid}` |
| Evolution API | `evolution` | Ilimitadas instâncias | `tenant-{uuid}` |

### Integração WhatsApp (QR + Webhook)

```mermaid
sequenceDiagram
    participant U as Usuário
    participant FE as Frontend
    participant BE as Backend
    participant PF as Provider Factory
    participant WA as WhatsApp Provider (WAHA ou Evolution)

    U->>FE: Clicar em conectar WhatsApp
    FE->>BE: POST /whatsapp/connect
    BE->>PF: Resolve provider (WHATSAPP_PROVIDER)
    PF-->>BE: Adapter instance
    BE->>WA: Cria sessão/instância
    WA-->>BE: session_id/status
    FE->>BE: GET /whatsapp/qrcode
    BE->>WA: Fetch QR code
    WA-->>BE: qrCode (base64)
    BE-->>FE: qr_code
    WA->>BE: Webhook (message event)
    BE->>BE: provider.normalize_webhook_payload()
    BE->>BE: Valida HMAC + session_id + tenant
    BE->>BE: Persiste Lead/Message
```

Estados de sessão mapeados no backend:
- `PENDING`
- `QR_CODE_READY`
- `CONNECTING`
- `CONNECTED`
- `DISCONNECTED`
- `ERROR`

Observação de infraestrutura:
- WAHA CORE suporta somente sessão `default` (sessão única). Para multi-tenant: WAHA PLUS.
- Evolution API suporta múltiplas instâncias em 1 container (ideal para multi-tenant).

Notas operacionais da Evolution API (v2.3.7):
- Endpoint correto de status de instância: `GET /instance/connectionState/{instanceName}`.
- Não usar `GET /instance/fetch/{instanceName}` para status (retorna 404 nas versões atuais).
- Webhook entre containers deve usar hostname de serviço Docker (`backend`) e nunca `localhost`.
- Quando o backend expõe um único endpoint (`/webhooks/whatsapp`), manter `webhook_by_events=false`.
- Referência rápida para troubleshooting: https://docs.evolutionfoundation.com.br/llms.txt

### Infraestrutura Docker Compose

O `docker-compose.yml` sobe os seguintes serviços:

| Serviço | Imagem | Porta | Descrição |
|---------|--------|-------|-----------|
| `db` | `postgres:16-alpine` | `5432` | PostgreSQL compartilhado — cria os bancos `leads` (backend) e `evolution_db` (Evolution API) |
| `backend` | build local | `8000` | FastAPI + Alembic |
| `evolution-api` | `evoapicloud/evolution-api:v2.3.7` | `3000 -> 8080` | Gerenciador de instâncias WhatsApp |

Observação: o serviço `frontend` está versionado no `docker-compose.yml`, porém atualmente comentado para uso opcional no fluxo local.

**Dois bancos no mesmo PostgreSQL:**
- `leads` — banco da aplicação (backend + Alembic)
- `evolution_db` — banco da Evolution API (Prisma)

O banco `evolution_db` é criado pelo script `init-db.sh` montado em `/docker-entrypoint-initdb.d/`, que só executa na **primeira inicialização do volume**. Para recriar: `docker compose down -v`.

**Alias de rede `postgres` no serviço `db`:**
A imagem `evoapicloud/evolution-api` carrega um `.env` interno com `DATABASE_CONNECTION_URI=postgresql://...@postgres:5432/...` hardcoded via Prisma, que sobrescreve variáveis de ambiente externas. O serviço `db` expõe o alias de rede `postgres` para que o hostname resolva corretamente dentro da rede Docker.

**Variáveis de ambiente da Evolution API (formato correto v2):**
```
DATABASE_PROVIDER=postgresql
DATABASE_CONNECTION_URI=postgresql://user:pass@postgres:5432/evolution_db?schema=evolution_api
AUTHENTICATION_API_KEY=<chave>
WEBHOOK_GLOBAL_ENABLED=true
WEBHOOK_GLOBAL_URL=<url>
```
> Não usar `DATABASE_CONNECTION__HOST/PORT/USER` (formato incorreto) nem `APIKEY__GLOBAL_APIKEY` ou `WEBHOOK__GLOBAL__*` (double-underscore não é reconhecido pela v2).

## 8. RFCs

- [001 - Padrão de Serviços](rfcs/001-padrao-servicos.md)
- [002 - Frontend Redesign](rfcs/002-frontend-redesign.md)

## 9. Referências Rápidas

- `.github/AGENTS.md`
- `.github/copilot-instructions.md`
- `.github/memories/exec-plans/PLAN-INDEX.md`
- `.github/rfcs/`
- `.github/skills/`
- `.prompts/frontend.md`
- `.prompts/redesign-frontend/`
- https://docs.evolutionfoundation.com.br/llms.txt

## 10. Atualização Obrigatória

- Atualize este arquivo ao alterar estrutura, fluxos, dependências, protocolo de validação ou RFCs vigentes.
- Sempre revise as RFCs relacionadas ao propor mudanças estruturais ou visuais significativas.
