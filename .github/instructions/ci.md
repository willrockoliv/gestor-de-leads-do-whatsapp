# Guia de Integração Contínua (CI)

## Como funciona o pipeline
- Workflows em `.github/workflows/` executam linters, type checkers e testes em cada push/PR.
- Jobs separados para lint, type-check e test.

## Como depurar falhas
- Verifique os logs do job com erro no GitHub Actions.
- Rode o comando localmente para reproduzir.
- Corrija o erro e faça novo push.

## Como adicionar novos jobs
- Edite ou crie arquivos em `.github/workflows/` seguindo exemplos existentes.
- Adicione etapas para comandos de lint, type-check ou test conforme necessário.

## Dicas
- Sempre mantenha o pipeline verde antes de mergear PRs.
