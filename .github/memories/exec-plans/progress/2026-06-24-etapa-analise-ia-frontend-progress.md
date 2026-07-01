# Progresso - Etapa Análise IA Frontend (2026-06-24)

Plano: `.github/memories/exec-plans/active/2026-06-24-etapa-analise-ia-frontend.md`
Data de início: 2026-06-24 (aguardando backend)
Status: Bloqueado por dependência do backend

## Status da implementação

- Plano criado como placeholder.
- Backend assíncrono concluído e frontend iniciado para preparação de contrato.
- Ajustes de base concluídos para habilitar a Fase 1 (integração/polling) sem retrabalho de contrato.

## Atualização 2026-07-01 - Preparação de contrato concluída

### Implementações realizadas

- `frontend/src/lib/api.ts` alinhado ao OpenAPI atual:
	- análise single/batch tipada para `202 Accepted` (`AnalysisJobAcceptedResponse` e `AnalyzeBatchResponse` com `total_enqueued`/`lead_ids`)
	- inclusão de tipos e funções para status assíncrono (`getAnalyzeStatus`, `getLeadAnalyzeStatus`)
	- inclusão de `analysis_status` e `analysis_error` nos modelos de lead
	- atualização do schema de status do WhatsApp para `phone` e `connected_since`
- Interações de análise ajustadas no frontend:
	- telas de lista e detalhe de leads agora tratam análise como enfileiramento (mensagem “Análise enfileirada”)
	- botões de análise respeitam estados `pending`/`processing` além de `is_processing`
	- feedback visual de erro final (`failed`) exibido na lista e no detalhe
	- dashboard ajustado para resposta de lote assíncrono (`total_enqueued`) e sinalização de falha
- Compatibilidade de templates de funil reforçada:
	- tipos em `api.ts`, onboarding e settings ajustados para suportar formato atual (`Record<string, string>`) e legado (`{ name, funnel_config }`)

### Validação

- `docker compose exec frontend npm run lint` executado sem erros.
- `docker compose exec frontend npx tsc --noEmit` executado sem erros após correção de type guards no onboarding.

### Próximo passo recomendado

- Iniciar implementação do polling silencioso (3-5s) com atualização incremental por `lead_ids` enfileirados usando `GET /leads/analyze/status`.

## Dependências

- Endpoints backend assíncrono: `POST /leads/{id}/analyze`, `POST /leads/analyze-all`, `GET /leads/analyze/status`.
- Documentação backend: ARCHITECTURE.md e CUSTOMER_JOURNEY_SEQUENCE_DIAGRAMS.md atualizados.

## Aprendizados

- A preencher quando backend estiver pronto.

## Débitos técnicos

- A preencher durante execução das fases.

## Decisões importantes

- Frontend iniciará apenas após backend estar documentado e funcional.
- Polling será implementado incrementalmente: começar com intervalo de 3-5s.
