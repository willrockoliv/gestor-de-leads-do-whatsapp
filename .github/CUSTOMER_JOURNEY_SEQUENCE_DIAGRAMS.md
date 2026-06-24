# Jornada do Cliente na Aplicacao

Este documento descreve, com diagramas de sequencia Mermaid, a jornada completa do cliente (time comercial) usando o Gestor de Leads do WhatsApp.

## 1. Visao Geral Ponta a Ponta

```mermaid
sequenceDiagram
    autonumber
    participant U as Usuario Comercial
    participant FE as Frontend Next.js
    participant BE as Backend FastAPI
    participant DB as PostgreSQL
    participant WA as Provider WhatsApp
    participant LLM as LiteLLM

    U->>FE: Acessa plataforma
    FE->>BE: POST /auth/register ou /auth/login
    BE->>DB: Cria/valida usuario e tenant
    DB-->>BE: Usuario autenticado
    BE-->>FE: JWT

    U->>FE: Define funil no onboarding
    FE->>BE: PUT /tenants/me/funnel
    BE->>DB: Salva configuracao de funil
    DB-->>BE: Configuracao persistida
    BE-->>FE: Confirmacao

    U->>FE: Conecta WhatsApp
    FE->>BE: POST /whatsapp/connect
    BE->>WA: Cria ou recupera sessao
    WA-->>BE: Sessao pronta
    FE->>BE: GET /whatsapp/qrcode
    BE->>WA: Busca QR Code
    WA-->>BE: QR Code
    BE-->>FE: Exibe QR
    U->>WA: Escaneia QR no celular

    WA->>BE: Webhook de mensagem recebida
    BE->>DB: Cria/atualiza lead e mensagens
    DB-->>BE: Dados salvos

    U->>FE: Solicita analise IA
    FE->>BE: POST /leads/{id}/analyze ou /leads/analyze-all
    BE->>LLM: Classificacao, resumo e sugestao
    LLM-->>BE: Resultado estruturado
    BE->>DB: Persiste analysis e score
    DB-->>BE: Persistencia concluida
    BE-->>FE: Resultado atualizado

    U->>FE: Acompanha dashboard e leads
    FE->>BE: GET /dashboard/stats, /leads, /leads/{id}
    BE->>DB: Consulta indicadores e detalhes
    DB-->>BE: Dados agregados
    BE-->>FE: Lista priorizada e KPI
```

## 2. Cadastro e Login

```mermaid
sequenceDiagram
    autonumber
    participant U as Usuario
    participant FE as Frontend
    participant BE as Backend
    participant DB as Banco

    alt Primeiro acesso (cadastro)
        U->>FE: Preenche formulario de cadastro
        FE->>BE: POST /auth/register
        BE->>DB: Cria tenant e usuario
        DB-->>BE: Registro concluido
        BE-->>FE: JWT e dados iniciais
        FE->>FE: Salva token no localStorage
    else Usuario existente (login)
        U->>FE: Preenche email e senha
        FE->>BE: POST /auth/login
        BE->>DB: Valida credenciais
        DB-->>BE: Credenciais validas
        BE-->>FE: JWT
        FE->>FE: Restaura sessao no auth-context
    end

    FE->>BE: GET /auth/me
    BE-->>FE: Perfil autenticado
```

## 3. Onboarding e Configuracao de Funil

```mermaid
sequenceDiagram
    autonumber
    participant U as Usuario
    participant FE as Frontend
    participant BE as Backend
    participant DB as Banco

    U->>FE: Abre onboarding
    FE->>BE: GET /auth/funnel-templates
    BE-->>FE: Templates disponiveis

    U->>FE: Seleciona template e ajusta etapas
    FE->>BE: PUT /tenants/me/funnel
    BE->>DB: Atualiza funnel_stages do tenant
    DB-->>BE: Atualizacao persistida
    BE-->>FE: Funil atualizado

    U->>FE: Acessa dashboard inicial
    FE->>BE: GET /dashboard/stats
    BE-->>FE: Estado inicial da operacao
```

## 4. Conexao WhatsApp (QR Code)

```mermaid
sequenceDiagram
    autonumber
    participant U as Usuario
    participant FE as Frontend
    participant BE as Backend
    participant PF as Provider Factory
    participant WA as WAHA ou Evolution
    participant DB as Banco

    U->>FE: Clica em conectar WhatsApp
    FE->>BE: POST /whatsapp/connect
    BE->>PF: Resolve provider por WHATSAPP_PROVIDER
    PF-->>BE: Adapter do provider
    BE->>WA: create_session(session_id)
    WA-->>BE: Sessao criada/recuperada
    BE->>DB: Persiste estado da sessao
    DB-->>BE: Sessao salva
    BE-->>FE: Sessao iniciada

    FE->>BE: GET /whatsapp/qrcode
    BE->>WA: fetch_qr_code(session_id)
    WA-->>BE: QR Code base64
    BE-->>FE: QR Code
    U->>WA: Escaneia QR no app WhatsApp

    FE->>BE: GET /whatsapp/status
    BE->>WA: fetch_session_status(session_id)
    WA-->>BE: CONNECTED
    BE-->>FE: Status conectado
```

## 5. Ingestao de Mensagens e Criacao de Leads

```mermaid
sequenceDiagram
    autonumber
    participant C as Contato do Lead
    participant WA as Provider WhatsApp
    participant BE as Backend Webhook
    participant DB as Banco

    C->>WA: Envia mensagem no WhatsApp
    WA->>BE: POST /webhooks/whatsapp
    BE->>BE: Valida assinatura HMAC e tenant
    BE->>BE: Normaliza payload por provider

    alt Lead novo
        BE->>DB: Cria Lead + primeira Message
        DB-->>BE: Lead criado
    else Lead existente
        BE->>DB: Salva Message no lead existente
        DB-->>BE: Mensagem anexada
    end

    BE-->>WA: 200 OK
```

## 6. Analise de Leads com IA

```mermaid
sequenceDiagram
    autonumber
    participant U as Usuario
    participant FE as Frontend
    participant BE as Backend Analysis
    participant DB as Banco
    participant LLM as LiteLLM

    U->>FE: Solicita analisar lead
    FE->>BE: POST /leads/{id}/analyze
    BE->>DB: Tenta lock otimista is_processing

    alt Lock adquirido
        DB-->>BE: Lock ativo para analise
        BE->>LLM: Envia contexto de mensagens e funil
        LLM-->>BE: Score, etapa, resumo e resposta sugerida
        BE->>DB: Persiste Analysis e atualiza Lead
        DB-->>BE: Persistencia concluida
        BE->>DB: Libera lock
        DB-->>BE: Lock liberado
        BE-->>FE: Resultado de analise
    else Lead em processamento
        DB-->>BE: Lock rejeitado
        BE-->>FE: Erro de concorrencia orientando retry
    end
```

## 7. Operacao Diaria: Dashboard e Gestao Manual

```mermaid
sequenceDiagram
    autonumber
    participant U as Usuario
    participant FE as Frontend
    participant BE as Backend Dashboard
    participant DB as Banco

    U->>FE: Abre dashboard
    FE->>BE: GET /dashboard/stats
    BE->>DB: Calcula KPIs agregados
    DB-->>BE: Totais por status e etapa
    BE-->>FE: KPIs atualizados

    U->>FE: Filtra e abre lista de leads
    FE->>BE: GET /leads?filtros
    BE->>DB: Busca leads com ordenacao/prioridade
    DB-->>BE: Lista paginada
    BE-->>FE: Leads para exibicao

    U->>FE: Abre detalhe de lead
    FE->>BE: GET /leads/{id} e /leads/{id}/messages
    BE->>DB: Busca historico e ultima analise
    DB-->>BE: Dados completos
    BE-->>FE: Timeline e contexto do lead

    U->>FE: Ajusta status ou etapa manualmente
    FE->>BE: PATCH /leads/{id}/status ou /leads/{id}/stage
    BE->>DB: Persiste override manual
    DB-->>BE: Atualizacao concluida
    BE-->>FE: Estado final atualizado
```

## 8. Loop Continuo da Operacao Comercial

```mermaid
sequenceDiagram
    autonumber
    participant WA as WhatsApp
    participant BE as Backend
    participant FE as Frontend
    participant U as Usuario

    loop Ciclo diario
        WA->>BE: Novas mensagens via webhook
        BE-->>FE: Dados atualizados para consultas
        U->>FE: Revisa prioridades e analises
        U->>FE: Executa contatos comerciais
        U->>FE: Atualiza status/etapa conforme resultado
    end
```

## Observacoes

- Os diagramas representam os fluxos principais da arquitetura atual e os endpoints publicos existentes.
- A selecao do provider WhatsApp e transparente para o frontend, ficando encapsulada no backend.
- A jornada combina automacao (webhooks e IA) com governanca humana (ajustes manuais de status e etapa).
