# Skill: Integração

## Quando usar
- Sempre que a tarefa envolver integração com APIs externas (WhatsApp, LLMs, webhooks) ou comunicação entre serviços.

## Padrões
- Use webhooks seguros para ingestão de dados.
- Integração de LLM via biblioteca agnóstica (`litellm`).
- Valide assinaturas HMAC em produção.
- Documente endpoints e payloads de integração em `.prompts/plano.md`.

## Armadilhas comuns
- Esquecer de validar webhooks em ambiente real.
- Não tratar erros de comunicação com serviços externos.
- Não atualizar exemplos de payloads/documentação.

## Links úteis
- [copilot-instructions.md](../../instructions/copilot-instructions.md)
- [memories/repo/gestor-leads.md](../../../memories/repo/gestor-leads.md)
