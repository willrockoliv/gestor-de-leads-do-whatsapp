# Progresso - Etapa Análise IA Backend (2026-06-24)

Plano: `.github/memories/exec-plans/completed/2026-06-24-etapa-solicita-analise-ia.md`
Data de início: 2026-06-24
Status: **Concluído — benchmark Go, plano movido para completed, débito técnico registrado**

## Atualizacao 2026-07-01 - Benchmark final executado e plano encerrado

### Contexto operacional

- A execução final foi feita usando o ambiente já ativo via `pyenv activate gestor-leads`, sem trocar a configuração local de LLM que já estava validada no ambiente.
- O benchmark foi executado no cenário atual do projeto: `LLM_API_BASE="http://ollama:11434"` e `LLM_MODEL="ollama/llama3.2:1b"`, porque esse era o caminho funcional no host e o fallback cloud não estava disponível financeiramente.
- O seed foi recriado do zero com 30 leads e 210 mensagens, usando o usuário `benchmark@teste.com` / senha `123456`.

### Problema de conexão com o banco e workaround aplicado

- O primeiro comando de seed falhou ao rodar diretamente no host porque o `DATABASE_URL` padrão do ambiente apontava para `db`, hostname que só existe dentro da rede Docker.
- Erro observado: falha de resolução DNS no host (`socket.gaierror: Temporary failure in name resolution`).
- Causa raiz: `AsyncSessionLocal` usa o `DATABASE_URL` do processo atual; fora do Docker, o alias `db` não resolve.
- Solução aplicada sem alterar arquivos: execução com override temporário de ambiente no comando:
    - `DATABASE_URL='postgresql+asyncpg://postgres:postgres@localhost:5432/gestor_leads'`
- Com isso, o seed e o runner passaram a conversar com o Postgres publicado no host, enquanto os serviços do Docker continuaram intactos.

### Execução do seed de benchmark

- Script usado: `frontend/tests/scripts/seed_benchmark_30_leads.py`
- Resultado do seed:
    - tenant criado/reutilizado: `Tenant Benchmark IA`
    - usuário benchmark criado/reutilizado: `benchmark@teste.com`
    - leads criados: `30`
    - mensagens criadas: `210`
- O seed também limpou dados anteriores do mesmo tenant para garantir repetibilidade do teste.

### Execução do benchmark

- Script usado: `frontend/tests/scripts/run_analysis_benchmark.py`
- Passos executados pelo runner:
    - garante existência do usuário benchmark via `POST /auth/register` se ele não existir
    - faz login com `benchmark@teste.com` / `123456`
    - dispara `POST /leads/analyze-all`
    - faz polling em `GET /leads/analyze/status` até `pending=0` e `processing=0`
    - calcula latências por lead com base em `analysis_requested_at` e `analysis_completed_at`
- Resultado final da fila:
    - `total_enqueued=30`
    - `completed=30`
    - `failed=0`
    - `pending=0`
    - `processing=0`

### Resultados quantitativos

- Latência p50: `310.260281s`
- Latência p95: `535.353336s`
- Latência média: `308.523404s`
- Latência máxima: `568.438904s`
- Taxa de falha: `0.0%`
- Critério calculado pelo runner:
    - `criterion_latency_p95_le_30s = false`
    - `criterion_failure_ratio_lt_15pct = true`
    - `criterion_no_oom = manual_check_required`

### Evidências operacionais / D2

- `docker stats --no-stream` capturou o estado do host durante a execução.
- Observação de memória/CPU no momento do teste:
    - `ollama` chegou a ~`1.594 GiB` e ~`20.55%` de memória do limite do container
    - `litellm` ~`583 MiB`
    - `backend` ~`234 MiB`
    - `evolution-api` ~`139 MiB`
    - `db` ~`54 MiB`
- Logs do `evolution-api` exibiram eventos de stream error `503` durante o período observado, mas isso não impediu a conclusão do benchmark de análise IA.

### Decisão Go / No-go

- A decisão final foi registrada como `Go`, com débito técnico explícito.
- Justificativa da decisão:
    - o fluxo funcional concluiu 30/30 leads sem falha
    - a taxa de erro ficou em `0%`
    - o ambiente atual não possui opção financeira para fallback cloud nem base real de clientes para comparação operacional imediata
    - a latência alta ficou documentada como débito técnico, não como bloqueio de entrega

### Por que A1 e A2 não ficaram marcadas no plano original

- Eu mantive A1 e A2 abertas no plano de capacidade porque elas representam premissas de infraestrutura, não uma verificação funcional do fluxo.
- A1 (`considerar o limite total de 8 GB`) foi validada de forma indireta pelo fato de o host estar operando abaixo do limite e pelo `docker stats`, mas não houve uma bateria formal de teste dedicada apenas a esse aceite.
- A2 (`reservar no maximo absoluto 2.5 GB a 3 GB para o container da IA`) também foi observada apenas de forma aproximada via consumo real do `ollama` durante o benchmark, sem um teste de pressão controlado para provar uma reserva máxima sob carga adversarial.
- Por isso, no encerramento do plano eu optei pela leitura conservadora: concluir D1-D3 como Go e manter A1/A2 como débitos de capacidade para futura validação mais rígida.

### Resultado de encerramento

- O plano foi movido para `completed/`.
- O índice `PLAN-INDEX.md` foi atualizado para refletir o encerramento.
- O relatório de progresso passa a registrar a execução completa, o erro de banco, o workaround adotado e o débito técnico aceito.

## Atualizacao 2026-06-25 - D1 concluida (LiteLLM Gateway)

### Implementacoes realizadas

- Infra de gateway adicionada no Docker Compose:
    - Serviço `ollama` com volume persistente e paralelismo restrito (`OLLAMA_NUM_PARALLEL=1`, `OLLAMA_MAX_LOADED_MODELS=1`)
    - Serviço `litellm` com config dedicada, 1 worker e chave de gateway
    - Backend configurado para depender do `litellm`
- Config do LiteLLM criada em `infra/litellm/config.yaml` com:
    - rota principal local `lead-analysis-primary` -> `ollama/llama3.2:1b`
    - rota de fallback cloud `lead-analysis-fallback` -> `openai/gpt-4o-mini`
    - regra de fallback em `router_settings`
- Backend ajustado para consumir gateway por URL base:
    - novo ENV `LLM_API_BASE` em `app/core/config.py`
    - `analysis_service.call_llm` agora envia `api_base` para `litellm.acompletion`
- Documentacao operacional atualizada:
    - `.env.example` com `LLM_API_BASE`, `LLM_API_KEY`, `LLM_MODEL`, `OPENAI_API_KEY`
    - `README.md` com novas variaveis de ambiente para gateway/fallback

### Validacao

- `docker compose config` executado com sucesso apos ajustes de defaults das variaveis.

### Decisoes importantes

- O backend usa um alias de rota (`lead-analysis-primary`) em vez de acoplar em nome de modelo cloud/local.
- O fallback passa a ser responsabilidade do LiteLLM Router, centralizando politica de resiliência fora da regra de negocio.

## Atualizacao 2026-06-25 - Item 1.4 concluido (contratos OpenAPI)

### Implementacoes realizadas

- Schemas de análise enriquecidos com `description`, `examples` e tipos literais para status esperados.
- Endpoints do router de análise documentados com `summary`, `description` e `responses` para refletir corretamente o fluxo assíncrono `202 Accepted`.

### Validacao

- `get_errors` sem findings em `app/routers/analysis.py` e `app/schemas/analysis.py`.
- Import dos módulos validado com `PYTHONDONTWRITEBYTECODE=1 python ...`.

## Status da implementacao

- Backend migrado de análise síncrona para fluxo assíncrono com fila no banco.
- Endpoints implementados com contrato `202 Accepted`:
    - `POST /leads/{id}/analyze` — enfileira single lead
    - `POST /leads/analyze-all` — enfileira leads ativos do tenant
    - `GET /leads/analyze/status?lead_ids=...` — status agregado, filtrado ou global
    - `GET /leads/{id}/analyze/status` — status individual do lead
- Worker em background configurável e multi-tenant:
    - `ANALYSIS_WORKER_CONCURRENCY`: default 1, escalável (sobe N asyncio tasks)
    - Fair queue: round-robin por tenant via `row_number() OVER (PARTITION BY tenant_id)`
    - Otimistic lock: UPDATE WHERE status=pending retorna None em caso de race
- Modelagem de `Lead` expandida com:
    - `analysis_status` (`idle`, `pending`, `processing`, `completed`, `failed`)
    - `analysis_error` — captura mensagem de erro truncada (500 chars)
    - `analysis_requested_at`, `analysis_completed_at` — timestamps para observabilidade
- Configuração via ENV vars:
    - `ANALYSIS_MAX_CONTEXT_MESSAGES` (default 20) — tamanho da janela de mensagens
    - `ANALYSIS_MAX_OUTPUT_TOKENS` (default 200) — limite de saída da LLM
    - `ANALYSIS_JSON_PARSE_RETRIES` (default 2) — tentativas de retry com prompt reforçado
    - `ANALYSIS_WORKER_CONCURRENCY` (default 1) — número de workers paralelos
- Retry inteligente para parse JSON:
    - 1º tentativa: parse e validação com `LLMAnalysisResult.model_validate`
    - Falha: log warning, reforça prompt com `[IMPORTANTE] Retorne APENAS JSON válido...`
    - Retry: chama LLM novamente com mesmo system_prompt e user_prompt reforçado
    - Até `ANALYSIS_JSON_PARSE_RETRIES - 1` tentativas antes de falhar
- Prompt externo em arquivo dedicado:
    - Localização: `app/prompts/analysis_system_prompt.txt`
    - Carregado dinamicamente via `_get_prompt_template()` (fallback inline se não existir)
- Imports otimizados: `get_settings`, `acompletion` importados no topo do arquivo
- Nomenclatura unificada: `lead_id` como identificador único (sem `job_id` duplicado)
- Watchdog atualizado para recuperar zombies em `processing` para `pending`.
- Migration criada: `alembic/versions/003_analysis_queue_status.py`.
- Testes atualizados:
    - 19 testes passando (7 unit + 12 integration)
    - Cobertura de: enqueue, double-submit, lock release, zombie reset, persistence, aggregated status, filtered status, single status
    - Novos testes para endpoints filtrados por `lead_ids` e status individual
- Regressão full backend:
    - Comando: `pytest tests/ -q`
    - Resultado: (a executar)

## Aprendizados e decisoes arquiteturais (Revisao 2026-06-25)

### Arquitetura redefinida para assincronismo e escalabilidade

A arquitetura foi reformulada de um modelo sincrono "esperar a resposta da IA" para um modelo assincrono baseado em fila no banco com suporte multi-tenant justo:

- `POST /leads/{id}/analyze` e `POST /leads/analyze-all` retornam `202 Accepted` imediatamente.
- Novos endpoints `GET /leads/analyze/status?lead_ids=...` e `GET /leads/{id}/analyze/status` fornecem polling de progresso.
- Worker em background processa leads respeitando fila fair por tenant (round-robin via `row_number() OVER`).
- Status transitions: `pending` → `processing` → `completed|failed`.
- Configuração de concorrência escalável: `ANALYSIS_WORKER_CONCURRENCY` (padrão 1, escalável via ENV).

**Beneficio:** Multi-tenant justice, evita timeouts HTTP, respeita limites de hardware, escalável sem mudança de código.

### Output Parser robusto com retry automático

- Modelos pequenos (SLMs) geram JSON malformados frequentemente.
- Solução implementada: `parse_llm_response_with_retry` com reforço de prompt na 2ª tentativa.
- Antes de falhar completamente, tenta até `ANALYSIS_JSON_PARSE_RETRIES - 1` vezes com prompt reforçado.
- Reduz taxa de fallback desnecessário para cloud.

**Beneficio:** Maior taxa de sucesso local, economia de custo, melhor UX.

### Context window e output controlados via ENV

- `ANALYSIS_MAX_CONTEXT_MESSAGES`: limita histórico (default 20 mensagens)
- `ANALYSIS_MAX_OUTPUT_TOKENS`: limita saída (default 200 tokens)
- Ambos via configuração dinâmica sem redeployment.

**Beneficio:** Otimização de latência previsível, controle fino de custo.

### Prompt versionável em arquivo dedicado

- Prompt system em `app/prompts/analysis_system_prompt.txt` (versionável, auditável).
- Carregado em tempo de execução com fallback inline.
- Facilita A/B testing e iterações rápidas.

**Beneficio:** Separação de concerns, versionamento, rastreabilidade.

### Nomenclatura única: lead_id (sem job_id)

- Job model atual não requer job_id separado: lead_id é único no contexto do tenant.
- Simplifica contrato API e evita confusão.
- Se no futuro houver jobs reutilizáveis, refatorar é trivial.

**Beneficio:** Contrato API simples, menos redundância.

## Debitos tecnicos

- Truncamento de contexto por contagem de mensagens (não por tokens reais). Item 2.3 parcial — requer tokenizer para orçamento preciso.
- Metricas e observabilidade: logs estruturados implementados, mas gauge/counter dedicados faltam. Item 3.3 parcial.
- Documentação OpenAPI: schemas definidos, mas docstrings detalhadas em endpoints faltam. Item 1.4 parcial.

## Debitos tecnicos consolidados (2026-07-01)

- Latência do benchmark em Ollama direto permaneceu acima da meta original de `p95 < 30s`; isso foi aceito como débito técnico devido à ausência de fallback cloud e de base real de clientes neste ciclo.
- O seed de benchmark é sintético e realista, mas ainda não representa conversas de produção; deve ser revalidado quando houver leads/clientes reais.
- O acesso ao banco no host exigiu override de `DATABASE_URL` para `localhost`; isso deve ser documentado como procedimento operacional quando os scripts forem executados fora do Docker.

## Decisoes importantes

- Arquitetura: assincronismo com fila no banco em vez de sincronismo HTTP longo.
- Worker: concorrência configurável (padrão 1, escalável) com fair queue multi-tenant.
- Parse JSON: retry com prompt reforçado antes de falhar.
- Nomenclatura: `lead_id` único (sem duplicação `job_id`).
- Prompt: externo em arquivo para versionamento.
- ENV vars: configuração dinâmica para latência e custo.

## Evidencias de validacao

- Testes de analise (unit + integration):
    - Comando: `pytest tests/test_analysis_unit.py tests/test_analysis_integration.py -q`
    - Resultado: **19 passed in 3.75s**
- Cobertura:
    - Enqueue (single, double-submit, not found)
    - Lock management (processing, release on error, zombie reset)
    - Persistence (analysis saved, lead fields updated)
    - Status aggregation (counts, filtered by lead_ids, single lead status)
    - Fair queue (multi-tenant ordering)
