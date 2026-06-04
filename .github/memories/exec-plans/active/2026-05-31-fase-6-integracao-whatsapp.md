# 📋 Plano de Implementação — Fase 6: Integração WhatsApp (QR Code e Status)

**Objetivo:** Implementar conexão real com WhatsApp via Waha ou Evolution API, permitindo que usuários conectem sua sessão WhatsApp via QR code e que o sistema receba mensagens reais.

**Dependências:** Fases 0–5 completas (backend + API + testes)  
**Prazo Estimado:** ~5–7 dias (prototipagem + testes end-to-end)  
**Critério de Saída:** QR code gerado e lido, sessão conectada, webhook recebendo mensagens reais, testes end-to-end passando.

---

## Fase 6.1 — Setup da Infraestrutura WhatsApp

### 6.1.1 Escolher e Integrar Serviço WhatsApp
- [x] Avaliar Waha vs Evolution API (ambos suportam QR code, webhooks, e multi-instância) — **Waha escolhido**
- [ ] Adicionar Waha ao `docker-compose.yml` com versão fixa (não usar `latest`)
- [ ] Configurar variáveis de ambiente (WHATSAPP_API_URL, WHATSAPP_API_PORT, WHATSAPP_API_KEY, WHATSAPP_WEBHOOK_URL, WHATSAPP_WEBHOOK_HMAC_KEY) nos arquivos .env e .env.example
- [ ] Validar que o container sobe sem erros

### 6.1.2 Estruturar Models e Esquemas
- [ ] Expandir model `WhatsAppSession` com campos: `session_id` (unique, string), `qr_code` (text, nullable), `qr_code_expires_at` (datetime, nullable), `phone_number` (string, nullable), `connected_since` (datetime, nullable)
- [ ] Adicionar enum `SessionStatus` com valores: `PENDING`, `QR_CODE_READY`, `CONNECTING`, `CONNECTED`, `DISCONNECTED`, `ERROR`
- [ ] Criar Pydantic schemas para payloads: `WhatsAppSessionResponse`, `QRCodeResponse`, `ConnectionStatusResponse`
- [ ] Gerar migration Alembic para alteração do model
- [ ] Testes unitários dos models atualizados

**RFs:** RF01  
**RNFs:** RNF01 (confiabilidade da conexão)

---

## Fase 6.2 — Service de Sessão WhatsApp

### 6.2.1 Implementar `WhatsAppSessionService`
- [ ] Método `create_session(tenant_id)` — cria instância no serviço WhatsApp, retorna session_id
- [ ] Método `get_qr_code(session_id)` — busca QR code atual do serviço WhatsApp
- [ ] Método `check_connection_status(session_id)` — verifica se sessão está conectada
- [ ] Método `disconnect_session(session_id)` — desconecta e limpa sessão
- [ ] Método `update_session_from_api(session_id)` — sincroniza estado com serviço WhatsApp
- [ ] Tratamento de timeout e retry (exponential backoff) para chamadas ao serviço WhatsApp
- [ ] Logging estruturado (tenant_id, session_id, status changes)
- [ ] Integração com `httpx` async para comunicação com API WhatsApp

**RFs:** RF01  
**RNFs:** RNF01, RNF02 (rate limiting considerado em 6.3)

### 6.2.2 Background Task para Sincronização de Sessão
- [ ] Task `sync_whatsapp_sessions()` que roda a cada 30s
- [ ] Sincroniza sessão ativa de cada tenant com estado do serviço Waha (1 sessão por tenant no MVP)
- [ ] Detecta desconexões inesperadas e atualiza `Lead.is_processing = false` para leads em processamento
- [ ] Log de mudanças de estado
- [ ] Tratamento de erro (não interrompe loop em caso de falha)

---

## Fase 6.3 — Endpoints de Controle de Sessão

### 6.3.1 `POST /whatsapp/connect` — Iniciar Conexão
- [ ] Recebe tenant_id (via JWT middleware)
- [ ] Cria sessão WhatsAppSession no DB
- [ ] Chama `WhatsAppSessionService.create_session()`
- [ ] Retorna `{"session_id": "...", "status": "PENDING"}`
- [ ] Teste unitário e integração

**RFs:** RF01

### 6.3.2 `GET /whatsapp/qrcode` — Obter QR Code
- [ ] Recebe tenant_id (via JWT middleware)
- [ ] Busca sessão ativa do tenant
- [ ] Chama `WhatsAppSessionService.get_qr_code(session_id)`
- [ ] Retorna `{"qr_code": "data:image/png;base64,..."}`  ou `{"status": "CONNECTED", "phone": "..."}`
- [ ] Se QR code expirou (> 5 min), gera novo
- [ ] Teste unitário e integração (mock de API WhatsApp)

**RFs:** RF01

### 6.3.3 `GET /whatsapp/status` — Status da Sessão
- [ ] Recebe tenant_id (via JWT middleware)
- [ ] Busca sessão do tenant
- [ ] Retorna `{"status": "CONNECTED|DISCONNECTED|QR_CODE_READY|ERROR", "phone": "...", "connected_since": "..."}`
- [ ] Teste unitário e integração

**RFs:** RF01, RNF01 (visibilidade do status)

### 6.3.4 Rate Limiting nos Endpoints
- [ ] Aplicar rate limit em `/whatsapp/connect` (máx 5 por minuto por tenant)
- [ ] Aplicar rate limit em `/whatsapp/qrcode` (máx 20 por minuto por tenant)
- [ ] Usar middleware de rate limit (ex: `slowapi` ou custom com Redis se necessário, ou in-memory para MVP)
- [ ] Retornar HTTP 429 com `Retry-After` header

**RNFs:** RNF02 (prevenção de abuso)

---

## Fase 6.4 — Validação e Segurança do Webhook

### 6.4.1 Atualizar Validação de Webhook WhatsApp
- [ ] Verificar que `POST /webhooks/whatsapp` valida assinatura HMAC do serviço WhatsApp
- [ ] Extrair `session_id` do payload e validar que sessão existe no DB
- [ ] Validar que tenant da sessão bate com evento
- [ ] Rejeitar (HTTP 403) se assinatura inválida ou sessão não existe
- [ ] Logging de eventos recusados
- [ ] Teste unitário: payload com assinatura inválida
- [ ] Teste unitário: payload com session_id desconhecido

**RFs:** RF03, RNF03 (segurança)

### 6.4.2 Configurar Webhook na API WhatsApp
- [ ] Obter URL de webhook (ex: `https://seu-backend.com/api/webhooks/whatsapp`)
- [ ] Configurar no serviço WhatsApp (Waha) apontando para esse URL
- [ ] Documentar em `.env.example` a variável `WHATSAPP_WEBHOOK_URL`
- [ ] Documentar em `README.md` como configurar o webhook

**RFs:** RF03

---

## Fase 6.5 — Testes End-to-End com Sessão Simulada

### 6.5.1 Mock do Serviço WhatsApp para Testes
- [ ] Criar mock HTTP server que simula Waha API
- [ ] Endpoints mock: `POST /sessions`, `GET /sessions/{id}/qrcode`, `GET /sessions/{id}/status`
- [ ] Fixture pytest que sobe mock server e sobrescreve `WHATSAPP_API_URL` em testes
- [ ] Simular transições de estado: PENDING → QR_CODE_READY → CONNECTING → CONNECTED

### 6.5.2 Teste E2E: Fluxo Completo de Conexão
- [ ] 1. Chamar `POST /whatsapp/connect` → sessão criada
- [ ] 2. Chamar `GET /whatsapp/qrcode` → QR code retornado
- [ ] 3. Simular leitura de QR code no mock (mudar estado para CONNECTING)
- [ ] 4. Chamar `GET /whatsapp/status` → status = CONNECTING
- [ ] 5. Simular conexão completa no mock
- [ ] 6. Chamar `GET /whatsapp/status` → status = CONNECTED, phone_number populado

### 6.5.3 Teste E2E: Recebimento de Mensagens
- [ ] 1. Sessão conectada (estado CONNECTED no mock)
- [ ] 2. Enviar evento `message.upsert` para `POST /webhooks/whatsapp`
- [ ] 3. Validar que lead é criado/atualizado no DB
- [ ] 4. Validar que Message é persistida
- [ ] 5. Validar que `Lead.is_processing = false` permite análise imediata

### 6.5.4 Teste E2E: Desconexão e Reconexão
- [ ] 1. Sessão conectada
- [ ] 2. Simular desconexão no mock (estado = DISCONNECTED)
- [ ] 3. Background task detecta desconexão
- [ ] 4. `WhatsAppSession.status = DISCONNECTED` atualizado
- [ ] 5. Tentar reconectar: criar nova sessão com novo QR code
- [ ] 6. Validar que leads em processamento recebem `is_processing = false` (lock liberado)

### 6.5.5 Teste de Rate Limiting
- [ ] Fazer 6 chamadas rápidas a `/whatsapp/connect` → 6ª retorna HTTP 429
- [ ] Validar header `Retry-After` presente
- [ ] Aguardar 1 min e tentar novamente → sucesso

**RFs:** RF01, RF03, RF06 (não deixar leads trancados)  
**RNFs:** RNF01, RNF02, RNF03

---

## Fase 6.6 — Documentação e Atualização do Projeto

### 6.6.1 Atualizar `.github/ARCHITECTURE.md`
- [ ] Seção "Integração WhatsApp" descrevendo fluxo QR code
- [ ] Documentar escolha: Waha (critérios de decisão)
- [ ] Diagrama de sequência: usuário → QR code → Waha API → webhook → lead + message
- [ ] Estados da sessão e transições
- [ ] Estrutura de payload webhook

### 6.6.2 Atualizar `README.md`
- [ ] Instrução de setup do serviço WhatsApp no docker-compose
- [ ] Variáveis de ambiente necessárias
- [ ] Como obter QR code no frontend (já implementado em Fase 7)
- [ ] Troubleshooting: "QR code não aparece", "Webhook não recebe mensagens"

### 6.6.3 Atualizar `.env.example`
- [ ] `WHATSAPP_API_URL` (ex: `http://localhost`)
- [ ] `WHATSAPP_API_PORT`
- [ ] `WHATSAPP_API_KEY` (se necessário)
- [ ] `WHATSAPP_WEBHOOK_URL` (ex: `https://seu-backend.com/api/webhooks/whatsapp`)
- [ ] `WHATSAPP_WEBHOOK_HMAC_KEY` (HMAC secret)

### 6.6.4 Atualizar `.github/memories/exec-plans/progress/` com aprendizados
- [ ] Registrar decisões: qual serviço WhatsApp foi escolhido e por quê
- [ ] Debitos técnicos encontrados
- [ ] Problemas resolvidos
- [ ] Sugestões para Fase 8 (hardening)

---

## Ordem de Execução

```
6.1 — Setup Infra
  ├─ 6.1.1 (escolher serviço, docker-compose)
  └─ 6.1.2 (models, schemas, migration)
       ↓
6.2 — Service
  ├─ 6.2.1 (WhatsAppSessionService)
  └─ 6.2.2 (background task sync)
       ↓
6.3 — Endpoints
  ├─ 6.3.1 (/whatsapp/connect)
  ├─ 6.3.2 (/whatsapp/qrcode)
  ├─ 6.3.3 (/whatsapp/status)
  └─ 6.3.4 (rate limiting)
       ↓
6.4 — Validação & Webhook
  ├─ 6.4.1 (validação HMAC, testes)
  └─ 6.4.2 (configurar webhook)
       ↓
6.5 — Testes E2E
  ├─ 6.5.1 (mock server)
  ├─ 6.5.2 (E2E fluxo conexão)
  ├─ 6.5.3 (E2E recebimento)
  ├─ 6.5.4 (E2E desconexão)
  └─ 6.5.5 (E2E rate limiting)
       ↓
6.6 — Documentação
  ├─ 6.6.1 (ARCHITECTURE.md)
  ├─ 6.6.2 (README.md)
  ├─ 6.6.3 (.env.example)
  └─ 6.6.4 (progresso)
```

**Critério de Saída da Fase 6:**
- ✅ Docker-compose com serviço WhatsApp rodando
- ✅ Models e migrations aplicadas
- ✅ Todos os endpoints funcionando
- ✅ Rate limiting ativo
- ✅ Webhook validando e recebendo mensagens
- ✅ Testes E2E cobrindo fluxo completo (conexão, recebimento, desconexão)
- ✅ 100+ testes acumulados (79 + fase 6)
- ✅ Documentação atualizada
- ✅ Frontend pronto para consumir endpoints (`GET /whatsapp/qrcode`, `GET /whatsapp/status`)
