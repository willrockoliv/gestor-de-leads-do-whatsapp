# Progresso — Desacoplamento do Provider WhatsApp

Plano relacionado: .github/memories/exec-plans/completed/2026-06-04-desacoplamento-provider-whatsapp.md
Data de inicio: 2026-06-04
Status: Concluido

## Encerramento
- Plano concluido com todos os checklists e criterios de saida marcados como concluidos.
- Validacao final executada com suite completa do backend sem regressao.

## Status da implementacao
- [x] Plano criado em active
- [x] Arquivo de progresso criado
- [x] Fase 1 iniciada
- [x] Fase 2 iniciada
- [x] Fase 3 iniciada
- [x] Fase 4 iniciada
- [x] Fase 5 iniciada
- [x] Fase 6 iniciada

## Aprendizados
- A implementacao atual usa Depends para db/auth, mas instancia manual do servico de WhatsApp.
- O acoplamento principal esta concentrado no servico de sessao e no contrato de webhook.
- Contrato de provider com normalizacao de webhook e mapeamento central de status reduz divergencia entre router e servico.
- Dependency injection do provider permite override limpo em testes sem monkeypatch de classe concreta.
- Regra de conflito CORE/default ficou encapsulada no adapter WAHA, sem vazar para o service.
- Anti-replay no webhook foi adicionado com guard em memoria e deduplicacao de mensagem no ponto de ingestao.
- Suite focal (WhatsApp/Webhook) e suite completa do backend executadas com sucesso apos refactor do provider.
- Selecao de provider por configuracao foi adicionada na factory via WHATSAPP_PROVIDER.

## Debitos tecnicos
- Anti-replay atual em memoria local nao compartilha estado entre replicas/processos.

## Decisoes importantes
- Refactor sera incremental para reduzir risco de regressao.
- Primeiro contrato e adapter, depois wiring de DI, depois webhook agnostico.
- Endpoints publicos devem manter compatibilidade durante toda a execucao.
- Contrato de provider foi reorganizado para app/providers/whatsapp (interface + factory + adapters).
- Loop de sync passa a usar o mesmo provider abstrato para manter consistencia do caminho de execucao.
- Erros de conflito CORE agora usam tipo de dominio (WhatsAppProviderConflictError), com mapeamento HTTP consistente.
