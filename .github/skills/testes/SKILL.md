# Skill: Testes

## Quando usar
- Sempre que a tarefa envolver criação, manutenção ou execução de testes em `tests/` ou validação de funcionalidades.

## Padrões
- Use pytest e pytest-asyncio.
- Testes unitários usam funções `_sync` dos serviços (sem banco de dados).
- Testes de integração usam SQLite in-memory e fixtures de `tests/conftest.py`.
- Rode todos os testes após qualquer alteração relevante: `pytest tests/ -v`.
- Siga TDD sempre que possível.

## Armadilhas comuns
- Esquecer de rodar todos os testes após mudanças.
- Não isolar dependências externas em testes unitários.
- Não atualizar contagem de testes em `.prompts/progresso.md`.

## Links úteis
- [copilot-instructions.md](../../instructions/copilot-instructions.md)
- [memories/gestor-leads.md](../../../memories/gestor-leads.md)
