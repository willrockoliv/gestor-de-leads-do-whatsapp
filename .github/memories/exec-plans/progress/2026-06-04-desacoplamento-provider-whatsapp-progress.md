# Progresso — Desacoplamento do Provider WhatsApp

Plano relacionado: .github/memories/exec-plans/active/2026-06-04-desacoplamento-provider-whatsapp.md
Data de inicio: 2026-06-04
Status: Nao iniciado

## Status da implementacao
- [x] Plano criado em active
- [x] Arquivo de progresso criado
- [ ] Fase 1 iniciada
- [ ] Fase 2 iniciada
- [ ] Fase 3 iniciada
- [ ] Fase 4 iniciada
- [ ] Fase 5 iniciada
- [ ] Fase 6 iniciada

## Aprendizados
- A implementacao atual usa Depends para db/auth, mas instancia manual do servico de WhatsApp.
- O acoplamento principal esta concentrado no servico de sessao e no contrato de webhook.

## Debitos tecnicos
- Falta contrato formal de provider para sessao e webhook.
- Falta factory de provider com selecao por configuracao.
- Falta padrao unico de erros de dominio para integracao externa.

## Decisoes importantes
- Refactor sera incremental para reduzir risco de regressao.
- Primeiro contrato e adapter, depois wiring de DI, depois webhook agnostico.
- Endpoints publicos devem manter compatibilidade durante toda a execucao.
