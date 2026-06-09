

# Index dos Planos de Execução

Use este arquivo para localizar rapidamente os planos de execução ativos, completos, arquivados e o progresso das implementações.

## .github/memories/exec-plans/active/ - planos em andamento

- 2026-04-15-plano-inicial.md
  - Scaffolding do projeto, setup FastAPI, Next.js, Docker, CI, banco e testes básicos. Entregas incrementais por fases.

- 2026-05-31-fase-6-integracao-whatsapp.md
  - Integração com WhatsApp via Waha/Evolution API. Conexão com QR code, endpoints de controle de sessão, webhook de recebimento, testes E2E com mock server.

## .github/memories/exec-plans/completed/ - planos completados

- 2026-04-30-plan-frontendRedesign.prompt.md
  - Redesign completo do frontend com design system Nordic Minimalist, correções de hidratação/tipografia, validação manual obrigatória no Integrated Browser, padronização compose-only e descontinuação dos E2E Playwright legados.

- 2026-06-04-desacoplamento-provider-whatsapp.md
  - Desacoplamento do provider WhatsApp com DI no FastAPI, adapter dedicado, seleção por configuração (`WHATSAPP_PROVIDER`) e critérios de saída concluídos.

## .github/memories/exec-plans/progress/ - progresso das implementaçoes com aprendizados e anotações importantes

- 2026-04-15-plano-inicial-progresso.md
  - Progresso incremental do plano inicial, checkpoints, entregas parciais, ajustes e diário de execução.

- 2026-05-31-fase-6-integracao-whatsapp-progresso.md
  - Diário de execução da Fase 6, decisões sobre escolha de serviço WhatsApp, debitos técnicos, aprendizados durante implementação.

- 2026-06-04-desacoplamento-provider-whatsapp-progress.md
  - Progresso do plano de desacoplamento do provider WhatsApp, incluindo decisões de arquitetura, débitos técnicos e validação por fases.

## .github/memories/exec-plans/archived - planos arquivados

- 2026-04-21-plano-de-redesign-do-frontend.md
  - Redesign premium do frontend, foco em E2E Playwright, seed robusta, integração frontend-backend validada, Docker estável.

## .github/memories/exec-plans/security/pending - revisoes e achados de seguranca pendentes de solução

- 2026-06-09-supply-chain-audit-findings.md
  - Achados de supply chain da Fase 6.8.5 (npm audit/pip-audit/Dependabot), com status bloqueado por vulnerabilidade alta residual no ecossistema frontend.

- 2026-06-09-whatsapp-threat-model.md
  - DFD, ativos sensíveis, ameaças por severidade e plano de mitigação da Fase 6.8.1 para fluxo WhatsApp.

## .github/memories/exec-plans/security/resolved - revisoes e achados de seguranca já resolvidos

- 2026-06-09-python-multipart-remediation.md
  - Correção de dependência inválida e mitigação de vulnerabilidades do python-multipart, com evidência de `pip-audit` limpo.

- 2026-06-09-fast-uri-override-remediation.md
  - Mitigação de vulnerabilidade alta transitiva no frontend via override para `fast-uri@3.1.2`, removendo achados high/critical no `npm audit` local.