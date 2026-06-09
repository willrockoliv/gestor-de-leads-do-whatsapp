# Security Resolved — WhatsApp Threat Model (2026-06-09)

Status: RESOLVED (com monitoramento contínuo)
Scope: Fase 6.8.1 (Threat modeling e escopo de risco)

## DFD (alto nível)

```mermaid
flowchart LR
  U[Usuario autenticado]
  FE[Frontend Next.js]
  API[FastAPI Backend]
  WA[Provider WhatsApp]
  WH[Webhook /webhooks/whatsapp]
  DB[(PostgreSQL)]
  LLM[LLM Provider]

  U --> FE --> API
  API --> WA
  WA --> WH --> API
  API --> DB
  API --> LLM
```

## Ativos sensíveis
- Telefone do lead (PII)
- Conteúdo de mensagens/conversas
- session_id de WhatsApp
- Tokens/segredos (`SECRET_KEY`, `WHATSAPP_API_KEY`, `WHATSAPP_WEBHOOK_HMAC_KEY`)
- Metadados de tenant (isolamento multi-tenant)

## Ameaças por severidade

### Alto
1. IDOR cross-tenant em `/whatsapp/qrcode` e `/whatsapp/status`
- Vetor: manipulação de identificadores para obter sessão de outro tenant.
- Mitigação aplicada: busca de sessão exclusivamente por `tenant_id` do contexto autenticado.

2. Replay/spoof de webhook
- Vetor: reenvio de payload válido ou assinatura falsa.
- Mitigação aplicada: HMAC + replay guard (timestamp/nonce/hash + TTL) + sessão conhecida.

3. Vazamento de PII em logs
- Vetor: logs com telefone/session_id/erros sensíveis.
- Mitigação aplicada: redaction central (`mask_identifier`, `sanitize_error_message`).

### Médio
1. Abuso por flood de endpoints sensíveis
- Mitigação: rate limiting em `/whatsapp/connect`, `/whatsapp/qrcode`, `/webhooks/whatsapp`, `/auth/login`.

2. Dependências vulneráveis (supply chain)
- Mitigação aplicada e validada: `pip-audit` limpo; `npm` high/critical mitigados com atualização de `next` e override de `fast-uri`.
- Estado atual: Dependabot remoto com `0 high` e `0 critical` (`12 medium`, `1 low`).
- Pendência remanescente: tratamento contínuo de medium/low em ciclo de hardening.

### Baixo
1. Configuração fraca por ambiente (headers/CORS)
- Mitigação: headers de segurança configuráveis + CORS com métodos explícitos + documentação no README.

## Plano de mitigação por risco
- Alto/IDOR: testes negativos cross-tenant em endpoints WhatsApp.
- Alto/Replay: manter validação anti-replay e monitoramento de eventos recusados.
- Alto/PII: manter testes de não exposição e revisão contínua de logs.
- Médio/Supply chain: triagem contínua Dependabot para redução incremental de medium/low.

## Critério de fechamento atendido
- Riscos altos mapeados com mitigação implementada e validada por testes.
- Sem bloqueadores high/critical no Dependabot remoto.
- Riscos residuais registrados como monitoramento operacional contínuo, sem impedimento para fechamento da Fase 6.8.

## Evidências associadas
- Testes de webhook/segurança e rate limiting no backend.
- Ajustes de redaction e headers de segurança.
- Registro de supply chain em `security/resolved/2026-06-09-supply-chain-audit-findings.md`.
