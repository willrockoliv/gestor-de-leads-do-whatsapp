# Skill: Funil de Vendas

## Quando usar
- Sempre que a tarefa envolver lógica, configuração ou visualização do funil de vendas (pipeline).

## Padrões
- Funil é configurável por tenant via JSON.
- Estrutura do funil deve ser injetada no prompt da LLM.
- Permita override manual da etapa pelo usuário.

## Armadilhas comuns
- Hardcode de etapas do funil.
- Não refletir override manual na interface.
- Não atualizar exemplos de funil em `.prompts/plano.md`.

## Links úteis
- [copilot-instructions.md](../../instructions/copilot-instructions.md)
- [memories/repo/gestor-leads.md](../../../memories/repo/gestor-leads.md)
