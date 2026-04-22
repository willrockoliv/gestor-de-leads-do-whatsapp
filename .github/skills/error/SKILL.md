# Skill: Error Handling (Tratamento de Erros)

## Quando usar
- Sempre que a tarefa envolver tratamento de exceções, validação de respostas ou logs de falha.

## Padrões
- Use try/finally para garantir liberação de recursos (locks, conexões).
- Valide respostas de APIs e LLMs antes de processar.
- Registre logs de erro detalhados para troubleshooting.

## Armadilhas comuns
- Não tratar exceções em fluxos críticos.
- Não registrar logs de falha.
- Não validar dados antes de processar.

## Links úteis
- [copilot-instructions.md](../../instructions/copilot-instructions.md)
- [memories/repo/gestor-leads.md](../../../memories/repo/gestor-leads.md)
