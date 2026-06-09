# Security Resolved — fast-uri high remediation (2026-06-09)

Status: RESOLVED
Scope: Fase 6.8.5 (Supply chain e dependências)

## Finding
- High severity vulnerability in `fast-uri` (path traversal / authority confusion), pulled transitively by `shadcn -> @modelcontextprotocol/sdk -> ajv`.

## Mitigation
- Added npm `overrides` forcing `fast-uri` to `3.1.2`.
- Regenerated lockfile with `npm install --package-lock-only --ignore-scripts`.
- Re-ran `npm audit --audit-level=high`.

## Evidence
- `npm audit --audit-level=high`: no high/critical vulnerabilities remaining (only moderate).
- Dependency pinned policy strengthened with exact versions in `frontend/package.json`.

## Residual risk
- Moderate npm advisories still pending triage/remediation.
- Repository Dependabot still reports open high alerts and requires triage workflow closure.
