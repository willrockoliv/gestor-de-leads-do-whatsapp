# Guia de Linting

## Linters Utilizados
- **Python:** ruff (`pyproject.toml`) ou flake8 (`.flake8`)
- **TypeScript/JS:** eslint (`eslint.config.mjs` ou `.eslintrc`)

## Como rodar o linter
- Python: `ruff check .` ou `flake8 .`
- JS/TS: `npm run lint`

## Como corrigir erros automaticamente
- Python: `ruff check . --fix`
- JS/TS: `npm run lint -- --fix`

## Como adicionar regras customizadas
- Edite `pyproject.toml` ou `.flake8` para Python
- Edite `eslint.config.mjs` ou `.eslintrc` para JS/TS

## Lint no CI
- Linters são executados em cada push/PR via workflow em `.github/workflows/lint.yml`

## Dicas
- Rode o linter antes de cada commit.
- Corrija todos os avisos antes de abrir PR.
