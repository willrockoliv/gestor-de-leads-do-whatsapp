# 🚀 PRD: Micro SaaS de Triagem de Leads no WhatsApp

## 1. Visão Geral do Produto
Um software de gestão de leads via WhatsApp focado em empreendedores individuais e microempresas. O sistema atua de forma invisível no background (via WebSocket), lendo as mensagens e utilizando uma LLM para classificar a "temperatura" do lead, gerar resumos da conversa e sugerir respostas. O objetivo é reduzir o tempo gasto com contatos desqualificados e focar a energia nas oportunidades com maior intenção de compra.

## 2. Casos de Uso (O Core)
* **Captação Silenciosa:** O usuário continua utilizando seu WhatsApp normalmente (App ou Web). O sistema apenas escuta e armazena os eventos de mensagens de novos contatos.
* **Priorização Inteligente:** O usuário acessa um Dashboard web para visualizar a lista de leads ativos, ordenados por um "Score de Temperatura" (0 a 100).
* **Gestão e Resposta Rápida:** Ao analisar um lead, o usuário lê o resumo gerado pela IA, avalia a dica qualitativa e clica em "Responder", sendo redirecionado para o WhatsApp com a mensagem sugerida já preenchida na caixa de texto.

## 3. Arquitetura e Stack Tecnológica
* **Backend:** Python 3.11+ com FastAPI (Alta performance e suporte assíncrono nativo para lidar com webhooks e processamento em lote).
* **Banco de Dados:** PostgreSQL (Modelo relacional para garantir a integridade das travas de processamento e modelagem de leads/mensagens).
* **Inteligência Artificial:** Integração agnóstica de LLMs (ex: via biblioteca `litellm`), permitindo rotacionar facilmente entre provedores (OpenAI, Anthropic, Google).
* **WhatsApp API:** Biblioteca baseada em WebSockets (ex: Waha ou Evolution API) hospedada em serviço apartado.
* **Frontend:** Next.js, React, Tailwind CSS e componentes shadcn/ui.
* **Infraestrutura:** Backend em containers Docker (ex: AWS EC2, ECS ou Render) e o Frontend na Vercel.

## 4. Máquina de Estados e Modelagem Principal

### 4.1. Regras de Negócio de Contatos
Qualquer novo número que enviar mensagem é tratado como Lead Ativo. Apenas mensagens de números com `status = active` são enviadas para processamento.
* **Status Possíveis do Lead:** `active` (em negociação), `converted` (fechou negócio), `lost/discarded` (não tem interesse/curioso). 

### 4.2. O Funil Dinâmico e Controle Manual (Human-in-the-Loop)
A estrutura do funil não é hardcoded, sendo definida em um JSON configurável por usuário (Tenant). 
* *Exemplo:* `{"etapa_1": "Descoberta", "etapa_2": "Orçamento Enviado", "etapa_3": "Em negociação"}`.
* Esse JSON é injetado no *System Prompt* da LLM para que ela faça a inferência da etapa atual.
* **Controle Soberano:** O usuário sempre terá a opção de sobreescrever manualmente a etapa do funil de um lead através da interface, ignorando a inferência da IA para aquele contato (ex: negociação avançou por telefone).

---

## 5. Requisitos Funcionais (RFs)

### 5.1. Módulo de Onboarding (Frictionless)
* **RF01:** O sistema deve exibir um QR Code para conexão da sessão do WhatsApp logo no primeiro acesso após o cadastro.
* **RF02:** O sistema deve solicitar apenas o nome do negócio e a escolha de um template simples de funil de vendas (que poderá ser editado posteriormente).

### 5.2. Módulo de Ingestão de Dados (Webhooks)
* **RF03:** O backend deve possuir um endpoint (webhook) seguro para receber eventos de `message.upsert` da API não-oficial do WhatsApp.
* **RF04:** O sistema deve salvar o histórico de mensagens (enviadas e recebidas) exclusivamente de leads com o status `active`. Mensagens de contatos `converted` ou `lost` devem ser descartadas pelo backend.

### 5.3. Módulo de Inteligência e Concorrência (Gatilho Manual e em Lote)
* **RF05:** O Dashboard deve possuir um botão individual de "Atualizar Análise" para cada lead, e um botão global de "Atualizar Todos" para processar a fila de leads ativos com novas mensagens pendentes.
* **RF06:** Ao acionar a atualização, o backend deve implementar um *Optimistic Lock* (trava de banco de dados via coluna `is_processing` no PostgreSQL).
* **RF06.1 - Prevenção de Double Submit:** Qualquer requisição duplicada para um lead que já esteja com `is_processing = true` deve ser rejeitada imediatamente pela API (ex: `HTTP 409 Conflict`), evitando chamadas redundantes à LLM.
* **RF06.2 - Anti-Zombie Lock (Try/Finally):** Toda chamada à LLM deve ser encapsulada em blocos de tratamento de erro para garantir que a trava seja liberada (`is_processing = false`) em caso de falha na API externa ou erro de execução.
* **RF06.3 - Watchdog de Timeout:** O backend deve implementar uma rotina em background que identifique leads presos em processamento por mais de 5 minutos, resetando-os automaticamente para `false` e gerando um log de alerta.
* **RF07:** A IA deve retornar um JSON estruturado com: `temperature_score` (0-100), `current_stage`, `conversation_summary`, `qualitative_tips` e `suggested_reply`.
* **RF08:** Caso a atualização (individual ou em lote) apresente erro, a interface deve indicar visualmente quais leads falharam, permitindo nova tentativa.

### 5.4. Módulo Dashboard e Visualização (Read-Only)
* **RF09:** O front-end deve exibir uma interface visual do funil (Kanban ou listas categorizadas por etapa) refletindo o status manual ou inferido do lead.
* **RF10:** O Dashboard deve calcular e exibir consolidações numéricas em tempo real (total de leads por etapa) e permitir filtragem rápida.
* **RF11:** O sistema deve exibir o "Tempo de Conversa" (diferença entre timestamp da primeira e última mensagem da sessão atual) para cruzar visualmente com o score de temperatura.
* **RF12:** O painel de detalhe do lead deve exibir as análises da LLM (resumo e dicas qualitativas) de forma clara.
* **RF13:** O botão "Responder" deve redirecionar o usuário utilizando o padrão `wa.me/<numero>?text=<mensagem_sugerida_url_encoded>`.

### 5.5. Gestão de Contatos
* **RF14:** O usuário deve conseguir alterar manualmente o status de um lead para `converted` ou `lost/discarded`. Essa ação remove o lead do Dashboard de aquisição e encerra o processamento de novas mensagens daquele número.

---

## 6. Requisitos Não Funcionais (RNFs)

* **RNF01 - Graceful Degradation (Resiliência do WhatsApp):** Se a conexão WebSocket com o celular cair, o painel deve exibir um *soft warning* (aviso amigável não obstrutivo) solicitando a reconexão via QR Code. O usuário não deve ser impedido de navegar no Dashboard ou ler resumos antigos durante a queda de conexão.
* **RNF02 - Custos de IA e Escalabilidade:** O acionamento da LLM deve ser estritamente *On-Demand* (gatilho manual pelo usuário). O sistema não deve processar mensagens automaticamente por tempo ou evento de recebimento, protegendo a aplicação contra *floods* de mensagens e garantindo a previsibilidade de custo da API de inteligência artificial.
* **RNF03 - Zero Trust Architecture:** O sistema não deve confiar no estado do Frontend para controle de concorrência ou segurança. Validações de estado, limites de requisição e travas de processamento serão executados primariamente na camada de Banco de Dados e API.
* **RNF04 - Performance de Queries:** O carregamento inicial do Dashboard deve ser otimizado realizando *queries* diretas nas tabelas raw para extrair as volumetrias, sem a necessidade (neste MVP) de tabelas pré-calculadas complexas. A meta é carregamento inferior a 2 segundos.