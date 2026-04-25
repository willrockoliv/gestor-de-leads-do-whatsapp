
---
name: dashboard
description: Skill para visualização, filtros, estatísticas e interface do dashboard (backend ou frontend).
whenToUse:
	- Sempre que a tarefa envolver visualização, filtros, estatísticas ou interface do dashboard (backend ou frontend).
patterns:
	- Exiba funil dinâmico conforme configuração do tenant.
	- Mostre análises da LLM, tempo de conversa e status do lead.
	- Permita filtragem e ordenação por etapa, score e status.
	- Atualize agregados em tempo real.
pitfalls:
	- Não refletir mudanças manuais de etapa/status.
	- Não atualizar estatísticas após alterações.
	- Esquecer de validar visualização após deploy.
links:
	- label: Instruções Copilot
		url: ../../instructions/copilot-instructions.md
	- label: Memórias do domínio
		url: ../../memories/gestor-leads.md
---
