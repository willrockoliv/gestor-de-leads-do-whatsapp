# Skill: Modelagem de Dados

## Quando usar
- Sempre que a tarefa envolver criação, alteração ou validação de models, schemas ou migrations.

## Padrões
- Models SQLAlchemy em `app/models/`, schemas Pydantic em `app/schemas/`.
- Use enums para status e tipos fixos.
- Migrations via Alembic, sempre versionadas em `alembic/versions/`.
- Teste relacionamentos e constraints em `tests/`.

## Armadilhas comuns
- Esquecer de gerar/aplicar migration após alterar models.
- Não validar constraints e relacionamentos em testes.
- Não atualizar documentação de campos obrigatórios.

## Links úteis
- [copilot-instructions.md](../../instructions/copilot-instructions.md)
- [memories/repo/gestor-leads.md](../../../memories/repo/gestor-leads.md)
