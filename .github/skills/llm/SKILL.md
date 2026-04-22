# Skill: LLM (Inteligência Artificial)

## Quando usar
- Sempre que a tarefa envolver prompts, integração, parsing ou validação de respostas de LLMs (OpenAI, Anthropic, Google, etc).

## Padrões
- Integração via biblioteca agnóstica (`litellm`).
- Prompts devem ser dinâmicos, incluindo contexto do funil e histórico de mensagens.
- Resposta da LLM deve ser JSON validado por Pydantic.
- Trate erros de parsing e falhas de API com try/finally para liberar locks.

## Armadilhas comuns
- Não validar o JSON retornado pela LLM.
- Não tratar timeouts ou falhas de API.
- Esquecer de atualizar exemplos de prompts/resultados em `.prompts/plano.md`.

## Links úteis
- [copilot-instructions.md](../../instructions/copilot-instructions.md)
- [memories/repo/gestor-leads.md](../../../memories/repo/gestor-leads.md)
