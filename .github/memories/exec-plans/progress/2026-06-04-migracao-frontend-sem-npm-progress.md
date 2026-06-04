# Progresso: Migracao frontend sem npm

## Status da implementacao
- Estado geral: Nao iniciado
- Fase atual: Planejamento
- Ultima atualizacao: 2026-06-04

## Aprendizados
- A migracao tem alto risco tecnico por causa de roteamento dinamico e gerenciamento de estado hoje acoplados ao ecossistema React/Next.
- O fluxo de paridade total exige validar todos os cenarios negativos de API (401, 403, 404, 409, 429).

## Debitos tecnicos
- Definir estrategia final para empacotamento de assets JS/CSS sem introduzir nova cadeia de dependencias insegura.
- Definir baseline de observabilidade para frontend estatico no cutover.

## Decisoes importantes
- Estrategia de migracao: big-bang.
- Modelo: SPA em HTML/CSS/JavaScript puro.
- Hospedagem: servico estatico separado.
- Escopo: paridade funcional total.

## Registro de execucao
- 2026-06-04: plano criado e adaptado ao padrao de exec-plans com checklist por fases e dependencias explicitas.
