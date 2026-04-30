---
name: Gestão de Planos de Implementação
description: Guia para criação, atualização e organização dos planos de implementação do projeto.
applyTo: .github/memories/exec-plans/**/*
---

# Instruções para gestão de arquivos de planos de implementação

## Estrutura de diretórios
- Em `.github/memories/exec-plans/` existem dois diretórios:
  - `active/`: planos em andamento ou prontos para serem implementados.
  - `completed/`: planos já implementados. Consulte-os para contexto histórico ou decisões anteriores.

## Fluxo de gestão
1. **Criação:**
   - Crie o arquivo em `active/` usando o padrão `YYYY-MM-DD-nome-do-plano.md`.
   - Inicie o plano com um breve resumo/objetivo no topo do arquivo.
   - Estruture as tasks em bullet-points:
     - `[ ]` para tasks não implementadas
     - `[x]` para tasks concluídas
2. **Execução:**
   - Implemente sempre uma task por vez, seguindo a ordem do plano.
   - Marque `[x]` imediatamente ao concluir uma task.
   - Mantenha o plano sempre atualizado durante a execução.
3. **Conclusão:**
   - Ao finalizar todas as tasks, mova o arquivo de `active/` para `completed/`.
   - Exemplo (terminal):
     ```bash
     mv .github/memories/exec-plans/active/2026-04-15-plano-inicial.md .github/memories/exec-plans/completed/
     ```
4. **Atualização do índice:**
   - Sempre que criar, mover ou concluir um plano, atualize o arquivo `PLAN-INDEX.md`.
   - Adicione uma breve descrição de cada plano no índice, resumindo seu objetivo.

## Boas práticas
- Revise planos em `completed/` antes de iniciar novas features para evitar retrabalho.
- Padronize o idioma (português) e o formato dos bullet-points.
- Utilize descrições claras e objetivas para facilitar buscas e automações futuras.

## Exemplo de estrutura de plano
```
# Plano de Implementação: Nova Feature X

Objetivo: Implementar a feature X conforme PRD.

- [ ] Criar modelagem inicial
- [ ] Implementar endpoint
- [ ] Escrever testes unitários
- [x] Configurar CI
```