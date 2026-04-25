# Skill: Tenant

## Quando usar
- Sempre que a tarefa envolver multi-tenancy, configuração ou isolamento de dados por tenant.

## Padrões
- Cada tenant possui configuração própria de funil e dados isolados.
- Atualize e valide sempre o JSON de configuração do funil.
- Teste acesso e restrição de dados entre tenants.

## Armadilhas comuns
- Vazamento de dados entre tenants.
- Não validar configuração do funil após edição.
- Não atualizar exemplos de configuração em `.prompts/plano.md`.

## Links úteis
- [copilot-instructions.md](../../instructions/copilot-instructions.md)
- [memories/gestor-leads.md](../../../memories/gestor-leads.md)
