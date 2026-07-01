# Plano de Implementação: Etapa Solicita Análise IA — Frontend

Objetivo: Implementar integração frontend com o backend assíncrono de análise IA, incluindo polling de status, atualização incremental de leads e feedback visual de progresso e erros.

## Escopo e ponto de partida

- Backend assíncrono já implementado (endpoints 202 Accepted, worker, fila no banco).
- Etapa alvo: integração frontend com endpoints de análise, polling, UX incremental.
- Fora de escopo: mudanças de design system ou alterações UX não relacionadas ao fluxo de análise.

## Dependências explícitas

- [x] D1. Backend com endpoints `POST /leads/{id}/analyze`, `POST /leads/analyze-all`, `GET /leads/analyze/status` implementados e documentados.
- [x] D2. ARCHITECTURE.md e CUSTOMER_JOURNEY_SEQUENCE_DIAGRAMS.md atualizados com novo fluxo assíncrono.

## Fase 1 - Integração com frontend (Polling)

- [x] 1.1 Ajustar chamadas de rede no `frontend/src/lib/api.ts` para os novos endpoints que retornam apenas `202`.
- [x] 1.2 Criar rotina de polling silencioso (a cada 3-5 segundos) no endpoint de status enquanto houver leads sendo processados.
- [x] 1.3 Atualizar a interface gradativamente: exibir labels ou ícones de "Concluído" nos leads um a um, alimentando a tela sem travar a navegação.
- [x] 1.4 Exibir feedback visual se a análise de algum lead específico cair em erro final (`failed`).

## Fase 2 - Testes e validação

- [x] 2.1 Validar chamadas de API com o backend assíncrono.
- [x] 2.2 Testar polling com diferentes cenários de latência.
- [x] 2.3 Executar checks de qualidade (lint/type-check) no frontend.

## Fase 3 - Documentação e encerramento

- [x] 3.1 Atualizar README.md se houver mudança de comportamento público.
- [x] 3.2 Mover plano para `completed/` e refletir no `PLAN-INDEX.md`.

## Ordem de execução (uma tarefa por vez)

1. Fase 1 completa
2. Fase 2 completa
3. Fase 3 completa

## Critérios de saída

- [x] Frontend enfileira análises corretamente e exibe feedback `202 Accepted`.
- [x] Polling atualiza incrementalmente a interface conforme leads terminam.
- [x] Erros exibem feedback visual orientado a ação.
- [x] Testes e checks de qualidade passando sem regressão.
- [x] Documentação atualizada conforme necessário.
