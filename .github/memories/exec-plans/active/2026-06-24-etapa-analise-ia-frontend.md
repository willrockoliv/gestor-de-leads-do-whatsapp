# Plano de Implementação: Etapa Solicita Análise IA — Frontend

Objetivo: Implementar integração frontend com o backend assíncrono de análise IA, incluindo polling de status, atualização incremental de leads e feedback visual de progresso e erros.

## Escopo e ponto de partida

- Backend assíncrono já implementado (endpoints 202 Accepted, worker, fila no banco).
- Etapa alvo: integração frontend com endpoints de análise, polling, UX incremental.
- Fora de escopo: mudanças de design system ou alterações UX não relacionadas ao fluxo de análise.

## Dependências explícitas

- [ ] D1. Backend com endpoints `POST /leads/{id}/analyze`, `POST /leads/analyze-all`, `GET /leads/analyze/status` implementados e documentados.
- [ ] D2. ARCHITECTURE.md e CUSTOMER_JOURNEY_SEQUENCE_DIAGRAMS.md atualizados com novo fluxo assíncrono.

## Fase 1 - Integração com frontend (Polling)

- [ ] 1.1 Ajustar chamadas de rede no `frontend/src/lib/api.ts` para os novos endpoints que retornam apenas `202`.
- [ ] 1.2 Criar rotina de polling silencioso (a cada 3-5 segundos) no endpoint de status enquanto houver leads sendo processados.
- [ ] 1.3 Atualizar a interface gradativamente: exibir labels ou ícones de "Concluído" nos leads um a um, alimentando a tela sem travar a navegação.
- [ ] 1.4 Exibir feedback visual se a análise de algum lead específico cair em erro final (`failed`).

## Fase 2 - Testes e validação

- [ ] 2.1 Validar chamadas de API com o backend assíncrono.
- [ ] 2.2 Testar polling com diferentes cenários de latência.
- [ ] 2.3 Executar checks de qualidade (lint/type-check) no frontend.

## Fase 3 - Documentação e encerramento

- [ ] 3.1 Atualizar README.md se houver mudança de comportamento público.
- [ ] 3.2 Mover plano para `completed/` e refletir no `PLAN-INDEX.md`.

## Ordem de execução (uma tarefa por vez)

1. Fase 1 completa
2. Fase 2 completa
3. Fase 3 completa

## Critérios de saída

- [ ] Frontend enfileira análises corretamente e exibe feedback `202 Accepted`.
- [ ] Polling atualiza incrementalmente a interface conforme leads terminam.
- [ ] Erros exibem feedback visual orientado a ação.
- [ ] Testes e checks de qualidade passando sem regressão.
- [ ] Documentação atualizada conforme necessário.
