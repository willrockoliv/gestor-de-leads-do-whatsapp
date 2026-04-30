# RFC 001 - Padrão de Serviços

## Contexto
Padronização da estrutura e responsabilidades dos serviços no backend.

## Decisão
- Cada domínio de negócio possui um service dedicado em `app/services/`.
- Services nunca acessam diretamente o banco, sempre via models/ORM.
- Funções de service devem ser assíncronas, com versão `_sync` para testes.
- Lógica de negócio nunca deve ficar em routers ou models.

## Alternativas consideradas
- Lógica em routers (rejeitada por dificultar testes e manutenção).
- Services síncronos apenas (rejeitada por limitar concorrência).

## Consequências
- Facilita testes, manutenção e evolução.
- Permite integração fácil com novas fontes de dados ou serviços externos.

## Status
Aprovada e vigente.
