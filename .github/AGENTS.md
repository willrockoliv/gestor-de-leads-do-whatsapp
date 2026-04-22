# AGENTS.md

## Agentes Customizados

Este repositório pode utilizar agentes customizados para tarefas autônomas ou fluxos complexos, potencializando o Copilot Chat Agent.

### Como funcionam
- Agentes são scripts ou configurações que automatizam fluxos recorrentes ou críticos.
- Podem ser invocados manualmente ou por instrução do Copilot.
- Devem ser documentados aqui com objetivo, escopo e exemplos de uso.

## Exemplos de Agentes

### 1. Explore (default)
- **Função:** Exploração e leitura do código, busca de padrões, sumarização de contexto.
- **Quando usar:** Sempre que for necessário mapear rapidamente o projeto, encontrar arquivos, funções ou dependências.

### 2. Test Runner
- **Função:** Executa todos os testes e sumariza resultados.
- **Quando usar:** Antes de deploys, após grandes refatorações ou para validação rápida.

### 3. Review Agent
- **Função:** Revisar PRs, sugerir melhorias, garantir padrões de código, cobertura de testes e docs atualizadas.
- **Checklist de revisão:**
  - Cobertura de testes adequada
  - Padrões de código seguidos (lint/type-check)
  - Documentação atualizada
  - Pipeline CI verde
- **Como acionar:** Manualmente (revisor humano) ou via comentário `/review` (automatizado/GitHub Actions).

## Como criar novos agentes
- Crie um diretório ou script dedicado.
- Documente objetivo, escopo, exemplos de prompt e limitações.
- Atualize este arquivo com instruções claras de uso.

## Boas práticas para prompts autônomos
- Seja específico sobre o objetivo do agente.
- Limite o escopo para evitar uso excessivo de tokens.
- Documente entradas e saídas esperadas.
