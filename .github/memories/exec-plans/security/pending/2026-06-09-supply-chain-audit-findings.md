# Security Pending — Supply Chain Findings (2026-06-09)

Status: BLOCKED (Dependabot highs still open)
Scope: Fase 6.8.5 (Supply chain e dependências)
Owner: Backend/Frontend platform

## Findings by severity

### Alto
1. Dependabot alerts (9 high) still open at repository level.
- Evidence: `gh api ... dependabot/alerts?state=open` summary by severity.
- Impact: unresolved high findings block merge/deploy by policy.
- Recommended fix: triage each alert and remediate or document risk acceptance with due date.

#### Triage detalhado dos 9 high abertos
1. #23 `next` / `GHSA-26hh-7cqf-hhc6` / fix `16.2.6`.
2. #18 `next` / `GHSA-mg66-mrh9-m8jx` / fix `16.2.5`.
3. #16 `next` / `GHSA-c4j6-fc7j-m34r` / fix `16.2.5`.
4. #15 `next` / `GHSA-492v-c6pp-mqqv` / fix `16.2.5`.
5. #13 `next` / `GHSA-267c-6grr-h53f` / fix `16.2.5`.
6. #12 `next` / `GHSA-36qx-fr4f-26g5` / fix `16.2.5`.
7. #11 `next` / `GHSA-8h8q-6873-q5fj` / fix `16.2.5`.
8. #7 `fast-uri` / `GHSA-v39h-62p7-jpjc` / fix `3.1.2`.
9. #6 `fast-uri` / `GHSA-q3j6-qgpj-74h6` / fix `3.1.1`.

Status de mitigação local já aplicada:
- `next` atualizado para `16.2.7` (acima das versões de correção).
- Override para `fast-uri@3.1.2` aplicado.
- `npm audit --audit-level=high` sem high/critical no ambiente local.

Bloqueio remanescente:
- Dependabot ainda reporta os 9 alerts high como abertos no repositório remoto.
- Aguardando atualização/fechamento dos alerts após push e nova varredura do GitHub, ou fechamento manual com justificativa.

### Médio
1. Other npm moderate vulnerabilities reported (brace-expansion, hono, ip-address, qs, postcss path via next)
- Evidence: npm audit --audit-level=high
- Impact: mixed risk; still requires remediation plan and validation.
- Recommended fix: npm audit fix for safe updates; targeted explicit version bumps where required.

## Process checks
- Dependabot open alerts count: 28 (gh api query).
- Security gate workflow added at .github/workflows/security-gate.yml to fail CI on pip-audit and npm audit high/critical.

## Immediate actions
1. Publicar alterações de lockfile/package para acionar novo scan do Dependabot.
2. Revalidar alerts abertos e fechar os que já estiverem mitigados por versão.
3. Resolver moderadas restantes ou registrar exceções temporárias com aceite de risco.

## Exit criteria for moving to resolved
- No high/critical npm vulnerabilities in CI gate.
- pip-audit passes with no unresolved vulnerability or justified exception.
- Dependabot open alerts triaged with remediation plan and due date.

## Applied mitigations in this iteration
- requirements.txt fixed typo `python-multipartt` and upgraded to `python-multipart==0.0.27`.
- `pip-audit -r requirements.txt` now passes with no known vulnerabilities.
- frontend upgraded from `next@16.2.3` to `next@16.2.7` in package.json/lockfile.
- frontend override added for `fast-uri@3.1.2`, removing npm high/critical findings.
- security workflow gate added: `.github/workflows/security-gate.yml`.
- Dependabot query executed: 28 open alerts.
