# Plano de Implementacao: Migracao frontend sem npm

Objetivo: Migrar o frontend de Next.js/React para SPA em HTML/CSS/JavaScript puro, removendo dependencia de npm no runtime e mantendo paridade funcional total.

## Dependencias entre fases
- Fase 1 desbloqueia Fase 2.
- Fase 2 desbloqueia Fase 3 e Fase 4.
- Fase 3.1 desbloqueia inicio da Fase 4 em ambiente alvo.
- Fase 4.1 e obrigatoria antes de 4.2 a 4.6.
- Fase 5 roda em paralelo com Fase 4.5 e 4.6, mas deve terminar antes da Fase 7.
- Fase 6 bloqueia o go-live (Fase 7.4).
- Fase 8 so inicia apos estabilizacao da Fase 7.

## Checklist de implementacao

### Fase 1 - Baseline tecnico e congelamento
- [ ] Inventariar todas as rotas, estados e interacoes do frontend atual.
- [ ] Definir criterios de aceite por fluxo critico.
- [ ] Congelar mudancas funcionais no frontend legado durante a migracao.

### Fase 2 - Arquitetura SPA vanilla
- [ ] Definir arquitetura de modulos JS (router, store, cliente HTTP, renderizadores, componentes).
- [ ] Definir roteamento SPA com History API para rotas estaticas e dinamicas (/leads/:id).
- [ ] Definir estrategia de estado com store central e eventos para evitar race conditions.
- [ ] Definir contrato de seguranca client-side para tratamento central de 401/403/409/429.

### Fase 3 - Infra de entrega sem npm em runtime
- [ ] Trocar servico frontend no docker-compose para servidor estatico dedicado.
- [ ] Definir pipeline de empacotamento de assets estaticos sem npm em runtime.
- [ ] Definir injecao de configuracao de ambiente para URL da API sem NEXT_PUBLIC_*.
- [ ] Ajustar healthchecks, portas e networking com CORS estrito e previsivel.

### Fase 4 - Implementacao funcional da SPA
- [ ] Onda A: Implementar login/register/logout, restauracao de sessao, guard de rota e redirecionamentos.
- [ ] Onda B: Implementar dashboard (estatisticas, top leads, analise em lote, loading e erro).
- [ ] Onda C: Implementar leads (filtros, ordenacao, paginacao, analise individual, status converted/lost).
- [ ] Onda D: Implementar detalhe de lead (/leads/:id) com carregamento paralelo e troca de etapa.
- [ ] Onda E: Implementar onboarding/settings com edicao e persistencia de funil.
- [ ] Onda F: Implementar fluxo WhatsApp (connect, polling de qrcode/status, tratamento de 429).

### Fase 5 - Paridade de UX e acessibilidade
- [ ] Reimplementar componentes criticos (dialog, select, toasts, tabela) com foco, teclado e ARIA.
- [ ] Preservar experiencia visual com CSS modular e tokens.
- [ ] Garantir responsividade mobile/desktop nas telas impactadas.

### Fase 6 - Hardening de seguranca e privacidade
- [ ] Revisar CORS e headers de seguranca para frontend estatico.
- [ ] Garantir nao exposicao de PII e tokens em logs e mensagens de erro.
- [ ] Validar fluxos negativos (token expirado, sem auth, id invalido, acao em lead inativo, rate-limit).
- [ ] Confirmar backend como fonte unica de verdade para regras de negocio sensiveis.

### Fase 7 - Validacao, cutover e rollback
- [ ] Executar regressao funcional completa por fluxo com dados seed.
- [ ] Executar testes backend para garantir ausencia de regressao de API.
- [ ] Validar observabilidade durante fluxos criticos e erros.
- [ ] Realizar cutover big-bang com snapshot do frontend legado para rollback.
- [ ] Estabelecer monitoramento reforcado pos-go-live (4xx/5xx, latencia, auth, 429).

### Fase 8 - Limpeza de legado e documentacao
- [ ] Remover codigo legado de Next.js/React/Tailwind e configs associadas apos estabilizacao.
- [ ] Atualizar documentacao operacional e onboarding com novo fluxo sem npm.
- [ ] Atualizar instrucoes de seguranca/dependencias para o novo contexto de supply chain.

## Arquivos relevantes
- frontend/package.json
- frontend/src/lib/api.ts
- frontend/src/lib/auth-context.tsx
- frontend/src/app/(authenticated)/leads/page.tsx
- frontend/src/app/(authenticated)/leads/[id]/page.tsx
- frontend/src/app/(authenticated)/dashboard/page.tsx
- frontend/src/app/(authenticated)/onboarding/page.tsx
- frontend/src/app/(authenticated)/settings/page.tsx
- docker-compose.yml
- .github/copilot-instructions.md
- README.md
- app/main.py

## Verificacao obrigatoria
- [ ] Executar pytest completo e validar contratos de endpoint usados pelo frontend.
- [ ] Executar revisao de seguranca de API (auth, autorizacao, IDOR, rate-limit, CORS).
- [ ] Validar manualmente rotas no browser: /login, /register, /dashboard, /leads, /leads/:id, /onboarding, /settings.
- [ ] Validar estados de erro (400/401/403/404/409/429), loading e expiracao de token.
- [ ] Validar logs frontend/backend sem PII em claro.
- [ ] Executar smoke de deploy via docker compose e handshake frontend-api.
- [ ] Testar rollback para artefato legado em janela curta.

## Decisoes
- [x] Estrategia de migracao: big-bang.
- [x] Modelo de aplicacao: SPA em JavaScript puro.
- [x] Hospedagem do frontend: servico estatico separado.
- [x] Escopo: paridade funcional total.
- [x] Incluido: migracao de UI/roteamento/estado/integracoes frontend e ajustes de infra/documentacao.
- [x] Excluido: mudancas de regra de negocio no backend e redesign profundo de UX.