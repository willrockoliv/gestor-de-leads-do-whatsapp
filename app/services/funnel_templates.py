FUNNEL_TEMPLATES = {
    "default": {
        "etapa_1": "Descoberta",
        "etapa_2": "Orçamento Enviado",
        "etapa_3": "Em Negociação",
        "etapa_4": "Fechamento",
    },
    "servicos": {
        "etapa_1": "Primeiro Contato",
        "etapa_2": "Levantamento de Necessidades",
        "etapa_3": "Proposta Enviada",
        "etapa_4": "Follow-up",
        "etapa_5": "Fechamento",
    },
    "ecommerce": {
        "etapa_1": "Interesse",
        "etapa_2": "Dúvidas sobre Produto",
        "etapa_3": "Aguardando Pagamento",
    },
    "imobiliaria": {
        "etapa_1": "Contato Inicial",
        "etapa_2": "Visita Agendada",
        "etapa_3": "Proposta",
        "etapa_4": "Documentação",
        "etapa_5": "Fechamento",
    },
}


def get_funnel_template(template_name: str) -> dict:
    return FUNNEL_TEMPLATES.get(template_name, FUNNEL_TEMPLATES["default"])


def list_funnel_templates() -> dict[str, dict]:
    return FUNNEL_TEMPLATES
