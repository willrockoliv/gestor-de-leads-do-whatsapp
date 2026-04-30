
---
name: autenticacao
description: Skill para autenticação de usuários, JWT, proteção de endpoints e testes de autenticação.
whenToUse:
	- Sempre que a tarefa envolver rotas, lógica ou testes de autenticação (ex: /auth/login, JWT, proteção de endpoints).
patterns:
	- Use JWT para autenticação de usuários.
	- Middleware de autenticação via dependency get_current_user.
	- Teste fluxos de login, registro e acesso autenticado.
	- Atualize templates e exemplos de payloads em .prompts/plano.md e .prompts/progresso.md.
pitfalls:
	- Esquecer de validar tokens após alterações.
	- Não testar casos de erro (token inválido, expirado, etc).
	- Não atualizar documentação de endpoints protegidos.
links:
	- label: Instruções Copilot
		url: ../../instructions/copilot-instructions.md
	- label: Memórias do domínio
		url: ../../memories/gestor-leads.md
---
