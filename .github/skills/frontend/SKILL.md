---
name: frontend
description: Skill para tarefas em frontend/, integração frontend-backend e validação de endpoints.

---

- whenToUse:
	- Sempre que a tarefa envolver código em frontend/ ou integração frontend-backend.

- patterns:
	- Use Next.js, siga o padrão de pastas do projeto.
	- Valide endpoints via curl (ver instruções globais).
	- Atualize componentes e páginas conforme especificação em `.github/rfcs/002-frontend-redesign.md`

- pitfalls:
	- Esquecer de validar endpoints após alterações.
	- Não atualizar o progresso após mudanças relevantes.


## Ambiente e dependências

- Nunca rode `npm install`, `npm run build` ou `npm run dev/start` manualmente no host ou container. Sempre utilize `docker compose up --build -d` para garantir consistência entre host e container.
- Se precisar refazer o ambiente, remova `node_modules`, `.next`, e outros caches tanto no host quanto no container, e reinicie com `docker compose up --build -d`.
- Sempre valide se o ambiente do host e do container estão sincronizados antes de rodar testes E2E ou Playwright.

## Execução do seed E2E para testes do frontend

Para garantir que os dados de teste estejam corretos no frontend, rode o seed E2E sempre que for rodar os testes Playwright ou validar fluxos de temperatura de lead. O seed agora inclui mensagens para cada lead, permitindo que o botão "Analisar" fique habilitado e os testes de análise funcionem corretamente.

O comando deve ser executado a partir da raiz do projeto para que o Python encontre o módulo `app` corretamente, portanto sempre execute o comando `pwd` para se localizar.

```bash
pwd

cd <diretorio-raiz-do-projeto>

PYTHONPATH=. python3 frontend/tests/scripts/seed_e2e.py
```

## Execução dos testes Playwright

Para rodar os testes E2E do frontend, entre na pasta `frontend/` e execute:

```bash
pwd

cd <diretorio-raiz-do-projeto>/frontend

npx playwright test
```

## Mock de análise de lead nos testes

O teste Playwright que valida o loading/spinner ao acionar análise de lead faz mock da resposta do endpoint `/api/analysis`, garantindo que o feedback visual seja testado sem depender de backend real ou LLM. Veja comentário no topo do arquivo `frontend/tests/leads.spec.ts`.

> **Importante:** Sempre rode o seed antes dos testes Playwright para garantir que os leads tenham mensagens e o botão "Analisar" esteja disponível.

## links:

- label: Instruções Copilot
	url: ../../instructions/copilot-instructions.md
- label: Memórias do domínio
	url: ../../memories/repo/
