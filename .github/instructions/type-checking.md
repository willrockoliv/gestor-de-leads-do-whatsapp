# Guia de Type Checking

## Ferramentas Utilizadas
- **Python:** mypy (`mypy.ini` ou `pyproject.toml`)
- **TypeScript:** `tsc --noEmit`

## Como rodar o type checker
- Python: `mypy .`
- TypeScript: `npm run type-check` ou `tsc --noEmit`

## Como interpretar e corrigir erros
- Leia a mensagem de erro e ajuste tipos nas funções, variáveis e retornos.
- Adicione anotações de tipo em código legado conforme necessário.

## Como adicionar tipos em código legado
- Use `# type: ignore` apenas como último recurso.
- Prefira tipar funções públicas e módulos principais primeiro.

## Type Checking no CI
- Type checkers são executados em cada push/PR via workflow em `.github/workflows/type-check.yml`
