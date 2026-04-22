
---
name: docker
description: Skill para Dockerfile, docker-compose, rebuilds e troubleshooting de containers.
whenToUse:
	- Sempre que a tarefa envolver Dockerfile, docker-compose, rebuilds ou troubleshooting de containers.
patterns:
	- Sempre rode docker compose up --build -d após alterar dependências.
	- Use volumes para hot-reload no backend.
	- Valide build e funcionamento do backend e frontend em containers.
pitfalls:
	- Não rebuildar após mudar dependências.
	- Não validar funcionamento dos serviços após build.
	- Não atualizar documentação de variáveis de ambiente.
links:
	- label: Instruções Copilot
		url: ../../instructions/copilot-instructions.md
	- label: Memórias do domínio
		url: ../../memories/repo/gestor-leads.md
---
