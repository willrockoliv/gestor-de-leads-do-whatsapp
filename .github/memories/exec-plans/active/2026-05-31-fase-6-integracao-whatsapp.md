# 📋 Plano de Implementação — Fase 6: Integração WhatsApp (QR Code e Status)

**Objetivo:** Implementar conexão real com WhatsApp via Waha ou Evolution API, permitindo que usuários conectem sua sessão WhatsApp via QR code e que o sistema receba mensagens reais.

**Dependências:** Fases 0–5 completas (backend + API + testes)  
**Prazo Estimado:** ~5–7 dias (prototipagem + testes end-to-end)  
**Critério de Saída:** QR code gerado e lido, sessão conectada, webhook recebendo mensagens reais, testes end-to-end passando.

---

## Fase 6.1 — Setup da Infraestrutura WhatsApp

### 6.1.1 Escolher e Integrar Serviço WhatsApp
- [x] Avaliar Waha vs Evolution API (ambos suportam QR code, webhooks, e multi-instância) — **Waha escolhido**
- [x] Adicionar Waha ao `docker-compose.yml` com versão fixa (não usar `latest`)
- [x] Configurar variáveis de ambiente (WHATSAPP_API_URL, WHATSAPP_API_PORT, WHATSAPP_API_KEY, WHATSAPP_WEBHOOK_URL, WHATSAPP_WEBHOOK_HMAC_KEY) nos arquivos .env e .env.example
- [x] Validar que o container sobe sem erros

Observação importante (2026-06-04):
- WAHA CORE aceita apenas sessão `default` (sessão única), impedindo "1 sessão por tenant" no runtime multi-tenant.
- Para cumprir 100% do RF de sessão por tenant em produção, será necessário WAHA PLUS (ou estratégia alternativa de isolamento por instância).

Atualização de direcionamento (2026-06-08):
- Plano de desacoplamento concluído: `.github/memories/exec-plans/completed/2026-06-04-desacoplamento-provider-whatsapp.md`.
- WAHA fica despriorizado como provider por enquanto.
- A estratégia agora é planejar e selecionar novo provider (TBD) aproveitando a arquitetura desacoplada já implementada.

### 6.1.2 Estruturar Models e Esquemas
- [x] Expandir model `WhatsAppSession` com campos: `session_id` (unique, string), `qr_code` (text, nullable), `qr_code_expires_at` (datetime, nullable), `phone_number` (string, nullable), `connected_since` (datetime, nullable)
- [x] Adicionar enum `SessionStatus` com valores: `PENDING`, `QR_CODE_READY`, `CONNECTING`, `CONNECTED`, `DISCONNECTED`, `ERROR`
- [x] Criar Pydantic schemas para payloads: `WhatsAppSessionResponse`, `QRCodeResponse`, `ConnectionStatusResponse`
- [x] Gerar migration Alembic para alteração do model
- [x] Testes unitários dos models atualizados

**RFs:** RF01  
**RNFs:** RNF01 (confiabilidade da conexão)

---

## Fase 6.2 — Service de Sessão WhatsApp

### 6.2.1 Implementar `WhatsAppSessionService`
- [x] Método `create_session(tenant_id)` — cria instância no serviço WhatsApp, retorna session_id
- [x] Método `get_qr_code(session_id)` — busca QR code atual do serviço WhatsApp
- [x] Método `check_connection_status(session_id)` — verifica se sessão está conectada
- [x] Método `disconnect_session(session_id)` — desconecta e limpa sessão
- [x] Método `update_session_from_api(session_id)` — sincroniza estado com serviço WhatsApp
- [x] Tratamento de timeout e retry (exponential backoff) para chamadas ao serviço WhatsApp
- [x] Logging estruturado (tenant_id, session_id, status changes)
- [x] Integração com `httpx` async para comunicação com API WhatsApp

**RFs:** RF01  
**RNFs:** RNF01, RNF02 (rate limiting considerado em 6.3)

### 6.2.2 Background Task para Sincronização de Sessão
- [x] Task `sync_whatsapp_sessions()` que roda a cada 30s
- [ ] Sincroniza sessão ativa de cada tenant com estado do provider ativo (Waha despriorizado; conclusão depende do novo provider TBD)
- [x] Detecta desconexões inesperadas e atualiza `Lead.is_processing = false` para leads em processamento
- [x] Log de mudanças de estado
- [x] Tratamento de erro (não interrompe loop em caso de falha)

---

## Fase 6.3 — Endpoints de Controle de Sessão

### 6.3.1 `POST /whatsapp/connect` — Iniciar Conexão
- [x] Recebe tenant_id (via JWT middleware)
- [x] Cria sessão WhatsAppSession no DB
- [x] Chama `WhatsAppSessionService.create_session()`
- [x] Retorna `{"session_id": "...", "status": "PENDING"}`
- [x] Teste unitário e integração

**RFs:** RF01

### 6.3.2 `GET /whatsapp/qrcode` — Obter QR Code
- [x] Recebe tenant_id (via JWT middleware)
- [x] Busca sessão ativa do tenant
- [x] Chama `WhatsAppSessionService.get_qr_code(session_id)`
- [x] Retorna `{"qr_code": "data:image/png;base64,..."}`  ou `{"status": "CONNECTED", "phone": "..."}`
- [x] Se QR code expirou (> 5 min), gera novo
- [x] Teste unitário e integração (mock de API WhatsApp)

**RFs:** RF01

### 6.3.3 `GET /whatsapp/status` — Status da Sessão
- [x] Recebe tenant_id (via JWT middleware)
- [x] Busca sessão do tenant
- [x] Retorna `{"status": "CONNECTED|DISCONNECTED|QR_CODE_READY|ERROR", "phone": "...", "connected_since": "..."}`
- [x] Teste unitário e integração

**RFs:** RF01, RNF01 (visibilidade do status)

### 6.3.4 Rate Limiting nos Endpoints
- [x] Aplicar rate limit em `/whatsapp/connect` (máx 5 por minuto por tenant)
- [x] Aplicar rate limit em `/whatsapp/qrcode` (máx 20 por minuto por tenant)
- [x] Usar middleware de rate limit (ex: `slowapi` ou custom com Redis se necessário, ou in-memory para MVP)
- [x] Retornar HTTP 429 com `Retry-After` header

**RNFs:** RNF02 (prevenção de abuso)

---

## Fase 6.4 — Validação e Segurança do Webhook

### 6.4.1 Atualizar Validação de Webhook WhatsApp
- [x] Verificar que `POST /webhooks/whatsapp` valida assinatura HMAC do serviço WhatsApp
- [x] Extrair `session_id` do payload e validar que sessão existe no DB
- [x] Validar que tenant da sessão bate com evento
- [x] Rejeitar (HTTP 403) se assinatura inválida ou sessão não existe
- [x] Logging de eventos recusados
- [x] Teste unitário: payload com assinatura inválida
- [x] Teste unitário: payload com session_id desconhecido

**RFs:** RF03, RNF03 (segurança)

### 6.4.2 Configurar Webhook na API WhatsApp
- [x] Obter URL de webhook (ex: `https://seu-backend.com/api/webhooks/whatsapp`)
- [x] Configurar no serviço WhatsApp (Waha) apontando para esse URL
- [x] Documentar em `.env.example` a variável `WHATSAPP_WEBHOOK_URL`
- [x] Documentar em `README.md` como configurar o webhook

**RFs:** RF03

---

## Fase 6.5 — Testes End-to-End com Sessão Simulada

### 6.5.1 Mock do Serviço WhatsApp para Testes
- [x] Criar mock HTTP server que simula Waha API
- [x] Endpoints mock: `POST /sessions`, `GET /sessions/{id}/qrcode`, `GET /sessions/{id}/status`
- [x] Fixture pytest que sobe mock server e sobrescreve `WHATSAPP_API_URL` em testes
- [x] Simular transições de estado: PENDING → QR_CODE_READY → CONNECTING → CONNECTED

### 6.5.2 Teste E2E: Fluxo Completo de Conexão
- [x] 1. Chamar `POST /whatsapp/connect` → sessão criada
- [x] 2. Chamar `GET /whatsapp/qrcode` → QR code retornado
- [x] 3. Simular leitura de QR code no mock (mudar estado para CONNECTING)
- [x] 4. Chamar `GET /whatsapp/status` → status = CONNECTING
- [x] 5. Simular conexão completa no mock
- [x] 6. Chamar `GET /whatsapp/status` → status = CONNECTED, phone_number populado

### 6.5.3 Teste E2E: Recebimento de Mensagens
- [x] 1. Sessão conectada (estado CONNECTED no mock)
- [x] 2. Enviar evento `message.upsert` para `POST /webhooks/whatsapp`
- [x] 3. Validar que lead é criado/atualizado no DB
- [x] 4. Validar que Message é persistida
- [x] 5. Validar que `Lead.is_processing = false` permite análise imediata

### 6.5.4 Teste E2E: Desconexão e Reconexão
- [x] 1. Sessão conectada
- [x] 2. Simular desconexão no mock (estado = DISCONNECTED)
- [x] 3. Background task detecta desconexão
- [x] 4. `WhatsAppSession.status = DISCONNECTED` atualizado
- [x] 5. Tentar reconectar: criar nova sessão com novo QR code
- [x] 6. Validar que leads em processamento recebem `is_processing = false` (lock liberado)

### 6.5.5 Teste de Rate Limiting
- [x] Fazer 6 chamadas rápidas a `/whatsapp/connect` → 6ª retorna HTTP 429
- [x] Validar header `Retry-After` presente
- [x] Aguardar 1 min e tentar novamente → sucesso

**RFs:** RF01, RF03, RF06 (não deixar leads trancados)  
**RNFs:** RNF01, RNF02, RNF03

---

## Fase 6.6 — Documentação e Atualização do Projeto

### 6.6.1 Atualizar `.github/ARCHITECTURE.md`
- [x] Seção "Integração WhatsApp" descrevendo fluxo QR code
- [x] Documentar escolha: Waha (critérios de decisão)
- [x] Diagrama de sequência: usuário → QR code → Waha API → webhook → lead + message
- [x] Estados da sessão e transições
- [x] Estrutura de payload webhook

### 6.6.2 Atualizar `README.md`
- [x] Instrução de setup do serviço WhatsApp no docker-compose
- [x] Variáveis de ambiente necessárias
- [x] Como obter QR code no frontend (já implementado em Fase 7)
- [x] Troubleshooting: "QR code não aparece", "Webhook não recebe mensagens"

### 6.6.3 Atualizar `.env.example`
- [x] `WHATSAPP_API_URL` (ex: `http://localhost`)
- [x] `WHATSAPP_API_PORT`
- [x] `WHATSAPP_API_KEY` (se necessário)
- [x] `WHATSAPP_WEBHOOK_URL` (ex: `https://seu-backend.com/api/webhooks/whatsapp`)
- [x] `WHATSAPP_WEBHOOK_HMAC_KEY` (HMAC secret)

### 6.6.4 Atualizar `.github/memories/exec-plans/progress/` com aprendizados
- [x] Registrar decisões: qual serviço WhatsApp foi escolhido e por quê
- [x] Debitos técnicos encontrados
- [x] Problemas resolvidos
- [x] Sugestões para Fase 8 (hardening)

---

## Fase 6.7 — Correção das Limitações Encontradas (Multi-Tenant Real)

Objetivo desta fase:
- Resolver o gap entre implementação atual e requisito de "1 sessão por tenant" em produção.
- Eliminar ambiguidades operacionais entre WAHA CORE e WAHA PLUS.

Status atual (2026-06-08):
- Em espera (on hold) para WAHA.
- Caminhos 6.7.2 e 6.7.3 não serão executados por enquanto.
- Próximo planejamento: provider alternativo (TBD) usando o contrato desacoplado já concluído.

Atualização (2026-06-09):
- Fase 6.7 encerrada sem implementação adicional neste ciclo, por decisão de produto/arquitetura.
- O trabalho segue diretamente para a Fase 6.8 (hardening e segurança).

### 6.7.1 Decisão Arquitetural Obrigatória (Go/No-Go)
- [ ] Formalizar decisão técnica: WAHA PLUS compartilhado x WAHA CORE isolado por instância por tenant
- [ ] Criar ADR com critérios: custo, isolamento, escalabilidade, operação, tempo de resposta a incidentes
- [ ] Definir estratégia de fallback e rollback por ambiente
- [ ] Atualizar `.github/ARCHITECTURE.md` com a decisão final e trade-offs

### 6.7.2 Caminho A — WAHA PLUS (sessões múltiplas nativas)
- [ ] Adicionar configuração explícita de tier/provedor (`WHATSAPP_PROVIDER`, `WHATSAPP_TIER`) e feature flag de ativação
- [ ] Ajustar `WhatsAppSessionService` para sempre usar `session_id` por tenant sem fallback para `default`
- [ ] Revisar constraints de banco para garantir 1 sessão ativa por tenant sem conflitar com histórico
- [ ] Garantir reconciliação de sessões órfãs (DB x provedor) no sync periódico
- [ ] Criar testes de integração multi-tenant reais (tenant A/B em paralelo, sem colisão)

### 6.7.3 Caminho B — WAHA CORE Isolado por Instância
- [ ] Modelar e persistir configuração por tenant (`base_url`, `api_key`, `session_alias`) com proteção de segredos
- [ ] Implementar roteamento dinâmico por tenant para a instância correta do WAHA CORE
- [ ] Implementar health-check por instância e circuit-breaker para isolamento de falhas
- [ ] Criar fluxo de provisionamento/deprovisionamento de instância por tenant (incluindo limpeza de sessão)
- [ ] Criar testes de falha isolada: indisponibilidade de tenant A não impacta tenant B

### 6.7.4 Migração, Observabilidade e Operação
- [ ] Criar plano de migração de tenants existentes para a estratégia escolhida
- [ ] Criar dashboard/alertas para: conflito de sessão, falha de webhook, taxa de reconexão, latência de status
- [ ] Definir SLOs de conexão (ex: tempo médio para CONNECTED, taxa de sucesso de reconexão)
- [ ] Publicar runbook operacional (incidente de sessão, rotação de chave, troca de endpoint)

**RFs:** RF01, RF06  
**RNFs:** RNF01, RNF02, RNF03

---

## Fase 6.8 — Revisão de Segurança e Hardening

Objetivo desta fase:
- Fechar lacunas de segurança antes de produção, com foco em PII, webhooks, abuso de API e isolamento por tenant.

### 6.8.1 Threat Modeling e Escopo de Risco
- [x] Criar DFD do fluxo WhatsApp (connect, qrcode, status, webhook, persistência)
- [x] Mapear ativos sensíveis (telefone, conteúdo de mensagem, tokens, session_id)
- [x] Classificar ameaças por severidade (spoofing, replay, IDOR, DoS, vazamento de PII)
- [x] Registrar plano de mitigação por risco em `.github/memories/exec-plans/security/pending`

### 6.8.2 Hardening de Webhook e API
- [x] Adicionar proteção anti-replay no webhook (timestamp + nonce/request-id + TTL)
- [x] Adicionar idempotência explícita para eventos repetidos do provedor
- [x] Aplicar limite de payload por endpoint sensível (timeout pendente)
- [x] Reforçar rate limiting para webhook/login conforme perfil de risco (refresh pendente: endpoint ainda não existe)
- [x] Garantir erros sanitizados sem stack trace/detalhes internos

### 6.8.3 Autorização e Isolamento por Tenant
- [x] Revisar endpoints WhatsApp para garantir ausência de IDOR
- [x] Garantir que `tenant_id` efetivo venha exclusivamente do contexto autenticado
- [x] Adicionar testes negativos cross-tenant (acesso indevido deve retornar 403/404)
- [x] Revisar regras de negócio no backend para não confiar em estado enviado pelo cliente

### 6.8.4 Proteção de PII, Logs e Segredos
- [x] Auditar logs para remover/mascarar telefone, mensagem e identificadores sensíveis
- [x] Implementar utilitário central de redaction para logs estruturados
- [x] Garantir que segredos não apareçam em logs de erro/debug
- [x] Revisar `.env.example` para evitar exemplos inseguros e documentar uso de secrets manager

### 6.8.5 Supply Chain e Dependências
- [x] Executar `pip-audit` e `npm audit` com bloqueio para severidade alta/crítica
- [x] Verificar alertas Dependabot abertos e registrar plano de correção
- [x] Garantir política de versões fixas e sem dependências de fonte não oficial
- [x] Incluir gate de CI para falhar merge em vulnerabilidade alta/crítica

### 6.8.6 Segurança de Infra e Transporte
- [x] Revisar CORS para configuração mínima por ambiente (sem permissivo global)
- [x] Revisar headers de segurança (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy)
- [x] Revisar Docker/Docker Compose: imagens fixas, usuário não-root, portas mínimas expostas
- [x] Documentar variáveis de security headers e recomendações dev/prod no README

Observação (2026-06-09):
- Item de validação HTTPS/TLS em ambiente alvo removido deste ciclo por escopo atual somente em dev local (sem produção ativa).

### 6.8.7 Testes de Segurança Automatizados
- [x] Criar testes para assinatura inválida, payload adulterado e replay
- [x] Criar testes para brute force/rate limiting em endpoints críticos (login e webhook)
- [x] Criar testes para não exposição de PII em respostas e logs
- [x] Atualizar pipeline para rodar suíte de segurança como etapa obrigatória

### 6.8.8 Fechamento e Governança
- [x] Consolidar achados por severidade: Crítico, Alto, Médio, Baixo
- [x] Bloquear merge/deploy enquanto houver risco alto/crítico sem mitigação
- [x] Mover itens mitigados para `.github/memories/exec-plans/security/resolved`
- [x] Emitir status final: "Bloqueado" (Dependabot remoto ainda com alerts high abertos; reavaliar após novo scan)

**RFs:** RF03  
**RNFs:** RNF02, RNF03

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
       ↓
6.7 — Correção de Limitações (multi-tenant real)
  ├─ 6.7.1 (decisão arquitetural)
  ├─ 6.7.2 (caminho WAHA PLUS)
  ├─ 6.7.3 (caminho CORE isolado)
  └─ 6.7.4 (migração + operação)
       ↓
6.8 — Revisão de Segurança
  ├─ 6.8.1 (threat model)
  ├─ 6.8.2 (hardening webhook/API)
  ├─ 6.8.3 (authz + tenant isolation)
  ├─ 6.8.4 (PII/logs/segredos)
  ├─ 6.8.5 (supply chain)
  ├─ 6.8.6 (infra/transporte)
  ├─ 6.8.7 (testes automatizados)
  └─ 6.8.8 (fechamento)
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
- ✅ Estratégia de multi-tenant real definida e implementada (WAHA PLUS ou isolamento por instância)
- ✅ Revisão de segurança concluída com registro de achados, mitigação e status final
