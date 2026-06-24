# Security Resolved — Supply Chain High Alerts Regression (2026-06-24)

Status: RESOLVED
Scope: Revisão de segurança obrigatória do diff local
Owner: Plataforma (Backend/Frontend)

## Contexto

- Diff local atual: apenas inclusão de `Makefile` com comando utilitário para decodificar QR code base64.
- Achado bloqueante não está no diff de código, mas no estado atual de supply chain do repositório.

## Evidências objetivas

1. Dependabot aberto (remoto)
- Comando: `gh api repos/willrockoliv/gestor-de-leads-do-whatsapp/dependabot/alerts?state=open --jq 'length'`
- Resultado: `28` alertas abertos.

2. Distribuição por severidade
- Comando: `gh api repos/willrockoliv/gestor-de-leads-do-whatsapp/dependabot/alerts?state=open --paginate --jq 'group_by(.security_advisory.severity)|map({severity:.[0].security_advisory.severity,count:length})'`
- Resultado: `3 high`, `19 medium`, `6 low`.

3. Alertas HIGH identificados
- `hono` (npm) — `GHSA-88fw-hqm2-52qc` / `CVE-2026-54290`
  - Manifest: `frontend/package-lock.json`
- `python-multipart` (pip) — `GHSA-5rvq-cxj2-64vf` / `CVE-2026-53539`
  - Manifest: `requirements.txt`
- `vite` (npm) — `GHSA-fx2h-pf6j-xcff` / `CVE-2026-53571`
  - Manifest: `.prompts/redesign-frontend/lead-dashboard/package-lock.json`

## Impacto

- Violação direta da política de bloqueio para severidade alta/crítica.
- Risco de exploração de vulnerabilidades em cadeia de dependências.
- Status de segurança do repositório incompatível com promoção segura para produção.

## Ações recomendadas (prioridade alta)

1. Corrigir/atualizar imediatamente as dependências afetadas e regenerar lockfiles.
2. Executar auditoria local:
   - `pip-audit -r requirements.txt`
   - `docker compose exec frontend npm audit --audit-level=high`
3. Validar Dependabot remoto até `0 high` e `0 critical`.
4. Reexecutar checks de CI de segurança.

## Progresso de mitigação nesta sessão

- Backend (pip): `requirements.txt` atualizado para versões corrigidas:
  - `pydantic-settings==2.14.2`
  - `python-multipart==0.0.31`
- Frontend (npm): `frontend/package.json` recebeu override explícito `"hono": "4.12.25"`.
- Prompt frontend (npm): `.prompts/redesign-frontend/lead-dashboard/package.json` atualizado para `"vite": "8.0.16"`.
- Lockfiles npm regenerados em ambiente isolado via container Node (sem instalação no host).
- Validação local concluída:
  - `pyenv exec python -m pip_audit -r requirements.txt` sem vulnerabilidades conhecidas.
  - `npm ci --ignore-scripts` no frontend concluído com sucesso em container.

## Evidências de fechamento

- GitHub Actions: workflow `Security Gate` mais recente em status `success`.
- Dependabot remoto: `0` alertas `high/critical` no momento do fechamento.

## Critério de saída para mover a RESOLVED

- Dependabot remoto com `0 high` e `0 critical`.
- Evidências de auditoria local sem high/critical anexadas.
- Registro atualizado em `security/resolved` com data, evidências e comandos.
