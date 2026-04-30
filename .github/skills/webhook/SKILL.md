# Skill: Webhook

## Quando usar
- Sempre que a tarefa envolver endpoints de webhook, ingestão de dados externos ou validação de assinaturas.

## Padrões
- Endpoints de webhook devem ser seguros (validação de assinatura HMAC em produção).
- Ignore eventos de contatos com status `converted` ou `lost`.
- Salve apenas mensagens de leads `active`.
- Teste ingestão com payloads reais e mocks.

## Armadilhas comuns
- Não validar assinatura em produção.
- Salvar mensagens de leads não ativos.
- Não tratar tipos de mensagem (texto, imagem, áudio, etc).

## Links úteis
- [copilot-instructions.md](../../instructions/copilot-instructions.md)
- [memories/gestor-leads.md](../../../memories/gestor-leads.md)
