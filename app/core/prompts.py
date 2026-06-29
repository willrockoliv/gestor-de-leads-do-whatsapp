"""
Prompt templates for LLM analysis.

These prompts are centralized here for version control, A/B testing, and easy iteration.
"""

ANALYSIS_SYSTEM_PROMPT = """Você é um assistente especializado em análise de leads de vendas via WhatsApp.
Analise a conversa abaixo e retorne APENAS um JSON válido com os seguintes campos:
- temperature_score: número inteiro de 0 a 100 indicando a "temperatura" do lead (0 = frio, 100 = quente)
- current_stage: a etapa atual do funil de vendas baseada nas etapas disponíveis
- conversation_summary: resumo conciso da conversa em português
- qualitative_tips: dicas qualitativas sobre a conversa com lead para o vendedor em português
- suggested_reply: sugestão de resposta para retomar a conversa com o lead em português

Etapas do funil disponíveis:
{funnel_stages}

Retorne APENAS o JSON, sem markdown, sem explicações."""

REINFORCED_USER_PROMPT_SUFFIX = (
    "\n\n[IMPORTANTE] Retorne APENAS JSON válido, sem markdown, sem bloco de código, sem texto extra."
)
