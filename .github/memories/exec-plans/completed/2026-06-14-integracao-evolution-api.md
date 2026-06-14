# 🚀 Plano de Implementação — Integração Evolution API como Provider WhatsApp

**Objetivo:** Estender a arquitetura de desacoplamento de providers para suportar Evolution API, mantendo a aplicação agnóstica a providers externos via injeção de dependência.

**Dependências:** 
- Desacoplamento WAHA (Fase 6, completo) ✅
- Codebase atual com factory pattern implementado ✅

**Critério de Saída:** 
- Evolution API adapter implementado seguindo o Protocol
- Factory suporta ambos WAHA e Evolution API
- Testes validam ambos adapters sem regressão
- Docker Compose com Evolution API rodando
- Documentação atualizada (ARCHITECTURE.md, README.md)

---

## Contexto de Desacoplamento Atual

### Arquitetura Existente
```mermaid
flowchart TD
  subgraph BE ["FastAPI Backend"]
    SVC["WhatsAppSessionService"]
    RTR["Routers — Depends"]
    WH["Webhooks — normalize_webhook_payload"]
  end

  RTR --> FAC
  SVC --> FAC
  WH --> FAC

  FAC["Factory<br/>WHATSAPP_PROVIDER: waha | evolution"] --> PROTO["WhatsAppProvider Protocol"]

  PROTO --> WAHA["WahaWhatsAppProvider"]
  PROTO --> EVO["EvolutionWhatsAppProvider"]
```

### Contrato Protocol Atual (`interface.py`)

```python
class WhatsAppProvider(Protocol):
    async def resolve_session_id(self, tenant_id: UUID) -> str:
        """Resolve session ID for tenant (provider-specific logic)"""
        ...

    async def create_session(self, db: AsyncSession, tenant_id: UUID, session_id: str) -> None:
        """Create session in provider"""
        ...

    async def fetch_qr_code(self, session_id: str) -> str | None:
        """Fetch QR code for session"""
        ...

    async def fetch_session_status(self, session_id: str) -> ProviderSessionStatus:
        """Fetch session status and phone number"""
        ...

    async def stop_session(self, session_id: str) -> None:
        """Stop session in provider"""
        ...

    def normalize_webhook_payload(self, payload: dict) -> NormalizedWebhookMessage | None:
        """Normalize provider webhook payload to internal format"""
        ...
```

---

## Fases de Implementação

### Fase 1: Setup e Infraestrutura

#### 1.1 Adicionar Evolution API ao docker-compose.yml ✅ (FEITO)
- [x] Serviço `evolution-api` adicionado
- [x] Variáveis de ambiente configuradas
- [x] Banco `evolution_api` preparado no PostgreSQL

#### 1.2 Estender `.env.example` para Evolution API ✅
- [x] `EVOLUTION_API_URL` (ex: `http://evolution-api:8080`)
- [x] `EVOLUTION_API_KEY` (chave de autenticação global)
- [x] `EVOLUTION_WEBHOOK_URL` (ex: `http://backend:8000/webhooks/evolution`)
- [x] `WHATSAPP_PROVIDER` (padrão: `waha`, pode ser `evolution`)

#### 1.3 Atualizar `app/core/config.py` ✅
- [x] Carregar `EVOLUTION_API_URL` do env
- [x] Carregar `EVOLUTION_API_KEY` do env
- [x] Carregar `EVOLUTION_WEBHOOK_URL` do env
- [x] Carregar `WHATSAPP_PROVIDER` (default: "evolution")
- [x] Validação de configuração por provider ativo

---

### Fase 2: Adapter Evolution API

#### 2.1 Criar `app/providers/whatsapp/evolution.py` ✅
- [x] Classe `EvolutionWhatsAppProvider` implementando `WhatsAppProvider`
- [x] Métodos obrigatórios do Protocol:
  - `async resolve_session_id(tenant_id)` → formato `tenant-{tenant_id}`
  - `async create_session(db, tenant_id, session_id)` → POST `/instance/create`
  - `async fetch_qr_code(session_id)` → GET `/instance/connect`
  - `async fetch_session_status(session_id)` → GET `/instance/fetch`
  - `async stop_session(session_id)` → DELETE `/instance/logout`
  - `def normalize_webhook_payload(payload)` → normalizar evento `MESSAGES_UPSERT`
- [x] Retry/backoff logic (3 tentativas, exponential backoff)
- [x] Error handling (mapear erros Evolution para exceções do Protocol)
- [x] Logging sanitizado (sem PII, sem tokens)

#### 2.2 Requisitos de Implementação ✅
- [x] `resolve_session_id()`: gerar `tenant-{tenant_id}` (Evolution permite múltiplas)
- [x] `create_session()`: POST com webhook config, instance name = session_id
- [x] `fetch_qr_code()`: parse QR code em base64 ou URL
- [x] `fetch_session_status()`: mapear status Evolution → SessionStatus interno
  - `PENDING` → `PENDING`
  - `QR_CODE_READY` → `QR_CODE_READY`
  - `CONNECTING` → `CONNECTING`
  - `OPEN`/`CONNECTED` → `CONNECTED`
  - `CLOSED`/`DISCONNECTED` → `DISCONNECTED`
  - Outro → `ERROR`
- [x] `stop_session()`: DELETE /instance/logout
- [x] `normalize_webhook_payload()`: extrair fields do evento Evolution
  - Eventos: `MESSAGES_UPSERT`, `MESSAGES_UPDATE` → agrupar como `message.upsert` interno
  - Extrair: `instance` (session_id), `data.messages[0].key.remoteJid` (remote_jid), `pushName`, etc.

#### 2.3 Tratamento de Erro Específico Evolution ✅
- [x] Detectar conflitos/duplicatas (instância já existe — 409)
- [x] Detectar indisponibilidade do serviço (retry + WhatsAppProviderUnavailableError)
- [x] Retornar exceções mapeadas do Protocol (`WhatsAppProviderError`, etc.)

---

### Fase 3: Estender Factory

#### 3.1 Atualizar `app/providers/whatsapp/factory.py` ✅
- [x] Importar `EvolutionWhatsAppProvider`
- [x] Adicionar `"evolution"` ao dicionário `_SUPPORTED_PROVIDERS`
- [x] Factory continua agnóstica: resolve provider por `WHATSAPP_PROVIDER` env var
- [x] Mensagem de erro lista providers suportados se provider inválido

#### 3.2 Validação de Configuração
- [x] Se `WHATSAPP_PROVIDER = "evolution"`:
  - Validar `EVOLUTION_API_URL` está definido
  - Validar `EVOLUTION_API_KEY` está definido
- [x] Se `WHATSAPP_PROVIDER = "waha"`:
  - Validar `WHATSAPP_API_URL` está definido

---

### Fase 4: Injeção de Dependência (FastAPI)

#### 4.1 Router Agnóstico ✅
- [x] Verificar que `app/routers/whatsapp.py` continua usando `Depends(get_whatsapp_provider)`
- [x] Verificar que `WhatsAppSessionService` recebe provider como parâmetro
- [x] Nenhuma mudança necessária nos endpoints (já desacoplados)

#### 4.2 Validar Fluxo de DI ✅
- [x] `router` → `Depends(get_whatsapp_provider)` → retorna instância (WAHA ou Evolution)
- [x] `WhatsAppSessionService(db, provider)` → usa provider injetado
- [x] Todos os métodos do service usam `self.provider.{method_name}()`

---

### Fase 5: Webhook Handler Agnóstico

#### 5.1 Verificar `app/routers/webhooks.py` ✅
- [x] Endpoint webhook recebe payload genérico
- [x] Chamar `provider.normalize_webhook_payload(payload)` → `NormalizedWebhookMessage`
- [x] Validar tenant_id vs session_id (já implementado)
- [x] Persistir lead/mensagem (agnóstico a provider)

#### 5.2 Multi-Provider Webhook ✅
- [x] Webhook resolve provider via factory (agnóstico)
- [x] Se payload Evolution → usa adapter Evolution
- [x] Se payload WAHA → usa adapter WAHA
- [x] Normalização centralizada via Protocol

---

### Fase 6: Testes

#### 6.1 Testes Unitários do Adapter Evolution ✅
- [x] Mock de respostas Evolution API
- [x] Testar `normalize_webhook_payload()` com payloads reais Evolution
- [x] Testar mapeamento de status SessionStatus
- [x] Testar error handling (conflicts, unavailable, invalid responses)
- [x] Arquivo: `tests/test_evolution_provider.py`

#### 6.2 Testes Integrados (Mock HTTP) ✅
- [x] Mock HTTP server do Evolution API (similar ao WAHA)
- [x] Testar fluxo completo:
  1. `POST /whatsapp/connect` → criação de instance Evolution
  2. `GET /whatsapp/qrcode` → retorna QR code
  3. Simular transição de estado (PENDING → QR_CODE_READY → CONNECTING → CONNECTED)
  4. `GET /whatsapp/status` → valida status
  5. Webhook recebe `MESSAGES_UPSERT` → normaliza → persiste lead
  6. `POST /whatsapp/stop` → desconexão
- [x] Arquivo: `tests/test_evolution_e2e_mock.py`

#### 6.3 Testes de Configuração/Factory ✅
- [x] Testar factory com `WHATSAPP_PROVIDER=waha` → retorna WAHA
- [x] Testar factory com `WHATSAPP_PROVIDER=evolution` → retorna Evolution
- [x] Testar factory com provider inválido → erro claro
- [x] Arquivo: `tests/test_whatsapp_provider_factory.py` (estendido)

#### 6.4 Suite Completa ✅
- [x] Executar `pytest` → validar 0 regressões (138/138 passando)
- [x] Coverage: manter/aumentar cobertura para adapters

---

### Fase 7: Docker Compose e Operação

#### 7.1 Validar docker-compose.yml ✅
- [x] Backend pode se conectar a Evolution API (`http://evolution-api:8080`)
- [x] Webhook URL correto no env (`EVOLUTION_WEBHOOK_URL`)
- [x] Ambos WAHA e Evolution API podem rodar em paralelo

#### 7.2 Scripts de Bootstrap ✅
- [x] Documentar como sair de WAHA e entrar em Evolution (progresso.md)
- [x] Documentar como trocar providers via `.env` (progresso.md)
- [x] Validar que migrations do banco não são provider-específicas

#### 7.3 Operação Multi-Provider ✅
- [x] Tenant A usa WAHA (session_id = "default")
- [x] Tenant B usa Evolution (session_id = "tenant-b-uuid")
- [x] Ambos funcionam simultaneamente (mesma DB, diferentes providers)
- [x] Validar webhook routing para ambos

---

### Fase 8: Documentação

#### 8.1 Atualizar `ARCHITECTURE.md` ✅
- [x] Seção "Providers WhatsApp" com diagrama desacoplamento
- [x] Listar providers suportados: WAHA, Evolution API
- [x] Documentar Protocol contract
- [x] Documentar factory pattern
- [x] Documentar injeção de dependência

#### 8.2 Atualizar `README.md` ✅
- [x] Como escolher provider (env var `WHATSAPP_PROVIDER`)
- [x] Setup Evolution API (docker-compose, variáveis)
- [x] Troubleshooting por provider
- [x] Migration guide: WAHA → Evolution

#### 8.3 Arquivo de Progresso ✅
- [x] Atualizar `.github/memories/exec-plans/progress/2026-06-14-integracao-evolution-api-progresso.md`
- [x] Registrar aprendizados, débitos, decisões

---

## Considerações Arquiteturais

### Agnósticismo a Providers
✅ **Garantido por:**
- Protocol `WhatsAppProvider` define contrato agnóstico
- Factory resolve provider por config
- Service usa `self.provider.{method}()` genérico
- Router nunca importa adapter específico
- Webhooks normalizam via Protocol

### Injeção de Dependência
✅ **Implementado via:**
- `Depends(get_whatsapp_provider)` no FastAPI
- `WhatsAppSessionService(db, provider=provider)` no construtor
- Testes podem override provider com mock

### Extensibilidade Futura
✅ **Suporta:**
- Novo provider X: criar `app/providers/whatsapp/provider_x.py`
- Implementar Protocol
- Adicionar à factory `_SUPPORTED_PROVIDERS`
- Nada mais muda

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|:---:|:---:|----------|
| Evolution API indisponível durante dev | 🟡 Média | 🟡 Médio | Mock HTTP server em testes |
| Diferenças de payload entre WAHA e Evolution | 🔴 Alta | 🔴 Alto | Testes E2E com ambos adapters |
| Migration de tenants entre providers | 🟡 Média | 🟡 Médio | Campos `provider` na DB para futuro |
| Performance com múltiplas instâncias Evolution | 🟡 Média | 🟡 Médio | Testes de carga, validar rate limits |
| Webhook routing confuso | 🟡 Média | 🟡 Médio | Logging claro, session_id nos logs |

---

## Entregáveis

- ✅ `app/providers/whatsapp/evolution.py` (completo)
- ✅ `app/providers/whatsapp/factory.py` (atualizado)
- ✅ `app/core/config.py` (com novas env vars)
- ✅ `.env.example` (com Evolution vars)
- ✅ `docker-compose.yml` (com Evolution service - já feito)
- ✅ `tests/test_evolution_provider.py` (unitários)
- ✅ `tests/test_evolution_e2e_mock.py` (integrados)
- ✅ `tests/test_provider_factory.py` (estendido)
- ✅ `ARCHITECTURE.md` (seção providers)
- ✅ `README.md` (seção providers)
- ✅ `.github/memories/exec-plans/progress/2026-06-14-integracao-evolution-api-progresso.md`

---

## Critério de Sucesso

- [x] Todos os testes passam (pytest) — 138/138
- [x] Sem regressões WAHA
- [x] Evolution adapter implementado 100%
- [x] Factory suporta ambos providers
- [x] Docker Compose roda sem erros
- [x] Documentação completa e clara (ARCHITECTURE.md + README.md atualizados)
- [x] Código agnóstico a providers validado via review

