
---
name: analysis
description: Skill para análise de leads, atualização de score, resumo de conversas e dicas qualitativas usando LLM.
whenToUse:
	- Sempre que a tarefa envolver análise de leads, atualização de score, resumo de conversas ou dicas qualitativas.
patterns:
	- Análise é disparada manualmente ou em lote.
	- Use locks otimizados para evitar double-submit.
	- Resposta da LLM deve conter: temperature_score, current_stage, conversation_summary, qualitative_tips, suggested_reply.
	- Indique falhas de análise visualmente no frontend.
pitfalls:
	- Não liberar lock após erro.
	- Não indicar falha de análise ao usuário.
	- Não validar JSON de resposta da LLM.
links:
	- label: Instruções Copilot
		url: ../../instructions/copilot-instructions.md
	- label: Memórias do domínio
		url: ../../memories/repo/gestor-leads.md
---
