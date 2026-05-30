---
name: Security Review Guardrails
description: Instrucao obrigatoria para agentes revisarem codigo e alteracoes com foco em seguranca da API, protecao de dados pessoais e dados sensiveis de lead, contrato e pagamento.
applyTo: "**/*"
---

# Security Review Obrigatorio para Todos os Agentes

## Objetivo
Esta instrucao define um padrao obrigatorio para revisar seguranca em qualquer mudanca de codigo, configuracao, infraestrutura, testes e documentacao tecnica.

Contexto critico deste repositorio:
- Dados pessoais (PII) sao processados durante onboarding e contratacao.
- O sistema trata dados sensiveis em cadastro de lead, fluxo contratual e etapa de pagamento.
- O frontend e cliente nao confiavel por definicao (Zero Trust Frontend).
- Qualquer vazamento, exposicao indevida ou retencao desnecessaria e considerado falha critica.

Regra de ouro:
- Nunca assumir seguranca por padrao.
- Sempre procurar ativamente risco de vazamento de dados e abuso de acesso.
- Em caso de duvida, tratar como incidente potencial e bloquear a entrega ate mitigacao.

## Principio obrigatorio: Backend como fonte unica de verdade
Regras mandatorias para toda implementacao e revisao:
- Nunca confiar em validacao feita no frontend como controle de seguranca.
- Validacoes, regras de negocio e autorizacao devem ser executadas e revalidadas no backend.
- Valores financeiros (preco, desconto, total, parcelas, juros, moeda) devem ser definidos e recalculados no backend.
- O backend nunca deve aceitar valor final de pagamento enviado pelo cliente como verdade.
- Estados da jornada (pending, contract_pending, contract_signed, payment_pending, payment_completed, expired) so podem mudar por transicoes permitidas no backend.
- Tokens e identificadores sensiveis nao devem depender de armazenamento persistente no navegador para seguranca.

## Quando esta instrucao deve ser aplicada
Aplicar em 100% dos casos abaixo:
- Revisao de PR.
- Revisao de diff local.
- Geracao de codigo novo.
- Refatoracao.
- Alteracoes de schema, migracoes e consultas SQL.
- Alteracoes em logs, observabilidade e tratamento de erros.
- Alteracoes de configuracoes, secrets, CI/CD, Docker e deploy.
- Alteracoes em autenticacao, autorizacao, sessao e webhooks.
- Alteracoes em onboarding, contrato, pagamento e calculo de valores.

## Politica de bloqueio
Se houver risco alto ou critico sem mitigacao comprovada, o agente deve:
1. Marcar a mudanca como bloqueada para merge/deploy.
2. Explicar exatamente o risco e o possivel impacto.
3. Propor correcao objetiva e valida.
4. Solicitar novos testes de seguranca quando necessario.
5. Registrar os detalhes e sugestões em `.github/memories/exec-plans/security/pending`, bem como o status da issue
6. após todas os achados serem mitigados, atualizar o status para resolvido e mover o registro para `.github/memories/exec-plans/security/resolved`.

## Checklist minimo obrigatorio por revisao
O agente deve confirmar explicitamente cada item:

1. Controle de acesso, autenticacao e autorizacao
- Endpoints administrativos exigem autenticacao forte e autorizacao por papel.
- Nao ha elevacao de privilegio por parametro manipulavel no request.
- Nao ha IDOR (acesso a recurso de outro usuario por troca de ID).
- JWT de onboarding e admin possuem segredos separados, expiracao curta e claims minimas.
- Fluxo de refresh de token nao amplia privilegios e respeita expiracao/revogacao.

2. Protecao de dados pessoais e dados sensiveis
- PII nao e logado em texto claro.
- Dados sensiveis nao aparecem em excecoes, traces e mensagens de erro.
- Campos sensiveis sao mascarados ou truncados ao registrar eventos.
- Exposicao em respostas de API segue principio do minimo necessario.
- Dados de pagamento sensiveis (cartao, PAN, CVV) nao transitam nem persistem no backend em texto claro.
- Tokens de pagamento e IDs externos sao tratados como sensiveis em logs e erros.

3. Segredos e credenciais
- Nenhum segredo hardcoded em codigo, testes, templates ou fixtures.
- Variaveis de ambiente criticas nao possuem fallback inseguro.
- Tokens/chaves nao sao impressos em logs, inclusive em debug.
- Segredos de JWT, webhook HMAC e credenciais de providers devem ser distintos por ambiente.

4. Entrada de dados e injecao
- Validacao de entrada com schemas robustos.
- Queries SQL sem concatenacao insegura de strings.
- Protecao contra command injection, path traversal e template injection.
- Webhooks validam assinatura e autenticidade antes de processar payload.
- Webhooks validam idempotencia e protecao contra replay quando aplicavel.

5. Integridade de negocio e valores financeiros
- Regras de preco, descontos e total sao calculadas no backend com fonte oficial (plano/settings).
- Nao existe confianca em valores vindos do frontend para contrato ou pagamento.
- Alteracoes de status de contrato/pagamento exigem pre-condicoes de estado no backend.
- Operacoes de pagamento e webhooks criticos possuem comportamento idempotente.

6. Criptografia e transporte
- Trafego de dados sensiveis apenas sobre HTTPS/TLS no ambiente alvo.
- Assinaturas HMAC/segredo de webhook sao verificadas com comparacao segura.
- Nao usar algoritmos criptograficos fracos ou obsoletos.

7. Seguranca da API contra abuso e tentativas de invasao
- Aplicar rate limiting por rota e por perfil de risco (login admin, onboarding por UUID, refresh, webhooks, endpoints publicos).
- Aplicar limites de burst e janela (ex.: por IP, por usuario e por chave de API quando houver).
- Proteger autenticacao contra brute force e credential stuffing (delay progressivo, lock temporario, bloqueio por IP quando necessario).
- Evitar enumeracao de usuarios/UUID por mensagens de erro diferenciadas.
- Definir limites de payload (tamanho/campos) e timeouts para reduzir DoS de aplicacao.
- Restringir CORS ao minimo necessario e evitar configuracoes permissivas globais.

8. LGPD e minimizacao de dados
- Coletar somente dados estritamente necessarios para o fluxo.
- Definir e respeitar retencao minima para dados sensiveis e logs.
- Evitar persistencia desnecessaria de dados sensiveis fora do fluxo essencial.
- Garantir possibilidade de exclusao/anonimizacao quando aplicavel.

9. Erros, observabilidade e auditoria
- Mensagens para cliente nao revelam internals, queries ou segredos.
- Logging estruturado com redacao de campos sensiveis.
- Eventos criticos de seguranca sao auditaveis (quem, quando, o que).
- Correlation/request id sem incluir dados pessoais.

10. Dependencias e superficie de ataque
- Dependencias novas sao justificadas e avaliadas por risco.
- Evitar bibliotecas sem manutencao ativa.
- Imagens Docker e base runtime com versoes fixas e atualizadas.
- Nao introduzir portas, CORS aberto ou configuracao permissiva sem motivo.

11. Testes de seguranca
- Testes cobrindo negativas de autenticacao/autorizacao.
- Testes cobrindo mascaramento de PII em logs.
- Testes para assinatura invalida de webhook e payload adulterado.
- Testes para garantir nao exposicao de campos sensiveis em respostas.
- Testes para garantir que valores financeiros enviados pelo frontend sao ignorados/recalculados no backend.
- Testes de rate limiting em endpoints de maior risco.
- Testes para brute force/lock temporario e nao enumeracao em login/recuperacao.

## Regras especificas para onboarding, contrato e pagamento
- Onboarding por UUID deve respeitar TTL no backend, sem depender de controle no cliente.
- Nao confiar em campos editaveis de cadastro sem validacao de formato, consistencia e autorizacao no backend.
- Em contrato, campos dinamicos (nome, documento, valor) devem ser derivados de dados validados no servidor.
- Em pagamento, backend deve aceitar somente tokenizacao segura para cartao e recusar dados sensiveis brutos.
- Webhooks de contrato e pagamento so podem atualizar estado apos validacao de assinatura + idempotencia.
- Em integracoes externas, erros devem ser sanitizados antes de persistencia/retorno.

## Padrao de revisao de alteracoes
Para cada arquivo alterado, o agente deve verificar:
1. Qual dado sensivel entra, onde e processado e onde sai.
2. Se existe risco de vazamento por log, erro, serializacao ou cache.
3. Se os controles de autorizacao sao aplicados no nivel correto.
4. Se existe validacao robusta na borda da aplicacao.
5. Se o diff introduz bypass de seguranca por condicao alternativa.
6. Se o backend continua como autoridade para regras de negocio e valores financeiros.
7. Se existe protecao adequada contra abuso (rate limit, limites de payload, brute force).

## Saida esperada do agente em revisoes
O resultado da revisao deve sempre conter:
- Lista de achados por severidade: Critico, Alto, Medio, Baixo.
- Evidencia objetiva (arquivo, ponto de codigo e cenario exploravel).
- Impacto de negocio e privacidade.
- Correcao recomendada com prioridade.
- Status final: Aprovado com ressalvas ou Bloqueado.

## Red flags de bloqueio imediato
- Log de PII sem mascaramento.
- Valor de pagamento aceito diretamente do frontend sem recalculo no backend.
- Endpoint sem autenticacao onde deveria existir.
- Segredo/token em repositorio.
- Webhook sem validacao de assinatura.
- Endpoint sensivel sem rate limiting e sem mitigacao equivalente.
- Query com potencial SQL injection.
- Mensagem de erro retornando stack trace ou detalhe interno sensivel.

## Principios de implementacao segura (resumo)
- Least privilege.
- Defense in depth.
- Secure by default.
- Fail safe defaults.
- Need to know e minimizacao de dados.
- Privacy by design.
- Zero trust frontend.
- Backend authoritative.

## Regra final
Se nao for possivel provar que a mudanca e segura para dados pessoais e dados sensiveis de onboarding, contrato e pagamento, a mudanca nao deve ser considerada pronta.
