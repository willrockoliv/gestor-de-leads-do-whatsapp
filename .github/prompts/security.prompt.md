---
name: security
description: Instrucoes para agentes revisarem codigo e alteracoes com foco em seguranca da API, protecao de dados pessoais e dados sensiveis.
agent: agent
---

# Instrução de Segurança Obrigatória

## Objetivo
Esta instrução define o padrão obrigatório para revisão de segurança em qualquer mudança de código, configuração, infraestrutura, testes e documentação técnica neste projeto de gestão de leads do WhatsApp.

Contexto crítico deste repositório:
- Dados pessoais (PII) e dados sensíveis de leads, incluindo conversas de WhatsApp, são processados durante ingestão de mensagens, análise por LLM, classificação de temperatura, geração de resumo e sugestões de resposta.
- O sistema trata dados sensíveis em cadastro de lead, fluxo de análise de conversas de WhatsApp, ingestão de mensagens, integrações externas e logs de análise.
- O frontend é cliente não confiável por definição (Zero Trust Frontend).
- Qualquer vazamento, exposição indevida ou retenção desnecessária é considerado falha crítica.

Regra de ouro:
- Nunca assumir seguranca por padrao.
- **Sempre procurar ativamente** risco de vazamento de dados e abuso de acesso.
- Em caso de duvida, tratar como incidente potencial e bloquear a entrega ate mitigacao.


## Princípio obrigatório: Backend como fonte única de verdade
Regras mandatórias para toda implementação e revisão:
- Nunca confiar em validação feita no frontend como controle de segurança.
- Validações, regras de negócio, permissões e consistência de dados de leads, mensagens e análises devem ser executadas e revalidadas no backend.
- O backend nunca deve aceitar valores finais enviados pelo cliente como verdade.
- Funil de etapas é dinâmico e validado por tenant, não hardcoded.
- Apenas leads com status ativo podem ter mensagens processadas e analisadas.
- Tokens, identificadores sensíveis e dados de sessão não devem depender de armazenamento persistente no navegador para segurança.


## Quando esta instrução deve ser aplicada
Aplicar em 100% dos casos abaixo:
- Revisão de PR.
- Revisão de diff local.
- Geração de código novo.
- Refatoração.
- Alterações de schema, migrações e consultas ao banco de dados.
- Alterações em logs, observabilidade e tratamento de erros.
- Alterações de configurações, segredos, CI/CD, Docker e deploy.
- Alterações em autenticação, autorização, sessão e webhooks.
- Alterações em ingestão/análise de leads, classificação, integrações externas e ingestão de mensagens.

## Politica de bloqueio
Se houver risco alto ou critico sem mitigacao comprovada, o agente deve:
1. Marcar a mudanca como bloqueada para merge/deploy.
2. Explicar exatamente o risco e o possivel impacto.
3. Propor correcao objetiva e valida.
4. Solicitar novos testes de seguranca quando necessario.
5. Registrar os detalhes e sugestões em `.github/memories/exec-plans/security/pending`, bem como o status da issue
6. após todas os achados serem mitigados, atualizar o status para resolvido e mover o registro para `.github/memories/exec-plans/security/resolved`.



## Checklist mínimo obrigatório por revisão
O agente deve confirmar explicitamente cada item:

1. Controle de acesso, autenticação e autorização
- Endpoints administrativos e de análise exigem autenticação forte e autorização por papel.
- Não há elevação de privilégio por parâmetro manipulável no request.
- Não há IDOR (acesso a lead, análise, mensagem ou recurso de outro usuário/tenant por troca de ID).
- JWT de usuário e admin possuem segredos separados, expiração curta e claims mínimas.
- Fluxo de refresh de token não amplia privilégios e respeita expiração/revogação.

2. Supply chain e dependências
- Auditoria obrigatória de dependências Python e Node (ex: `pip-audit`, `npm audit`) em todo PR que altere requirements.txt, package.json, poetry.lock, package-lock.json ou outros lockfiles.
- Verificação obrigatória de alertas do Dependabot via GitHub CLI:
	- `gh api repos/willrockoliv/gestor-de-leads-do-whatsapp/dependabot/alerts?state=open`
	- Nenhum alerta aberto deve permanecer sem justificativa e plano de correção registrado.
- Proibido dependências de fontes não oficiais e dependências sem manutenção ativa.
- Atualização periódica de dependências críticas e revisão de changelogs de segurança.
- Instalação de dependências npm, pip e poetry deve seguir obrigatoriamente:
	- `ignore-scripts=true` (npm, poetry): nunca permitir execução automática de scripts pós-install.
	- `min-release-age=7` (npm, poetry): só permitir instalação de pacotes publicados há pelo menos 7 dias.
	- Lockfiles (`package-lock.json`, `poetry.lock`, `requirements.txt`) devem sempre fixar versão exata (`1.2.3`), nunca usar `^`, `~`, `>=`, `latest` ou intervalos.
	- `allow-git=none` ou equivalente: proibido dependências que puxam direto de repositórios git (npm, poetry, pip).
	- Proibido dependências com scripts de preinstall/postinstall customizados.
	- Proibido dependências deprecated, com alertas de segurança, ou sem atualização há mais de 1 ano.
	- Sempre revisar e aprovar manualmente dependências novas ou atualizadas em PRs.
	- Proibido dependências que requerem permissões elevadas, binários nativos não auditados ou que alterem variáveis de ambiente sensíveis.
	- Exigir configuração de `audit-level=high` (npm) e bloqueio de merge se vulnerabilidade alta/crítica for detectada.
	- Proibir dependências que instalam binários de fontes externas ou executam downloads dinâmicos no postinstall.

3. Logs e observabilidade
- Garantir que logs sensíveis não sejam enviados para stdout/stderr em produção (usar sinks seguros).
- Mascaramento de PII em logs de debug, inclusive em staging.
- Proibido logs de payloads completos de requisições contendo dados sensíveis.

4. CORS e headers de segurança
- Checklist explícito para revisão de CORS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy e outros headers de segurança.
- Proibido CORS permissivo em produção.

5. Uploads e arquivos
- Se houver upload de arquivos (imagens, áudios, documentos), exigir validação de tipo, tamanho e análise de conteúdo.
- Proibido execução de arquivos enviados pelo usuário.

6. Prompts e LLM
- Checklist para revisão de prompts enviados a LLMs, garantindo que não contenham dados sensíveis desnecessários.
- Proibido uso de dados reais de produção em prompts de testes/dev.

7. Gestão de segredos
- Exigir uso de secrets managers (ex: Docker secrets, AWS Secrets Manager) em produção.
- Proibido exposição de segredos em arquivos versionados, inclusive exemplos.

8. Frontend
- Garantir que tokens JWT, segredos ou dados sensíveis nunca sejam expostos em variáveis globais, HTML ou JS acessível ao cliente.
- Validar que erros de frontend não revelem stack traces ou detalhes internos do backend.

9. MFA e acesso administrativo
- Recomendar (ou exigir) MFA para acessos administrativos e operações críticas.

10. Infraestrutura
- Checklist para Dockerfile e docker-compose: não expor portas desnecessárias, não rodar como root, fixar versões de base image.
- Proibir variáveis sensíveis em logs de build.

11. Testes de segurança automatizados
- Exigir cobertura de testes para fluxos negativos (autorização, autenticação, rate limit, replay, etc).
- Cobertura de testes para supply chain (ex: CI falha se `pip-audit`/`npm audit` reportar vulnerabilidade alta/crítica).

12. Proteção de dados pessoais e dados sensíveis
+ PII (nome, telefone, mensagens e conversas de WhatsApp, etc.) não deve aparecer em logs em texto claro.
+ Dados sensíveis não aparecem em exceções, traces e mensagens de erro.
+ Campos sensíveis são mascarados ou truncados ao registrar eventos.
+ Exposição em respostas de API segue princípio do mínimo necessário.
+ Tokens de integração (ex: WhatsApp, LLM, provedores externos) e IDs externos são tratados como sensíveis em logs e erros.
+ Prompts de LLM não devem vazar dados sensíveis para logs, respostas ou terceiros.

13. Segredos e credenciais
- Nenhum segredo hardcoded em código, testes, templates ou fixtures.
- Variáveis de ambiente críticas não possuem fallback inseguro.
- Tokens/chaves não são impressos em logs, inclusive em debug.
- Segredos de JWT, webhook HMAC e credenciais de provedores devem ser distintos por ambiente.

14. Entrada de dados e injeção
- Validação de entrada com schemas robustos (Pydantic, FastAPI).
- Queries SQL sem concatenação insegura de strings (usar SQLAlchemy com bind params).
- Proteção contra command injection, path traversal e template injection.
- Webhooks validam assinatura e autenticidade antes de processar payload.
- Webhooks validam idempotência e proteção contra replay quando aplicável.

15. Integridade de negócio
+ Regras de negócio, permissões e consistência de dados de leads, mensagens e análises são validadas no backend.
+ Não existe confiança em valores vindos do frontend para qualquer decisão de negócio.
+ Alterações manuais de status/etapa de lead devem ser auditáveis e autorizadas.
+ Webhooks críticos possuem comportamento idempotente.
+ Apenas leads ativos podem ter mensagens processadas e analisadas.
+ Watchdog deve resetar locks de processamento travados.
+ O backend nunca processa análise automaticamente por evento/flood, apenas por gatilho manual.

16. Criptografia e transporte
- Tráfego de dados sensíveis apenas sobre HTTPS/TLS no ambiente alvo.
- Assinaturas HMAC/segredo de webhook são verificadas com comparação segura.
- Não usar algoritmos criptográficos fracos ou obsoletos.

17. Segurança da API contra abuso e tentativas de invasão
- Aplicar rate limiting por rota e por perfil de risco (login admin, refresh, webhooks, endpoints públicos).
- Aplicar limites de burst e janela (ex.: por IP, por usuário e por chave de API quando houver).
- Proteger autenticação contra brute force e credential stuffing (delay progressivo, lock temporário, bloqueio por IP quando necessário).
- Evitar enumeração de usuários/UUID por mensagens de erro diferenciadas.
- Definir limites de payload (tamanho/campos) e timeouts para reduzir DoS de aplicação.
- Restringir CORS ao mínimo necessário e evitar configurações permissivas globais.

18. LGPD e minimização de dados
- Coletar somente dados estritamente necessários para o fluxo.
- Definir e respeitar retenção mínima para dados sensíveis e logs.
- Evitar persistência desnecessária de dados sensíveis fora do fluxo essencial.
- Garantir possibilidade de exclusão/anonimização quando aplicável.

19. Erros, observabilidade e auditoria
- Mensagens para cliente não revelam internals, queries ou segredos.
- Logging estruturado com redação de campos sensíveis.
- Eventos críticos de segurança são auditáveis (quem, quando, o que).
- Correlation/request id sem incluir dados pessoais.

20. Dependências e superfície de ataque
- Dependências novas são justificadas e avaliadas por risco.
- Evitar bibliotecas sem manutenção ativa.
- Imagens Docker e base runtime com versões fixas e atualizadas.
- Não introduzir portas, CORS aberto ou configuração permissiva sem motivo.

21. Testes de segurança
- Testes cobrindo negativas de autenticação/autorização.
- Testes cobrindo mascaramento de PII em logs.
- Testes para assinatura inválida de webhook e payload adulterado.
- Testes para garantir não exposição de campos sensíveis em respostas.
- Testes de rate limiting em endpoints de maior risco.
- Testes para brute force/lock temporário e não enumeração em login/recuperação.


## Regras específicas para ingestão, análise e integrações externas
+ Não confiar em campos editáveis de cadastro de lead sem validação de formato, consistência e autorização no backend.
+ Em ingestão de mensagens, garantir que apenas leads ativos tenham mensagens processadas e analisadas.
+ Em análise de mensagens e conversas de WhatsApp, garantir que dados sensíveis não sejam expostos em logs, prompts ou respostas de LLM.
+ Alterações manuais de status/etapa de lead devem ser auditáveis e autorizadas.
+ Em integrações externas (ex: WhatsApp, LLM), erros devem ser sanitizados antes de persistência/retorno.
+ Webhooks só podem atualizar estado após validação de assinatura + idempotência.
+ Watchdog deve resetar locks de processamento travados.
+ O backend nunca processa análise automaticamente por evento/flood, apenas por gatilho manual.

## Padrão de revisão de alterações
Para cada arquivo alterado, o agente deve verificar:
1. Qual dado sensível entra, onde é processado e onde sai.
2. Se existe risco de vazamento por log, erro, serialização ou cache.
3. Se os controles de autorização são aplicados no nível correto.
4. Se existe validação robusta na borda da aplicação.
5. Se o diff introduz bypass de segurança por condição alternativa.
6. Se o backend continua como autoridade para integridade, permissões e consistência dos dados de negócio.
7. Se existe proteção adequada contra abuso (rate limit, limites de payload, brute force).

## Saída esperada do agente em revisões
O resultado da revisão deve sempre conter:
- Lista de achados por severidade: Crítico, Alto, Médio, Baixo.
- Evidência objetiva (arquivo, ponto de código e cenário explorável).
- Impacto de negócio e privacidade.
- Correção recomendada com prioridade.
- Status final: Aprovado com ressalvas ou Bloqueado.


## Red flags de bloqueio imediato
+ Log de PII (nome, telefone, mensagem, conversa de WhatsApp, etc.) sem mascaramento.
+ Endpoint sensível (leads, análise, ingestão, webhooks) sem autenticação/autorização adequada.
+ Segredo/token em repositório.
+ Webhook sem validação de assinatura.
+ Endpoint sensível sem rate limiting e sem mitigação equivalente.
+ Query com potencial SQL injection.
+ Mensagem de erro retornando stack trace ou detalhe interno sensível.


## Princípios de implementação segura (resumo)
- Least privilege.
- Defense in depth.
- Secure by default.
- Fail safe defaults.
- Need to know e minimização de dados.
- Privacy by design.
- Zero trust frontend.
- Backend authoritative.


## Regra final
Se não for possível provar que a mudança é segura para dados pessoais e dados sensíveis de leads, onboarding, ingestão, análise e integrações externas, a mudança não deve ser considerada pronta.

## Referências Rápidas:

- Skill de revisão de segurança: `.github/skills/security-review/SKILL.md`