---
name: Copilot Agent Instructions
description: Instruções persistentes para LLMs que trabalham neste workspace. Este arquivo é lido automaticamente pelo GitHub Copilot como contexto em toda interação. 
applyTo: "**/*"
---

# Copilot Instructions

Instruções persistentes para LLMs que trabalham neste workspace.
Este arquivo é lido automaticamente pelo GitHub Copilot como contexto em toda interação.

---

## 📂 Contexto do Projeto

Antes de começar qualquer tarefa, leia os seguintes arquivos para entender o estado atual:

- `.prompts/progresso.md` - Registro de progresso, bugs conhecidos e roadmap.
- `.prompts/prd.md` - PRD completo do produto.
- `.prompts/plano.md` - Plano de desenvolvimento detalhado, dividido em fases
- `.prompts/frontend.md` - especificação do frontend

---

## 🔧 Convenções de Desenvolvimento

### Gerenciamento de Dependências

- **Sempre que instalar uma nova biblioteca** (via `pip install`), **atualize imediatamente o `requirements.txt`** com a versão exata instalada (`lib==X.Y.Z`).
- Para verificar a versão instalada: `pip show <pacote> | grep Version`.
- Dependências de teste/dev ficam no mesmo `requirements.txt` (sem separação por arquivo).
- Após editar `requirements.txt`, valide com `pip install -r requirements.txt` para garantir que não há conflitos.

### Validação do Frontend

- **Sempre validar o frontend após qualquer alteração feita no código do frontend.**
- siga as especificações do arquivo `.prompts/frontend.md`
- acesse o frontend diretamente pela porta configurada para garantir que as mudanças funcionam corretamente, utilizando o comando `curl -i http://<gateway>:<frontend_port>`
- É possível que VS Code esteja rodando no modo Dev Container, e portanto vc precise descobrir qual o gateway do container ao invés de usar apenas `localhost`. Descubra o gateway em que vc está rodando com o comando `ip route | grep default` e faça as requisições usando ele, por exemplo: http://172.17.0.1:3000, e não apenas `localhost`.
- teste sempre todas os endpoints envolvidos na investigação do erro ou nas modificações feitas, e sempre faça pelo menos 3 tentativas de requisição para cada um dos endpoint envolvidos, pois o Next.js pode demorar para compilar e responder na primeira requisição, e isso pode ser confundido com um erro ou sucesso.
- caso precise acessar alguma área logada, utilize o endpoint de login do backend para obter um token JWT válido para conseguir utiliza-lo na requisição do frontend. Utilize o usuário `teste@teste.com` com senha `123456` para isso.
  - `curl -X POST http://172.17.0.1:8000/auth/login -H "Content-Type: application/json" -d '{"email":"teste@teste.com","password":"123456"}'`
  - `curl -i http://172.17.0.1:3000/settings`
  - `curl -i http://172.17.0.1:3000/onboarding`
  - `curl -i http://172.17.0.1:3000/register`
  - `curl -i http://172.17.0.1:3000/login`
  - `curl -i http://172.17.0.1:3000/leads`
  - `curl -i http://172.17.0.1:3000/dashboard`

### Testes

- Seguir o princípio **TDD** — escrever testes primeiro quando possível.
- Testes ficam em `tests/` e usam `pytest` com `pytest-asyncio`.
- Testes unitários usam funções `_sync` dos serviços (sem banco de dados).
- Testes de integração HTTP usam SQLite in-memory via fixtures de `tests/conftest.py`.
- **Sempre rodar `pytest tests/ -v`** após qualquer alteração para validar que nada quebrou.

### Código Python

- Async por padrão nos routers e serviços (FastAPI + SQLAlchemy async).
- Cada serviço expõe uma versão `_sync` pura para testes unitários.
- Models SQLAlchemy em `app/models/`, schemas Pydantic em `app/schemas/`.
- Lógica de negócio em `app/services/`, nunca diretamente nos routers.

### Docker

- Ao alterar `requirements.txt`, o container precisa de rebuild: `docker compose up --build -d`.
- Volume `./app:/app/app` permite hot-reload de código Python e templates.

### Commits e Progresso

- Após concluir uma sessão de trabalho significativa, **atualizar `.prompts/progresso.md`** com:
  - O que foi feito (changelog).
  - Bugs encontrados/corrigidos.
  - Novos débitos técnicos.
  - Atualizar contagem de testes.
- **Manter o `README.md` atualizado** sempre que houver:
  - Novos endpoints ou rotas.
  - Mudanças na stack ou dependências relevantes.
  - Alterações na estrutura de pastas.
  - Avanço no roadmap (marcar fases concluídas).
  - Novas variáveis de ambiente.
  - Mudança na contagem de testes.

### Procedimento de Validação do Frontend (2026-04-19)

- Após cada alteração no frontend, todos os endpoints principais devem ser validados via `curl` para garantir resposta HTTP 200 OK e renderização correta.
- Endpoints validados:
  - `/dashboard`
  - `/leads`
  - `/settings`
  - `/onboarding`
  - `/register`
  - `/login`
- Para cada endpoint, execute:
  - `curl -i http://<host>:3000/<endpoint>`
  - Aguarde a compilação do Next.js, se necessário (pode demorar na primeira chamada).
  - Corrija imediatamente qualquer erro de build, import ou resposta inesperada.
- Considere o frontend validado apenas se todos os endpoints retornarem HTTP 200 OK e exibirem a interface esperada (formulários, tabelas, onboarding, etc).
- Registre o progresso e eventuais correções em `/memories/repo/frontend-validation.md`.