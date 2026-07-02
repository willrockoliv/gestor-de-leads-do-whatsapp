# Progresso: Deploy em Produção

**Plano:** `active/2026-07-02-deploy-producao.md`
**Início:** 2026-07-02
**Status:** Aguardando início da execução

---

## Decisões Registradas

### Stack de Exposição
- **Traefik v3** como reverse proxy único gerenciando dev e prod na mesma VPS
- **Cloudflare Free** é suficiente para MVP: SSL automático, CDN, DDoS básico, sem custo
- SSL via **ACME Let's Encrypt com DNS challenge Cloudflare** (wildcard `*.dominio.com`) — Traefik gerencia renovação

### Separação de Ambientes
- Docker networks isoladas: `prod_network` e `dev_network`
- Volumes nomeados separados: `pgdata_prod` vs `pgdata` (dev)
- Dev recebe limites de CPU/RAM via `deploy.resources.limits` para não concorrer com prod

### Cloudflare — Custo
- **Free: R$ 0** — confirmado suficiente para MVP
- Limitações do Free que não afetam MVP: WAF avançado, analytics detalhado, SLA formal
- Recursos Free úteis: proxy DNS, SSL, DDoS L3/L4, Bot Fight Mode, Cloudflare Tunnel

### Riscos Identificados
- Ollama pode ser gargalo de memória em prod — considerar usar apenas LLM cloud em prod
- Backup de banco não está coberto neste plano — criar plano dedicado após estabilizar

---

## Log de Execução

*(Preencher durante execução)*
