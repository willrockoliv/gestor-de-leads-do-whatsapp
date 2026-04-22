# Skill: Lock (Concorrência e Locks)

## Quando usar
- Sempre que a tarefa envolver controle de concorrência, optimistic lock, double-submit ou watchdog de processamento.

## Padrões
- Use coluna `is_processing` para lock otimista.
- Rejeite requisições duplicadas com HTTP 409.
- Libere lock com try/finally após processamento.
- Implemente watchdog para resetar locks presos (>5min).

## Armadilhas comuns
- Não liberar lock após erro.
- Não rejeitar double-submit corretamente.
- Não registrar logs de reset de lock.

## Links úteis
- [copilot-instructions.md](../../instructions/copilot-instructions.md)
- [memories/repo/gestor-leads.md](../../../memories/repo/gestor-leads.md)
