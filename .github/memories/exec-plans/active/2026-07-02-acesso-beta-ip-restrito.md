# Plano de Implementação: Acesso Beta Restrito por IP

**Objetivo:** Liberar acesso ao app em produção apenas para o IP de casa, permitindo que a primeira beta tester (esposa) use o sistema enquanto o servidor permanece fechado para o mundo.

---

## Contexto

- VPS já tem firewall com política Drop para Any e Accept apenas para SSH em porta customizada.
- A beta tester acessa de casa (mesmo IP que o desenvolvedor).
- Risco: IP residencial pode ser dinâmico — endereço pode mudar sem aviso.

---

## Decisão Arquitetural

Duas abordagens possíveis, em ordem de preferência:

| Abordagem | Quando usar |
|---|---|
| **A — UFW por IP** | IP fixo ou estático na conexão de casa |
| **B — Cloudflare Access (Zero Trust)** | IP dinâmico; mais robusto a longo prazo |

A abordagem B é recomendada como solução permanente. A abordagem A pode ser usada como passo imediato enquanto o Cloudflare Access não estiver configurado.

---

## Fases e Tarefas

### Fase 1 — Diagnóstico

- [ ] **1.1** Verificar IP público atual de casa: `curl ifconfig.me`
- [ ] **1.2** Confirmar se o IP é fixo ou dinâmico com a operadora / roteador
- [ ] **1.3** Verificar ferramenta de firewall ativa na VPS: `ufw status` ou `iptables -L`

### Fase 2 — Abordagem A: Liberar acesso por IP via UFW (rápido)

> Pré-requisito: VPS usa UFW. Pular se usar iptables puro.

- [ ] **2.1** Anotar IP de casa (resultado do 1.1)
- [ ] **2.2** Adicionar regras UFW para portas 80 e 443:
  ```bash
  ufw allow from SEU_IP to any port 80
  ufw allow from SEU_IP to any port 443
  ufw reload
  ```
- [ ] **2.3** Validar acesso: abrir `http://IP_VPS` e `https://dominio.com` no browser de casa
- [ ] **2.4** Validar bloqueio: testar acesso via VPN ou rede diferente (deve ser bloqueado)

### Fase 3 — Abordagem B: Cloudflare Access / Zero Trust (robusto, sem depender de IP)

> Recomendado quando IP for dinâmico ou para controle mais granular.

- [ ] **3.1** Acessar [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com)
- [ ] **3.2** Criar Application do tipo "Self-hosted":
  - Nome: `Gestor de Leads - Beta`
  - Domínio: `app.seudominio.com`
- [ ] **3.3** Criar política de acesso:
  - Rule name: `Beta Testers`
  - Selector: `Emails` → adicionar e-mail da esposa e o seu
- [ ] **3.4** Ativar e testar: acessar `app.seudominio.com` sem estar logado (deve pedir autenticação por e-mail)
- [ ] **3.5** Confirmar que a esposa consegue acessar após autenticação Cloudflare

### Fase 4 — Procedimento para atualização de IP (se Abordagem A)

> Se o IP de casa mudar, seguir este runbook:

- [ ] **4.1** Documentar runbook de atualização de IP no arquivo de progresso:
  ```bash
  # Remover regra antiga
  ufw delete allow from IP_ANTIGO to any port 80
  ufw delete allow from IP_ANTIGO to any port 443
  # Adicionar novo IP
  ufw allow from IP_NOVO to any port 80
  ufw allow from IP_NOVO to any port 443
  ufw reload
  ```
- [ ] **4.2** (Opcional) Criar script `/root/update-beta-ip.sh` na VPS para facilitar a troca

---

## Dependências com o Plano de Deploy

Este plano é paralelo ao `2026-07-02-deploy-producao.md` e deve ser executado **após** a Fase 4 (Traefik) e Fase 5 (Cloudflare DNS) daquele plano estarem concluídas, pois as regras de firewall só fazem sentido quando o app estiver acessível via domínio público.

---

## Notas

- **Não commitar** nenhum IP real em arquivos do repositório.
- O Cloudflare Access (Fase 3) substitui completamente a necessidade de gestão de IP no firewall para controle de acesso de usuários — recomendado migrar para ele assim que o domínio estiver configurado.
- UFW rules são perdidas em alguns provedores de VPS ao fazer rebuild da instância — documentar no runbook.
