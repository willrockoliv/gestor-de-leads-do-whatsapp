# Guia de Testes

## Como rodar todos os testes
- Backend: `pytest`
- Frontend: `npm test`
- E2E: `npx playwright test`

## Como criar novos testes
- Siga convenções de nomeação: `test_<feature>.py` ou `<feature>.spec.ts`
- Use mocks para dependências externas.
- Testes de integração usam SQLite in-memory.

## CI
- Todos os testes são executados em cada push/PR.
- Corrija falhas antes de dar merge.

## Dicas
- Priorize TDD.
- Sempre cubra casos de erro e borda.
