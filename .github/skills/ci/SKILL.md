
---
name: ci
description: Skill para integração contínua, configuração e troubleshooting de pipelines CI/CD.
whenToUse:
	- Sempre que a tarefa envolver configuração, manutenção ou troubleshooting de pipelines CI/CD.
patterns:
	- Rode todos os testes automatizados em cada push/PR.
	- Valide build do Docker e deploy do frontend.
	- Registre falhas e logs relevantes para troubleshooting.
pitfalls:
	- Não rodar todos os testes no pipeline.
	- Não validar build do Docker após mudanças em dependências.
	- Não registrar logs de falha para análise posterior.
links:
	- label: Instruções Copilot
		url: ../../instructions/copilot-instructions.md
	- label: Memórias do domínio
		url: ../../memories/gestor-leads.md
---
