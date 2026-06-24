# Progresso - Etapa Análise IA Backend (2026-06-24)

Plano: `.github/memories/exec-plans/active/2026-06-24-etapa-solicita-analise-ia.md`
Data de início: 2026-06-24
Status: Em planejamento

## Status da implementacao

- Plano criado, revisado com feedback do Gemini e indexado.
- Execucao ainda nao iniciada.

## Aprendizados e decisoes arquiteturais (Revisao 2026-06-24)

### Arquitetura redefinida para assincronismo

A arquitetura foi reformulada de um modelo sincrono "esperar a resposta da IA" para um modelo assincrono baseado em fila no banco de dados:

- `POST /leads/{id}/analyze` e `POST /leads/analyze-all` agora retornam `202 Accepted` imediatamente em vez de bloquear.
- Novo endpoint `GET /leads/analyze/status` fornece polling de progresso em tempo real.
- Worker em background (job loop) processa 1 lead por vez, alterando status no banco: `pending` → `processing` → `completed` ou `failed`.
- Frontend faz polling a cada 3-5s e atualiza incrementalmente a interface conforme cada lead termina.

**Beneficio:** Evita timeouts em conexoes HTTP longas, respeita limite absoluto de concorrencia (1 inferencia por vez) e melhora UX ao mostrar progresso em tempo real.

### LiteLLM como padrao de Gateway

- LiteLLM centraliza a comunicacao com LLM local (Ollama) e provedor cloud (fallback).
- Backend aponta apenas para `LLM_API_BASE` (container LiteLLM), nao conhece Ollama ou cloud diretamente.
- LiteLLM config.yaml define rota principal (Ollama local) e rota de fallback (Groq/OpenAI).

**Beneficio:** Desacoplamento, fallback transparente, metricas/logging centralizados, preparacao para futuros providers.

### Output Parser robusto para SLMs

- Modelos pequenos (1B-3B) geram JSON malformados com frequencia.
- Adicionar biblioteca tipo `instructor` para limpar/corrigir JSONs antes de rejeitar como falha.
- Reduz taxa de fallback desnecessario para cloud.

**Beneficio:** Maior taxa de sucesso local, economia de custo.

### Context window agressivo

- Limitar contexto a 1000 tokens antes do envio para reduzir KV Cache.
- `max_tokens` output limitado a ~200.
- Otimizar System Prompt para JSON Schema apenas.

**Beneficio:** Latencia previsivel mesmo em CPU fraca.

## Debitos tecnicos

- Nenhum identificado em planejamento. A ser preenchido durante execucao das fases.

## Decisoes importantes

- Arquitetura: assincronismo com fila no banco em vez de sincronismo HTTP longo.
- Gateway: LiteLLM centralizado para fallback transparente local/cloud.
- Modelo de dados: campo `analysis_status` (idle, pending, processing, completed, failed) adicionado a Lead.
- Frontend: polling em lugar de aguardar resposta, atualizacoes incrementais de leads conforme terminam.
- Estrategia de infraestrutura: local-first com modelo 1B-3B quantizado, fallback confiavel para nuvem barata (Groq).
- Concorrencia: estritamente 1 (worker serial) para respeitar 8 GB de RAM e manter Evolution-API ativa.
