# Plano de Implementacao: Etapa Solicita Analise IA

Objetivo: Implementar com seguranca e previsibilidade a etapa da jornada em que o usuario solicita analise IA de leads, incluindo analise individual e em lote, persistencia do resultado e retorno confiavel para o frontend.

## Escopo e ponto de partida

- Jornada ja implementada ate: ingestao de mensagens e dados de leads salvos.
- Etapa alvo desta execucao: "Solicita analise IA".
- Fora de escopo: mudancas de UX nao relacionadas ao fluxo de analise, novos canais alem de WhatsApp.

## Dependencias explicitas

- [ ] D1. Validar disponibilidade de configuracao LLM no ambiente (`LITELLM_MODEL`, chave do provider e endpoint, quando aplicavel).
- [ ] D2. Confirmar modelagem e relacoes de dados (`Lead`, `Message`, `Analysis`) prontas para persistencia do resultado.
- [ ] D3. Confirmar funil do tenant acessivel para compor o contexto da analise.
- [ ] D4. Definir/validar limites de concorrencia e rate limit para evitar estouro de custo.

## Fase 1 - Contrato funcional da analise

- [ ] 1.1 Definir contrato de entrada e saida para `POST /leads/{id}/analyze` (campos obrigatorios, erros e codigos HTTP).
- [ ] 1.2 Definir contrato de entrada e saida para `POST /leads/analyze-all` (quantidade processada, falhas parciais e resumo final).
- [ ] 1.3 Definir comportamento idempotente para retry no frontend sem duplicar analyses.

## Fase 2 - Pipeline de analise individual

- [ ] 2.1 Implementar orquestracao no service: coletar mensagens do lead + funil do tenant + metadados relevantes.
- [ ] 2.2 Implementar lock otimista (`is_processing`) com retorno claro em caso de concorrencia.
- [ ] 2.3 Chamar LiteLLM com timeout, retries controlados e trilha de logs sem PII sensivel.
- [ ] 2.4 Validar e normalizar resposta da IA (score, etapa, resumo, resposta sugerida).
- [ ] 2.5 Persistir `Analysis` e atualizar campos derivados do lead de forma atomica.
- [ ] 2.6 Garantir liberacao de lock em sucesso, falha e cancelamento.

## Fase 3 - Pipeline de analise em lote

- [ ] 3.1 Definir criterios de selecao de leads elegiveis para lote.
- [ ] 3.2 Implementar processamento concorrente com limite de paralelismo (semaphore).
- [ ] 3.3 Garantir isolamento por lead para que erro unitario nao interrompa o lote inteiro.
- [ ] 3.4 Retornar resumo de execucao com totais: analisados, ignorados, falhas e motivos.

## Fase 4 - Confiabilidade operacional

- [ ] 4.1 Implementar/validar watchdog para reset de locks zombies (`is_processing`) com janela segura.
- [ ] 4.2 Definir padrao de erros para indisponibilidade de LLM e resposta invalida.
- [ ] 4.3 Adicionar metricas minimas e logs estruturados para observabilidade do fluxo de analise.

## Fase 5 - Integracao com frontend

- [ ] 5.1 Validar `frontend/src/lib/api.ts` para chamadas de analise individual e lote.
- [ ] 5.2 Ajustar estado de carregamento e bloqueio de botoes durante processamento.
- [ ] 5.3 Exibir feedback de erro orientado a acao (retry, aguardar processamento, falha de provedor).
- [ ] 5.4 Revalidar lista/detalhe de leads apos analise para refletir score e etapa atualizados.

## Fase 6 - Testes e validacao

- [ ] 6.1 Cobrir service de analise com testes unitarios para sucesso, erro de LLM e lock concorrente.
- [ ] 6.2 Cobrir endpoints com testes de integracao (`/leads/{id}/analyze` e `/leads/analyze-all`).
- [ ] 6.3 Cobrir cenarios de lote com falha parcial e resultado agregado.
- [ ] 6.4 Executar regressao backend (`pytest`) e garantir ausencia de quebra em webhooks/dashboard.
- [ ] 6.5 Executar checks de qualidade (lint/type-check aplicaveis ao escopo alterado).

## Fase 7 - Documentacao e encerramento

- [ ] 7.1 Atualizar documentacao tecnica relevante (fluxo de analise, limites e tratamento de erro).
- [ ] 7.2 Atualizar `README.md` e `ARCHITECTURE.md` se houver mudanca de comportamento publico.
- [ ] 7.3 Atualizar progresso final, mover plano para `completed/` e refletir mudanca no `PLAN-INDEX.md`.

## Ordem de execucao (uma tarefa por vez)

1. Fase 1 completa
2. Fase 2 completa
3. Fase 3 completa
4. Fase 4 completa
5. Fase 5 completa
6. Fase 6 completa
7. Fase 7 completa

## Criterios de saida

- [ ] Endpoint individual analisa e persiste com lock seguro e resposta consistente.
- [ ] Endpoint em lote processa com limite de concorrencia e resumo final confiavel.
- [ ] Falhas da LLM nao deixam lock preso e retornam erro padronizado ao frontend.
- [ ] Testes de unidade/integracao cobrindo fluxos criticos passando sem regressao.
- [ ] Documentacao e indice de planos atualizados.

---

## Anexo A - Plano tecnico para modelo local (VPS KVM 2: 2 vCPU, 8 GB RAM)

Objetivo do anexo: habilitar analise IA local com custo baixo, mantendo fallback para cloud quando necessario.

### Premissas de capacidade

- [ ] A1. Reservar no minimo 3 GB de RAM livres para inferencia local.
- [ ] A2. Operar com concorrencia de inferencia = 1 (sem paralelismo em CPU).
- [ ] A3. Usar modelos pequenos (1B a 3B) quantizados.

### Fase A - Runtime local

- [ ] A.1 Adicionar servico de runtime local no `docker-compose.yml` (preferencia: Ollama).
- [ ] A.2 Persistir cache de modelos em volume dedicado para evitar re-download.
- [ ] A.3 Definir healthcheck do runtime local e dependencia do backend.

### Fase B - Configuracao da aplicacao

- [ ] B.1 Estender `app/core/config.py` com:
  - `LLM_API_BASE` (default vazio)
  - `LLM_TIMEOUT_SECONDS` (default 45)
  - `LLM_MAX_TOKENS` (default 220)
  - `LLM_ENABLE_FALLBACK` (default true)
  - `LLM_FALLBACK_MODEL` (default vazio)
- [ ] B.2 Atualizar `analysis_service.call_llm()` para usar `api_base` quando definido.
- [ ] B.3 Adicionar timeout e tratamento de excecao com erro padronizado para indisponibilidade local.

### Fase C - Modelo e tuning inicial

- [ ] C.1 Definir modelo inicial local: instruct 2B-3B para CPU.
- [ ] C.2 Reduzir contexto enviado ao modelo (ultimas N mensagens + resumo curto).
- [ ] C.3 Limitar output (`LLM_MAX_TOKENS`) para manter latencia previsivel.
- [ ] C.4 Padronizar schema JSON de saida e manter validacao Pydantic estrita.

### Fase D - Fallback e resiliencia

- [ ] D.1 Implementar fallback para cloud quando local falhar por timeout/erro de conexao/schema invalido.
- [ ] D.2 Logar motivo do fallback sem vazar conteudo sensivel da conversa.
- [ ] D.3 Expor metrica minima: total local, total fallback, taxa de falha local.

### Fase E - Benchmark e criterio go/no-go

- [ ] E.1 Rodar benchmark com os 30 leads reais anonimizados.
- [ ] E.2 Capturar p95 de latencia por analise individual e por lote.
- [ ] E.3 Validar qualidade minima:
  - score coerente com historico
  - etapa do funil valida
  - resumo util para vendedor
- [ ] E.4 Definir go/no-go:
  - p95 individual <= 20s
  - taxa de JSON invalido < 5%
  - fallback <= 15% em horario normal

### Entregaveis do anexo

- [ ] Runtime local operacional no compose.
- [ ] Backend configuravel para local + fallback.
- [ ] Parametros de timeout/tokens/documentados no `.env.example`.
- [ ] Relatorio curto de benchmark com decisao go/no-go.
