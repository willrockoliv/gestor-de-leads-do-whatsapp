# Auditoria de Variáveis de Ambiente WhatsApp & Evolution

**Data:** 2026-06-14  
**Status:** Completo - Mapa de uso gerado

## 📊 Resumo Executivo

| Achado | Severidade | Impacto |
|--------|-----------|---------|
| **WHATSAPP_WEBHOOK_SECRET vs WHATSAPP_WEBHOOK_HMAC_KEY — Redundância crítica** | 🔴 Alto | Confusão de qual usar; fallback acidental em código |
| **WHATSAPP_API_PORT nunca é usado em waha.py** | 🟡 Médio | Variável inútil, aumenta superfície de confusão |
| **Separação de webhooks (WHATSAPP_WEBHOOK_URL vs EVOLUTION_WEBHOOK_URL)** | 🟢 Baixo | Design intencional, mas poderia ser mais explícito |
| **Falta de validação de variáveis críticas no startup** | 🔴 Alto | Erros descobertos apenas em runtime |

---

## 1️⃣ WHATSAPP_WEBHOOK_SECRET vs WHATSAPP_WEBHOOK_HMAC_KEY

### Definição em Config
```python
# app/core/config.py (linhas 23-24)
WHATSAPP_WEBHOOK_SECRET: str = ""
WHATSAPP_WEBHOOK_HMAC_KEY: str = ""
```

### Onde é Usado

#### 🔹 app/routers/webhooks.py (L43)
```python
def _webhook_hmac_secret() -> str:
    return settings.WHATSAPP_WEBHOOK_HMAC_KEY or settings.WHATSAPP_WEBHOOK_SECRET
```
**Contexto:** Função helper que busca secret para validação de assinatura HMAC-SHA512. Tenta HMAC_KEY primeiro, fallback para SECRET.

#### 🔹 app/providers/whatsapp/waha.py (L143-144)
```python
"hmac": {"key": settings.WHATSAPP_WEBHOOK_HMAC_KEY}
if settings.WHATSAPP_WEBHOOK_HMAC_KEY
else None,
```
**Contexto:** Configura webhook no WAHA com chave HMAC (apenas HMAC_KEY, não usa SECRET).

### Arquivo de Ambiente
```
# .env, .env.example (linhas 33-35)
WHATSAPP_WEBHOOK_HMAC_KEY=
WHATSAPP_WEBHOOK_SECRET=
```

### 🚨 Problema
- **Ambos existem** mas têm propósitos semelhantes
- **Conflito de nomes**: `SECRET` vs `HMAC_KEY` — qual é a mais recente?
- **Fallback silencioso**: `WHATSAPP_WEBHOOK_HMAC_KEY or WHATSAPP_WEBHOOK_SECRET` pode mascarar configuração errada
- **Inconsistência**: WAHA usa apenas `HMAC_KEY`, webhooks.py tenta ambas
- **Sem documentação clara** sobre qual usar em cada caso

### 💡 Recomendação
**Consolidar em `WHATSAPP_WEBHOOK_HMAC_KEY`** (nome mais descritivo e técnico)
- Remover `WHATSAPP_WEBHOOK_SECRET` (deprecar com aviso)
- Atualizar fallback: `settings.WHATSAPP_WEBHOOK_HMAC_KEY` apenas
- Documentar mudança em README e `.env.example`

---

## 2️⃣ EVOLUTION_WEBHOOK_URL

### Definição em Config
```python
# app/core/config.py (linha 35)
EVOLUTION_WEBHOOK_URL: str = ""
```

### Onde é Usado

#### 🔹 app/providers/whatsapp/evolution.py
```python
# L41-42: inicialização
self.base_url = settings.EVOLUTION_API_URL.rstrip("/")
self.api_key = settings.EVOLUTION_API_KEY

# L124, L143: configuração de webhook
"webhook": {
    "url": settings.EVOLUTION_WEBHOOK_URL,
    "enabled": True,
    "events": [...]
} if settings.EVOLUTION_WEBHOOK_URL else None,

# L147: validação
if not settings.EVOLUTION_WEBHOOK_URL:
    payload.pop("webhook", None)
```
**Contexto:** URL de webhook que a Evolution API chama para enviar eventos (messages, status, etc).

### Arquivo de Ambiente
```
# .env, .env.example (linha 28)
EVOLUTION_WEBHOOK_URL="http://localhost:8000/webhooks/evolution"
```

### ✅ Status
- **Bem definida** e usada apenas em evolution.py
- **Sem redundâncias detectadas**
- **Comportamento correto**: se não configurada, webhook é omitido do payload

---

## 3️⃣ WHATSAPP_WEBHOOK_URL

### Definição em Config
```python
# app/core/config.py (linha 40)
WHATSAPP_WEBHOOK_URL: str = ""
```

### Onde é Usado

#### 🔹 app/providers/whatsapp/waha.py
```python
# L141: configuração de webhook
"url": settings.WHATSAPP_WEBHOOK_URL,

# L152: validação
if not settings.WHATSAPP_WEBHOOK_URL:
    payload = {"name": session_id}
```
**Contexto:** URL de webhook que o WAHA chama para enviar eventos (messages, status, etc).

### Arquivo de Ambiente
```
# Não está em .env.example atualmente!
# (pode ser um oversight ou intencional)
```

### ✅ Status
- **Bem definida** e usada apenas em waha.py
- **Sem redundâncias detectadas**
- **Comportamento correto**: se não configurada, webhook é omitido

### 🟡 Nota
- Não aparece explicitamente em `.env.example`
- Deveria estar documentada lá para clareza

---

## 4️⃣ WHATSAPP_API_URL, WHATSAPP_API_PORT, WHATSAPP_API_KEY

### Definição em Config
```python
# app/core/config.py (linhas 28-30)
WHATSAPP_API_URL: str = "http://waha:3000"
WHATSAPP_API_PORT: int = 3000
WHATSAPP_API_KEY: str = ""
```

### Onde é Usado

#### 🔹 app/providers/whatsapp/waha.py
```python
# L40: base URL
self.base_url = settings.WHATSAPP_API_URL.rstrip("/")

# L44-45: API key em header
if settings.WHATSAPP_API_KEY:
    headers["X-Api-Key"] = settings.WHATSAPP_API_KEY
```
**Contexto:** Configuração de conexão ao serviço WAHA.

### Arquivo de Ambiente
```
# .env, .env.example (linhas 21-22)
WHATSAPP_API_URL="http://waha:3000"
WHATSAPP_API_PORT=3000
```

### 🚨 Problema
- **WHATSAPP_API_PORT é definida em config.py mas NUNCA é usada** em waha.py
- A porta já está embutida em `WHATSAPP_API_URL` ("http://waha:3000")
- Redundância: URL já contém porta, não há razão ter PORT separado
- Confunde desenvolvedores: alterando PORT não afeta comportamento

### ✅ OK
- **WHATSAPP_API_URL** é usado corretamente
- **WHATSAPP_API_KEY** é usado corretamente

### 💡 Recomendação
**Remover WHATSAPP_API_PORT** (está morto)
- Deletar de config.py
- Deletar de .env e .env.example
- Atualizar README (se documentado)

---

## 5️⃣ EVOLUTION_API_URL, EVOLUTION_API_KEY

### Definição em Config
```python
# app/core/config.py (linhas 32-33)
EVOLUTION_API_URL: str = "http://evolution-api:8080"
EVOLUTION_API_KEY: str = ""
```

### Onde é Usado

#### 🔹 app/providers/whatsapp/evolution.py
```python
# L41-42: inicialização
self.base_url = settings.EVOLUTION_API_URL.rstrip("/")
self.api_key = settings.EVOLUTION_API_KEY

# L47-50: headers
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}
if self.api_key:
    headers["Authorization"] = f"Bearer {self.api_key}"
```
**Contexto:** Configuração de conexão à Evolution API.

### Arquivo de Ambiente
```
# .env.example, .env (não tem URL, apenas em config padrão)
# EVOLUTION_API_URL não está em .env.example
# EVOLUTION_API_KEY não está em .env.example
```

### ✅ Status
- **Bem usados em evolution.py**
- **Sem redundâncias detectadas**

### 🟡 Nota
- Não aparecem em `.env.example` (deveria estar para configuração prod)

---

## 6️⃣ WHATSAPP_PROVIDER

### Definição em Config
```python
# app/core/config.py (linha 25)
WHATSAPP_PROVIDER: str = "evolution"
```

### Onde é Usado

#### 🔹 app/providers/whatsapp/factory.py
```python
# L15
provider_key = (settings.WHATSAPP_PROVIDER or "waha").strip().lower()
provider_cls = _SUPPORTED_PROVIDERS.get(provider_key)
```
**Contexto:** Seleciona provider (WAHA ou Evolution).

### Arquivo de Ambiente
```
# .env, .env.example (linha 20)
WHATSAPP_PROVIDER="evolution"
```

### ✅ Status
- **Bem definida e usada corretamente**
- **Factory pattern é apropriado**

---

## 7️⃣ Variáveis de Webhook Rate Limiting & Security

### Definição em Config
```python
# app/core/config.py (linhas 40-47)
WHATSAPP_WEBHOOK_URL: str = ""
WHATSAPP_WEBHOOK_REPLAY_TTL_SECONDS: int = 300
WHATSAPP_WEBHOOK_REQUIRE_REPLAY_HEADERS: bool = False
WHATSAPP_WEBHOOK_MAX_PAYLOAD_BYTES: int = 262144  # 256KB
WHATSAPP_WEBHOOK_RATE_LIMIT: int = 300
WHATSAPP_WEBHOOK_RATE_LIMIT_WINDOW_SECONDS: int = 60
AUTH_LOGIN_RATE_LIMIT: int = 10
AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 60
```

### Onde é Usado

#### 🔹 app/routers/webhooks.py
```python
# L89-90: rate limiting por IP
limit=settings.WHATSAPP_WEBHOOK_RATE_LIMIT,
window_seconds=settings.WHATSAPP_WEBHOOK_RATE_LIMIT_WINDOW_SECONDS,

# L101: validação de tamanho
if len(body) > settings.WHATSAPP_WEBHOOK_MAX_PAYLOAD_BYTES:

# L111: validação de replay headers
if settings.WHATSAPP_WEBHOOK_REQUIRE_REPLAY_HEADERS and (not request_id or request_ts is None):

# L117: TTL de replay
settings.WHATSAPP_WEBHOOK_REPLAY_TTL_SECONDS,

# L148: replay guard
window_seconds=settings.WHATSAPP_WEBHOOK_REPLAY_TTL_SECONDS,
```

### ✅ Status
- **Bem definidas e usadas corretamente**
- **Importante para segurança (rate limit, replay protection)**

---

## 📋 Tabela Consolidada: Variável → Arquivo → Contexto

| Variável | Config.py | Arquivo(s) de Uso | Tipo | Status |
|----------|-----------|-------------------|------|--------|
| `WHATSAPP_WEBHOOK_SECRET` | L23 | webhooks.py:43 | string | 🚨 REDUNDANTE |
| `WHATSAPP_WEBHOOK_HMAC_KEY` | L24 | webhooks.py:43, waha.py:143 | string | ✅ Ativo |
| `WHATSAPP_PROVIDER` | L25 | factory.py:15 | string | ✅ OK |
| `WHATSAPP_API_URL` | L28 | waha.py:40 | string | ✅ OK |
| `WHATSAPP_API_PORT` | L29 | **NUNCA USADO** | int | 🚨 MORTO |
| `WHATSAPP_API_KEY` | L30 | waha.py:44-45 | string | ✅ OK |
| `EVOLUTION_API_URL` | L32 | evolution.py:41 | string | ✅ OK |
| `EVOLUTION_API_KEY` | L33 | evolution.py:42 | string | ✅ OK |
| `EVOLUTION_WEBHOOK_URL` | L35 | evolution.py:124, 143, 147 | string | ✅ OK |
| `WHATSAPP_WEBHOOK_URL` | L40 | waha.py:141, 152 | string | ✅ OK |
| `WHATSAPP_WEBHOOK_REPLAY_TTL_SECONDS` | L41 | webhooks.py:117, 148 | int | ✅ OK |
| `WHATSAPP_WEBHOOK_REQUIRE_REPLAY_HEADERS` | L42 | webhooks.py:111 | bool | ✅ OK |
| `WHATSAPP_WEBHOOK_MAX_PAYLOAD_BYTES` | L43 | webhooks.py:101 | int | ✅ OK |
| `WHATSAPP_WEBHOOK_RATE_LIMIT` | L44 | webhooks.py:89 | int | ✅ OK |
| `WHATSAPP_WEBHOOK_RATE_LIMIT_WINDOW_SECONDS` | L45 | webhooks.py:90 | int | ✅ OK |

---

## 🔴 Redundâncias & Problemas Detectados

### 1. WHATSAPP_WEBHOOK_SECRET vs WHATSAPP_WEBHOOK_HMAC_KEY
- **Problema**: Ambas mapeiam o mesmo conceito (chave de assinatura de webhook)
- **Fallback confuso**: `HMAC_KEY or SECRET` em webhooks.py
- **Inconsistência em WAHA**: usa apenas HMAC_KEY
- **Impacto**: Confusão de qual usar, comportamento não-determinístico

**Prioridade**: 🔴 **CRÍTICA** — Consolidar em uma única variável

### 2. WHATSAPP_API_PORT nunca é usado
- **Problema**: Definida em config.py:29, mas waha.py usa PORT embutida em WHATSAPP_API_URL
- **Impacto**: Usuário pode alterar PORT e código continua ignorando
- **Superfície de confusão**: Variável inútil que faz parecer que PORT é configurável

**Prioridade**: 🟡 **ALTA** — Remover PORT (está morto)

### 3. Falta de documentação em .env.example
- **Problema**: `EVOLUTION_API_URL`, `EVOLUTION_API_KEY`, `WHATSAPP_WEBHOOK_URL` não aparecem em .env.example
- **Impacto**: Usuários não sabem que existem ou como configurar
- **Confundibilidade**: Defaults em config.py são usados silenciosamente

**Prioridade**: 🟡 **ALTA** — Adicionar a .env.example com comentários

### 4. Sem validação de startup
- **Problema**: Variáveis críticas (EVOLUTION_WEBHOOK_URL, WHATSAPP_WEBHOOK_URL) não são validadas no startup
- **Impacto**: Erros descobertos apenas após tentar processar webhook, não durante boot
- **Segurança**: Sem validação, payload pode ser processado com config incompleta

**Prioridade**: 🟡 **ALTA** — Adicionar validação condicional

---

## 💡 Oportunidades de Consolidação

### ✅ Recomendação 1: Consolidar Secrets de Webhook
```python
# ANTES (redundante)
WHATSAPP_WEBHOOK_SECRET: str = ""
WHATSAPP_WEBHOOK_HMAC_KEY: str = ""

# DEPOIS (único)
WHATSAPP_WEBHOOK_HMAC_KEY: str = ""
# (WHATSAPP_WEBHOOK_SECRET removido ou deprecado com aviso)
```

**Ação**: 
- Remover `WHATSAPP_WEBHOOK_SECRET` de config.py
- Atualizar fallback em webhooks.py
- Deprecated warning em README

---

### ✅ Recomendação 2: Remover WHATSAPP_API_PORT
```python
# ANTES (config.py)
WHATSAPP_API_PORT: int = 3000

# DEPOIS (removido)
# PORT já está em WHATSAPP_API_URL
```

**Ação**:
- Remover `WHATSAPP_API_PORT` de config.py
- Remover de .env e .env.example
- Documentar em README como usar `WHATSAPP_API_URL` com porta

---

### ✅ Recomendação 3: Documentar Webhooks em .env.example
```bash
# Add to .env.example

# WAHA Webhook (if WHATSAPP_PROVIDER="waha")
WHATSAPP_WEBHOOK_URL="http://localhost:8000/webhooks/whatsapp"

# Evolution Webhook (if WHATSAPP_PROVIDER="evolution")
EVOLUTION_WEBHOOK_URL="http://localhost:8000/webhooks/evolution"

# Evolution API Config (if WHATSAPP_PROVIDER="evolution")
EVOLUTION_API_URL="http://evolution-api:8080"
EVOLUTION_API_KEY=""
```

---

### ✅ Recomendação 4: Validação de Startup
```python
# app/core/config.py or app/main.py

def validate_whatsapp_config(settings):
    """Validate WhatsApp configuration on startup."""
    provider = (settings.WHATSAPP_PROVIDER or "waha").lower()
    
    if provider == "waha":
        if not settings.WHATSAPP_WEBHOOK_URL:
            logger.warning("WHATSAPP_WEBHOOK_URL not configured; webhooks will be disabled")
    
    elif provider == "evolution":
        if not settings.EVOLUTION_API_KEY:
            raise ValueError("EVOLUTION_API_KEY is required when using Evolution provider")
        if not settings.EVOLUTION_WEBHOOK_URL:
            logger.warning("EVOLUTION_WEBHOOK_URL not configured; webhooks will be disabled")
    
    # Validate HMAC secret
    hmac_secret = settings.WHATSAPP_WEBHOOK_HMAC_KEY or settings.WHATSAPP_WEBHOOK_SECRET
    if not hmac_secret:
        logger.warning("No WHATSAPP_WEBHOOK_HMAC_KEY configured; webhook verification disabled")
```

---

## 📍 Referências de Código

- **Config**: [app/core/config.py](app/core/config.py#L20-L50)
- **WAHA Provider**: [app/providers/whatsapp/waha.py](app/providers/whatsapp/waha.py#L40-L152)
- **Evolution Provider**: [app/providers/whatsapp/evolution.py](app/providers/whatsapp/evolution.py#L41-L147)
- **Webhooks Router**: [app/routers/webhooks.py](app/routers/webhooks.py#L40-L120)
- **Factory**: [app/providers/whatsapp/factory.py](app/providers/whatsapp/factory.py#L15)
- **Environment Files**: [.env.example](.env.example#L20-L35)

---

## ✅ Checklist de Ação

- [ ] Consolidar `WHATSAPP_WEBHOOK_SECRET` → `WHATSAPP_WEBHOOK_HMAC_KEY`
- [ ] Remover `WHATSAPP_API_PORT` (nunca usado)
- [ ] Adicionar `EVOLUTION_API_URL`, `EVOLUTION_API_KEY`, `WHATSAPP_WEBHOOK_URL` a `.env.example`
- [ ] Implementar validação de config no startup
- [ ] Atualizar README com clareza sobre qual secret usar
- [ ] Criar teste para verificar nenhuma variável "morta" na config
