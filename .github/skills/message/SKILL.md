# Skill: Message (Mensagens)

## Quando usar
- Sempre que a tarefa envolver ingestão, exibição ou processamento de mensagens de leads.

## Padrões
- Salve histórico de mensagens apenas de leads `active`.
- Ignore mensagens de leads `converted` ou `lost`.
- Suporte a múltiplos tipos de mensagem (texto, imagem, áudio, vídeo, documento).

## Armadilhas comuns
- Salvar mensagens de leads não ativos.
- Não tratar tipos de mensagem corretamente.
- Não atualizar exemplos de payloads em `.prompts/plano.md`.

## Links úteis
- [copilot-instructions.md](../../instructions/copilot-instructions.md)
- [memories/repo/gestor-leads.md](../../../memories/repo/gestor-leads.md)
