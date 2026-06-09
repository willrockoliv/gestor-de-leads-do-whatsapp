# Plano de Implementacao — Desacoplamento do Provider WhatsApp

Objetivo: Reduzir o acoplamento com WAHA e habilitar troca de provider com injeção de dependência no backend, sem quebrar os endpoints atuais.

Dependencias:
- Base funcional da Fase 6 concluida ate 6.6
- Testes atuais de WhatsApp e webhook como baseline de regressao

## Fase 1 — Baseline e Contrato (bloqueante)
Dependencia explicita:
- Deve concluir antes das Fases 2, 3 e 4

- [x] Consolidar baseline de comportamento atual (connect, qrcode, status, webhook, conflito CORE)
- [x] Definir contrato unico do provider (operacoes de sessao + normalizacao de webhook)
- [x] Definir erros de dominio para integracao externa e mapeamento para HTTP
- [x] Definir mapeamento central de status externo para SessionStatus interno

## Fase 2 — Adapter WAHA Dedicado
Dependencia explicita:
- Requer Fase 1 concluida

- [x] Extrair detalhes WAHA para adapter dedicado (endpoints, headers, payloads)
- [x] Isolar retry/backoff e tratamento de indisponibilidade no adapter
- [x] Preservar comportamento CORE e PLUS sem alterar contrato publico
- [x] Garantir logs sem vazamento de segredo e sem PII desnecessaria

## Fase 3 — Injecao de Dependencia no FastAPI
Dependencia explicita:
- Requer Fase 2 concluida

- [x] Criar factory/dependency do provider por configuracao
- [x] Remover instancia manual do servico nos routers de WhatsApp
- [x] Usar o mesmo provider no loop de sync
- [x] Permitir override do provider em testes

## Fase 4 — Webhook Agnostico a Provider
Dependencia explicita:
- Requer Fases 1 e 2 concluidas
- Pode executar em paralelo com a Fase 3 apos contrato estabilizado

- [x] Separar validacao de transporte (router) da normalizacao de payload (provider)
- [x] Definir evento interno normalizado para ingestao
- [x] Manter validacoes de seguranca (assinatura, sessao, tenant)
- [x] Preparar extensao para anti-replay e idempotencia

## Fase 5 — Testes de Regressao e Arquitetura
Dependencia explicita:
- Requer Fases 2, 3 e 4 concluidas

- [x] Atualizar testes para validar contrato do provider
- [x] Manter E2E com mock WAHA para regressao comportamental
- [x] Adicionar testes de override de provider via dependency_overrides
- [x] Adicionar testes de falha (provider fora, payload invalido, conflito CORE)
- [x] Executar suite focal e suite completa do backend

## Fase 6 — Documentacao e Governanca do Plano
Dependencia explicita:
- Requer Fase 5 concluida

- [x] Atualizar ARCHITECTURE.md com desenho provider-agnostico
- [x] Atualizar README.md com configuracao de provider e troubleshooting
- [x] Atualizar arquivo de progresso com aprendizados, debitos e decisoes
- [x] Revisar criterio de saida e status final do plano

## Criterio de Saida
- [x] Router de WhatsApp sem instancia direta de implementacao concreta
- [x] Detalhes WAHA confinados ao adapter
- [x] Testes de WhatsApp e webhook sem regressao
- [x] Troca de provider viavel por configuracao sem alterar endpoints
