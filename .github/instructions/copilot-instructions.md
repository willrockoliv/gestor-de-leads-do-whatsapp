---
name: Copilot Agent Instructions
description: Instruções persistentes para LLMs que trabalham neste workspace. Este arquivo é lido automaticamente pelo GitHub Copilot como contexto em toda interação. 
applyTo: "**/*"
---

# Copilot Instructions

## Memoria de planos

- sempre leia o arquivo `.github/memories/plan.md` para entender os planos de implementação, próximos passos e decisões em andamento no projeto. Este arquivo deve ser atualizado a cada tarefa concluída, constantemente com o progresso e mudanças de direção, servindo como guia para o desenvolvimento assistido.

## Contexto do Projeto
- Sempre antes de iniciar tarefas, leia os arquivos:
  - `.prompts/prd.md`
  - `.prompts/plano.md`
  - `.prompts/progresso.md`
  - `.github/instructions/CONTEXT-INDEX.md`
  - `.github/memories/`
  - `.github/ARCHITECTURE.md`
  - `.github/rfcs/`
  - `.github/skills/SKILLS-INDEX.md`
- sempre procure pelos arquivos `*INDEX.md` para se guiar quais arquivos fazem sentido ler conforme a tarefa para evitar carregar para o contexto arquivos desnecessários e economizar tokens.
- Siga as convenções de dependências, testes e validação descritas abaixo.

## Convenções Globais
- **Dependências:** Sempre atualize `requirements.txt` após instalar libs. Use versões exatas. Valide com `pip install -r requirements.txt`.
- **Testes:** Use pytest, siga TDD, rode todos os testes após mudanças. Testes unitários usam funções `_sync` dos serviços. Testes de integração usam SQLite in-memory.
- **Frontend:** Valide endpoints via curl após alterações (veja instruções detalhadas abaixo). Siga `.prompts/frontend.md`.
- **Documentação:** Atualize README e progresso após cada entrega. Registre bugs, débitos técnicos e avanços em `.prompts/progresso.md`.
- **Docker:** Ao alterar dependências, rode `docker compose up --build -d`.

## Estrutura de Contexto Obrigatória
- `.prompts/prd.md` — PRD completo do produto
- `.prompts/plano.md` — Plano de desenvolvimento
- `.prompts/progresso.md` — Progresso, bugs e roadmap
- `.prompts/frontend.md` — Especificação do frontend

## Skills
- Carregue skills específicas conforme o domínio da tarefa (ex: autenticação, frontend, integração, testes).
- Skills ficam em `.github/skills/<domínio>/SKILL.md`.

## Memória
- Use arquivos em `.github/memories/` para registrar decisões, padrões, troubleshooting e lições aprendidas.
- Mantenha arquivos curtos e objetivos para facilitar o carregamento automático.

## Fluxo de Trabalho Ideal
1. Leia os arquivos de contexto obrigatórios.
2. Carregue apenas as skills relevantes para a tarefa.
3. Siga as convenções globais e específicas do domínio.
4. Valide o frontend e rode todos os testes após mudanças.
5. Atualize progresso, README e memórias conforme necessário.

## Exemplo de Validação do Frontend
- Descubra o gateway do container: `ip route | grep default`
- Valide endpoints principais (ex: `/dashboard`, `/leads`, `/settings`, `/onboarding`, `/register`, `/login`) via curl:
  - `curl -i http://<gateway>:3000/<endpoint>`
- Teste cada endpoint pelo menos 3 vezes após alterações.
- Use o endpoint de login do backend para obter JWT se necessário.

### Melhores Práticas para Testes Playwright/E2E e Frontend

- Sempre simule login nos testes Playwright/E2E de páginas autenticadas. Use usuário de teste conhecido (ex: teste@teste.com/123456) ou crie um usuário de teste no setup do teste.
- Antes de rodar testes, verifique se o serviço frontend está rodando e acessível. Use `curl` ou `docker compose ps` para garantir que o endpoint está disponível.
- Sempre confira os logs do serviço frontend (`docker compose logs frontend --tail 40`) ao depurar falhas ou timeouts em testes automatizados.
- Se ocorrer timeout, verifique se a página está compilando, lenta ou em loading. Aguarde e execute novamente, ou aumente o timeout do teste Playwright se necessário.
- Para ambientes Docker, valide se o endpoint correto é `localhost` ou o gateway do container, usando comandos bash para descobrir o IP correto.

## Atualização de Skills e Instruções
- Atualize skills e instructions sempre que fluxos mudarem ou bugs recorrentes forem identificados.
- Documente exemplos de prompts eficazes e ineficazes.

## Links Úteis
- [README.md](../../README.md)
- [.github/memories/](../memories/)