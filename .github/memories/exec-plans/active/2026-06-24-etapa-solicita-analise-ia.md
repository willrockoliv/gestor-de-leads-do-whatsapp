# Plano de Implementacao: Etapa Solicita Analise IA — Backend

Objetivo: Implementar com seguranca a etapa da jornada no backend em que o usuario solicita analise IA de leads, com foco em processamento assincrono (fila no banco) para respeitar limites de hardware e garantir atualizacao em tempo real no frontend, utilizando LiteLLM como Gateway e Ollama como motor de IA local.

## Escopo e ponto de partida

- Jornada ja implementada ate: ingestao de mensagens e dados de leads salvos.
- Etapa alvo desta execucao: backend da etapa "Solicita analise IA" (worker, persistencia, confiabilidade).
- Fora de escopo: integracao com frontend (sera plano separado), mudancas de UX nao relacionadas ao fluxo de analise.

## Dependencias explicitas

- [ ] D1. Subir e configurar o LiteLLM (LLM Gateway) para padronizar rotas e gerenciar o fallback entre Ollama (local) e Cloud (OpenAI).
- [ ] D2. Confirmar modelagem e relacoes de dados (`Lead`, `Message`, `Analysis`) prontas para persistencia do resultado.
- [ ] D3. Adicionar campo `analysis_status` (ex: idle, pending, processing, completed, failed) na tabela de Leads para controle de fila.
- [ ] D4. Definir limites de concorrencia absolutos (worker assincrono = 1) para evitar gargalos de CPU na Evolution-API.

## Fase 1 - Contrato funcional da analise (Assincrono)

- [ ] 1.1 Definir contrato `POST /leads/{id}/analyze`: marca o lead como `pending` e retorna `202 Accepted` com id do job.
- [ ] 1.2 Definir contrato `POST /leads/analyze-all`: marca lote de leads selecionados como `pending` e retorna `202 Accepted` informando a quantidade enfileirada.
- [ ] 1.3 Criar endpoint `GET /leads/analyze/status`: retorna a contagem atualizada de status (pending, processing, completed, failed) e quais ids foram concluidos.
- [ ] 1.4 Documentar contrato de resposta em schemas Pydantic e em docstrings OpenAPI.

## Fase 2 - Pipeline de analise em Background (Worker)

- [ ] 2.1 Implementar worker assincrono ou job loop (no backend) que busca estritamente 1 lead por vez com status `pending`.
- [ ] 2.2 Alterar status do lead de `pending` para `processing` (lock no banco) antes de iniciar a inferencia.
- [ ] 2.3 Orquestrar contexto: coletar mensagens truncadas (limite maximo de 1000 tokens) + funil do tenant.
- [ ] 2.4 Chamar o LiteLLM com timeout restrito, retries controlados e trilha de logs limpa (sem PII).
- [ ] 2.5 Validar resposta com Output Parser robusto (capaz de limpar/corrigir JSONs malformados por LLMs menores antes de falhar).
- [ ] 2.6 Persistir objeto `Analysis`, atualizar campos no lead e mudar status para `completed` (ou `failed`).

## Fase 3 - Confiabilidade operacional

- [ ] 3.1 Implementar watchdog para resetar locks zombies: reverter leads travados em `processing` ha mais de 5 minutos de volta para `pending`.
- [ ] 3.2 Definir padrao de erros no banco de dados para justificar o status `failed` (ex: falha na nuvem, timeout local, json quebrado sem conserto).
- [ ] 3.3 Adicionar metricas e logs estruturados para observabilidade do tamanho da fila e taxa de resolucao.

## Fase 4 - Testes e validação

- [ ] 4.1 Cobrir worker com testes unitários focados na estabilidade da extração JSON e tratamento de timeouts.
- [ ] 4.2 Cobrir endpoints com testes de integração verificando as trocas de estado corretas (pending -> processing -> completed).
- [ ] 4.3 Executar regressão (`pytest`) validando impactos indiretos.
- [ ] 4.4 Checar qualidade (lint/type-check).

## Fase 5 - Documentação e encerramento

- [ ] 5.1 Atualizar `ARCHITECTURE.md` com novo fluxo assíncrono: endpoints `POST /leads/{id}/analyze`, `POST /leads/analyze-all`, `GET /leads/analyze/status`, worker loop, campos `analysis_status` e status transitions.
- [ ] 5.2 Atualizar `CUSTOMER_JOURNEY_SEQUENCE_DIAGRAMS.md` com diagrama de sequência refletindo o novo fluxo (202 Accepted, fila no banco, worker, polling do frontend).
- [ ] 5.3 Mover plano para `completed/` e refletir no `PLAN-INDEX.md`.

## Ordem de execucao (uma tarefa por vez)

1. Fase 1 completa
2. Fase 2 completa
3. Fase 3 completa
4. Fase 4 completa
5. Fase 5 completa

## Criterios de saida

- [ ] Endpoints individuais e em lote enfileiram corretamente e retornam `202 Accepted`.
- [ ] Worker processa 1 lead por vez, respeitando lock e tratando falhas sem travar.
- [ ] Falhas da LLM retornam erro padronizado e não deixam lock preso.
- [ ] Watchdog reseta locks zombies conforme esperado.
- [ ] Testes de unidade/integração cobrindo fluxos críticos passando sem regressão.
- [ ] Documentação atualizada em ARCHITECTURE.md e CUSTOMER_JOURNEY_SEQUENCE_DIAGRAMS.md refletindo novo fluxo assíncrono.

---

## Anexo A - Plano tecnico para modelo local e Gateway (VPS 8 GB RAM)

Objetivo do anexo: configurar ambiente local ultra-otimizado para inferencia com LLMs pequenos (SLMs) e fallback garantido via LiteLLM.

### Premissas de capacidade e restricoes

- [ ] A1. Considerar o limite total de 8 GB de RAM em servidor compartilhado com DB e Evolution-API.
- [ ] A2. Reservar no maximo absoluto 2.5 GB a 3 GB para o container da IA.
- [ ] A3. Forcar execucao concorrente do Ollama em 1 requisicao por vez (zero paralelismo via hardware).
- [ ] A4. Utilizar modelos SLM da faixa de 1B a 3B de parametros.

### Fase A - Runtime Docker Local (Ollama + LiteLLM)

- [ ] A.1 Adicionar `ollama` ao `docker-compose.yml` mapeando volume persistente e aplicando limites severos de recurso (ex: `OLLAMA_NUM_PARALLEL=1`, `OLLAMA_MAX_VRAM=0`).
- [ ] A.2 Adicionar `litellm` ao `docker-compose.yml` conectado à mesma rede privada do Ollama.
- [ ] A.3 Validar comunicacao entre os containers (Backend -> LiteLLM -> Ollama).

### Fase B - Setup de Modelos e Fallback

- [ ] B.1 Configurar LiteLLM `config.yaml` com rota principal apontando para o modelo local (ex: `ollama/qwen2.5:1.5b` ou `ollama/llama3.2:1b`).
- [ ] B.2 Configurar rota de fallback no LiteLLM para um provedor Cloud confiavel e barato (ex: `groq/llama3-8b-8192` ou `openai/gpt-4o-mini`).
- [ ] B.3 Ajustar variaveis do backend `LLM_API_BASE` e `LLM_API_KEY` para apontar diretamente ao container do LiteLLM (o backend ignora o Ollama).

### Fase C - Profiling de inferencia e Prompting

- [ ] C.1 Aplicar restricao rigida de contexto antes do envio (cortar historico antigo para manter KV Cache baixo).
- [ ] C.2 Limitar o parametro `max_tokens` (saida) para ~200, garantindo que o calculo termine rapido.
- [ ] C.3 Otimizar System Prompt para focar apenas na estrutura da resposta esperada (JSON Schema padrao).

### Fase D - Benchmark e decisao Go/No-go

- [ ] D.1 Rodar teste de estresse real com 30 leads usando apenas o Ollama (sem nuvem).
- [ ] D.2 Monitorar o host (htop) garantindo sobrevivencia das portas do WhatsApp durante 100% de uso da CPU pelos cores de IA.
- [ ] D.3 Definir criterio de sucesso Go/No-go: Analise unitaria em menos de 30s; Nenhum OOM (Out of Memory) no servidor; Taxa de falhas de JSON dependentes de fallback em < 15%.
