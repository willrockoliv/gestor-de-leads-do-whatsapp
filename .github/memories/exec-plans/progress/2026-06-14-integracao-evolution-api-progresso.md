# 📊 Progresso — Integração Evolution API como Provider WhatsApp

**Plano:** `.github/memories/exec-plans/active/2026-06-14-integracao-evolution-api.md`  
**Data de Início:** 2026-06-14  
**Status:** Iniciado (Fase 1 em preparação)

---

## ✅ Tarefas Concluídas

- [x] Evolution API adicionado ao `docker-compose.yml` (2026-06-14)
- [x] Pesquisa completa de documentação oficial Evolution API (2026-06-14)
- [x] Análise da arquitetura desacoplamento atual (Protocol + Factory + DI) (2026-06-14)
- [x] Plano detalhado de implementação criado (2026-06-14)
- [x] Validação: Evolution API atende 100% dos requisitos do PRD (2026-06-14)

---

## 🔄 Tarefas em Progresso

- [ ] Fase 1.2: Estender `.env.example` para Evolution API
- [ ] Fase 1.3: Atualizar `app/core/config.py`

---

## ⏳ Tarefas Pendentes

- [ ] Fase 2: Implementar adapter Evolution API (`app/providers/whatsapp/evolution.py`)
- [ ] Fase 3: Estender factory
- [ ] Fase 4: Validar injeção de dependência (já implementado, apenas validação)
- [ ] Fase 5: Webhook handler agnóstico (já implementado, apenas validação)
- [ ] Fase 6: Testes (unitários + E2E)
- [ ] Fase 7: Docker Compose validação
- [ ] Fase 8: Documentação (ARCHITECTURE.md, README.md)

---

## 📝 Decisões Importantes

### 1. Agnósticismo via Protocol (Confirmado ✅)
- Arquitetura atual já usa Protocol pattern (`WhatsAppProvider`)
- Factory resolve provider por config
- Service recebe provider via DI (construtor)
- Router usa `Depends(get_whatsapp_provider)`
- **Conclusão:** Padrão perfeito, apenas estender com novo adapter

### 2. Múltiplas Instâncias vs Sessão Única
- **WAHA:** Tier CORE = 1 sessão (`default`), Tier PLUS = múltiplas
- **Evolution API:** Suporta ilimitadas instâncias em 1 container (é o ponto forte)
- **Decisão:** Evolution API resolve o problema multi-tenant do WAHA
- **Session ID:** WAHA usa `default`, Evolution usa `tenant-{uuid}`

### 3. Contrato Permanece Agnóstico
- Não adicionar métodos específicos de Evolution
- Se Evolution precisar de config extra → usar `resolve_session_id()` (já agnóstico)
- Webhook normalization centralizado via `normalize_webhook_payload()` (já agnóstico)

### 4. Docker Compose: Ambos em Paralelo
- WAHA e Evolution API podem rodar juntos (não conflita)
- Útil para testes de migração
- Pode desabilitar um se necessário

---

## 🎯 Aprendizados até Agora

### Sobre Evolution API
- Suporta Baileys (free, sem custo) e Meta Cloud API (oficial, com custo)
- Gerenciador de instâncias centralizado em 1 container
- Webhooks mais robustos (JWT + HMAC validation)
- Melhor integração com LLM (OpenAI nativo)
- 8.7k stars, 154 contributors, manutenção ativa

### Sobre Desacoplamento Atual
- Codebase bem estruturada para adicionar novos providers
- Protocol pattern reduz acoplamento a ~50 LOC por adapter
- Factory é agnóstica (não precisa saber detalhes de adapters)
- DI via FastAPI `Depends` é elegante e testável

### Sobre Multi-Tenancy
- Problema original (1 sessão WAHA) será resolvido por Evolution
- DB pode suportar múltiplos providers por tenant (future feature)
- Webhook routing precisa detectar provider via session_id (já implementado)

---

## 🛠️ Débitos Técnicos

- [ ] Anti-replay em webhook: em memória local, não compartilha entre replicas
- [ ] Rate limiting: em-memory, escalabilidade em produção com Redis (future)
- [ ] Multi-provider por tenant: DB schema não suporta ainda (future)
- [ ] Monitoramento: adicionar observabilidade (Prometheus, etc) - future

---

## 📈 Métricas de Sucesso

| Métrica | Target | Status |
|---------|:---:|:---:|
| Regressões WAHA | 0 | ⏳ A validar |
| Cobertura de testes Evolution | ≥ 85% | ⏳ A validar |
| Endpoints agnósticos | 100% | ✅ Confirmado |
| Providers suportados | 2+ (WAHA, Evolution) | ✅ Em progresso |
| Tempo ramp-up Evolution | < 3 dias | 📅 Estimado |

---

## 🔗 Referências

- Plano: `.github/memories/exec-plans/active/2026-06-14-integracao-evolution-api.md`
- Evolution API docs: https://docs.evolutionfoundation.com.br/
- GitHub Evolution API: https://github.com/evolution-foundation/evolution-api
- ARCHITECTURE.md atual: `.github/ARCHITECTURE.md`
- Desacoplamento anterior: `.github/memories/exec-plans/completed/2026-06-04-desacoplamento-provider-whatsapp.md`

---

## 📋 Próximos Passos Imediatos

1. **Hoje (2026-06-14):**
   - [x] Plano criado
   - [x] Arquivo de progresso criado
   - [ ] Fase 1.2: atualizar `.env.example`
   - [ ] Fase 1.3: atualizar `config.py`

2. **Amanhã (2026-06-15):**
   - [ ] Fase 2: iniciar adapter Evolution (`evolution.py`)
   - [ ] Implementar métodos principais

3. **2026-06-16:**
   - [ ] Fase 2: concluir adapter
   - [ ] Fase 3: estender factory
   - [ ] Iniciar testes

4. **2026-06-17–2026-06-18:**
   - [ ] Testes completos
   - [ ] Docker Compose validação
   - [ ] Documentação

