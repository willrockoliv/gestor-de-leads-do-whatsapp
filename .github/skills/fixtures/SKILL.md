# Skill: Fixtures (Testes)

## Quando usar
- Sempre que a tarefa envolver criação, manutenção ou uso de fixtures em testes automatizados.

## Padrões
- Use fixtures em `tests/conftest.py` para setup de banco, clientes HTTP e mocks.
- Prefira SQLite in-memory para integração.
- Documente e reutilize fixtures para evitar duplicidade.

## Armadilhas comuns
- Fixtures com escopo inadequado (ex: session vs function).
- Não isolar dependências externas.
- Não atualizar fixtures após mudanças em models/schemas.

## Links úteis
- [copilot-instructions.md](../../instructions/copilot-instructions.md)
- [memories/repo/gestor-leads.md](../../../memories/repo/gestor-leads.md)
