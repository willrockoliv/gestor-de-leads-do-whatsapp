# Checklist — Hardening em Desenvolvimento (Fase 8)

Objetivo: validar os requisitos de hardening em dev antes de fechar o plano.

## Pré-condições
- [x] Serviços ativos com `docker compose up -d`
- [x] Banco com migrações aplicadas
- [x] Ambiente carregado com `.env`

## 8.1 Rate limit (webhook + análise)
- [x] Confirmar `WEBHOOK_RATE_LIMIT` e `WEBHOOK_RATE_LIMIT_WINDOW_SECONDS` no `.env`
- [x] Confirmar `ANALYSIS_RATE_LIMIT` e `ANALYSIS_RATE_LIMIT_WINDOW_SECONDS` no `.env`
- [x] Validar suporte a `429` e header `Retry-After` nos handlers de:
  - [x] `POST /webhooks/whatsapp`
  - [x] `POST /leads/{id}/analyze`
  - [x] `POST /leads/analyze-all`

## 8.2 CORS em dev
- [x] Confirmar `CORS_ORIGINS` no `.env` para frontend local
- [x] Validar preflight `OPTIONS` e request autenticada via frontend local

## 8.3 Logging estruturado em JSON
- [x] Confirmar `LOG_JSON=true` e `LOG_LEVEL=INFO` (ou nível desejado)
- [x] Validar que logs de API saem em JSON com campos mínimos:
  - [x] `timestamp`
  - [x] `level`
  - [x] `logger`
  - [x] `message`

## 8.4 Health check
- [x] `GET /health` retorna `200` e body com `status=ok`

## 8.5 Variáveis de ambiente documentadas
- [x] `.env.example` atualizado com variáveis de rate limit de análise e logging

## Verificações de qualidade
- [x] `pytest` sem regressões
- [x] `ruff check .` sem erros novos

## Encerramento
- [x] Atualizar progresso do plano para refletir conclusão da Fase 8
- [x] Registrar qualquer pendência fora do escopo em memória/roadmap

## Evidências
- Implementações concluídas: rate limit em análise, logging JSON configurável, variáveis em `.env.example` e documentação sincronizada.
- Verificação de regressão executada: `pytest tests/test_analysis_unit.py tests/test_analysis_integration.py tests/test_health.py -q` (17 passed).
- Pendência fora de escopo: deploy em produção permanece adiado por decisão do plano.
