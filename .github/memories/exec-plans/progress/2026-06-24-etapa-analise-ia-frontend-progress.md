# Progresso - Etapa Análise IA Frontend (2026-06-24)

Plano: `.github/memories/exec-plans/completed/2026-06-24-etapa-analise-ia-frontend.md`
Data de início: 2026-06-24
Data de conclusão: 2026-07-01
Status: Concluído

## Status da implementação

- Plano criado como placeholder.
- Backend assíncrono concluído e frontend iniciado para preparação de contrato.
- Ajustes de base concluídos para habilitar a Fase 1 (integração/polling) sem retrabalho de contrato.
- Fase de integração com polling concluída nas telas de Leads, Lead Detail e Dashboard.

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

- Plano concluído. Próximo passo recomendado: acompanhar métricas de UX e volume de polling em produção para ajuste fino do intervalo.

## Atualização 2026-07-01 - Implementação concluída

### Implementações realizadas

- Polling silencioso implementado no frontend com intervalo de 4 segundos:
	- `frontend/src/app/(authenticated)/leads/page.tsx`
	- `frontend/src/app/(authenticated)/leads/[id]/page.tsx`
	- `frontend/src/app/(authenticated)/dashboard/page.tsx`
- Atualização incremental de estado por lead durante processamento:
	- transições `pending`/`processing`/`completed`/`failed` refletidas sem travar navegação.
	- limpeza de `is_processing` quando job finaliza.
- Feedback visual de conclusão e erro:
	- label de "Análise concluída" na lista de leads.
	- mensagem de erro final por lead (`analysis_error`) e toast quando o status final é `failed`.
- Polling de detalhe por lead:
	- uso de `GET /leads/{id}/analyze/status` para sincronizar status no detalhe.
	- refresh automático de dados do lead quando análise conclui para refletir resumo/score atualizados.
- Documentação atualizada:
	- `README.md` com comportamento de polling/feedback da UI.
	- `.github/ARCHITECTURE.md` com nota de integração de polling no frontend.

### Validação

- `docker compose exec frontend npm run lint` sem erros.
- `docker compose exec frontend npx tsc --noEmit` sem erros.
- Navegação manual em rotas autenticadas validada no navegador integrado (login, dashboard, leads e detalhe).

## Aprendizados

- Para evitar falso positivo de lint (`react-hooks/set-state-in-effect`), foi necessário remover `setState` síncrono dentro de `useEffect` e derivar os ids monitorados dentro do próprio ciclo de polling.
- O endpoint agregado de status (`/leads/analyze/status`) combinado com endpoint por lead (`/leads/{id}/analyze/status`) reduz custo de atualização e melhora o feedback de erro final sem chamadas excessivas.

## Débitos técnicos

- Extrair a lógica de polling para um hook compartilhado (ex.: `useAnalysisPolling`) para reduzir duplicação entre Dashboard e Leads.
- Consolidar estratégia de deduplicação de toasts de falha para sessão inteira, não apenas por ciclo ativo em memória.

## Dependências

- Endpoints backend assíncrono: `POST /leads/{id}/analyze`, `POST /leads/analyze-all`, `GET /leads/analyze/status`.
- Documentação backend: ARCHITECTURE.md e CUSTOMER_JOURNEY_SEQUENCE_DIAGRAMS.md atualizados.

## Decisões importantes

- Frontend iniciou integração após contrato backend estabilizado e documentado.
- Intervalo de polling fixado em 4 segundos (dentro da janela 3-5s do plano), priorizando responsividade sem agressividade excessiva.
- Atualização incremental prioriza experiência de continuidade da tela (sem refresh total da listagem a cada ciclo).
