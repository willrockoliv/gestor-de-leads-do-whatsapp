from typing import Literal

from pydantic import BaseModel, Field


class LLMAnalysisResult(BaseModel):
    temperature_score: int = Field(
        ge=0,
        le=100,
        description="Pontuação de temperatura do lead calculada pela IA, de 0 a 100.",
        examples=[82],
    )
    current_stage: str = Field(
        description="Etapa atual do lead no funil configurado para o tenant.",
        examples=["Proposta enviada"],
    )
    conversation_summary: str = Field(
        description="Resumo curto da conversa usado para contextualização comercial.",
        examples=["Lead pediu proposta e demonstrou urgência para fechamento ainda hoje."],
    )
    qualitative_tips: str = Field(
        description="Sugestões qualitativas para abordagem comercial do lead.",
        examples=["Responder com objetividade, reforçando prazo e próximos passos."],
    )
    suggested_reply: str = Field(
        description="Resposta sugerida pela IA para continuidade da conversa.",
        examples=["Posso te enviar a proposta final agora e alinhar a ativação ainda hoje."],
    )


class AnalysisJobAcceptedResponse(BaseModel):
    lead_id: str = Field(
        description="Identificador do lead que foi enfileirado para análise.",
        examples=["5a3c1d3e-2f64-4d8d-8b89-1d0f4637f7f3"],
    )
    analysis_status: Literal["pending"] = Field(
        description="Status inicial retornado após o aceite da solicitação assíncrona.",
        examples=["pending"],
    )

    model_config = {"from_attributes": True}


class AnalyzeBatchResponse(BaseModel):
    total_enqueued: int = Field(
        description="Quantidade de leads ativos do tenant enfileirados para análise.",
        examples=[12],
    )
    lead_ids: list[str] = Field(
        default_factory=list,
        description="Lista de identificadores dos leads que entraram na fila.",
        examples=[["5a3c1d3e-2f64-4d8d-8b89-1d0f4637f7f3", "7f04eb24-0f66-4b9b-8f1e-13cf69b9670a"]],
    )


class AnalyzeStatusCounts(BaseModel):
    idle: int = Field(default=0, description="Quantidade de leads sem solicitação de análise pendente.")
    pending: int = Field(default=0, description="Quantidade de leads aguardando processamento na fila.")
    processing: int = Field(default=0, description="Quantidade de leads com análise em execução.")
    completed: int = Field(default=0, description="Quantidade de leads com análise concluída com sucesso.")
    failed: int = Field(default=0, description="Quantidade de leads cuja análise terminou com falha.")


class AnalyzeStatusResponse(BaseModel):
    counts: AnalyzeStatusCounts = Field(
        description="Contadores agregados por status de análise no escopo consultado."
    )
    pending_ids: list[str] = Field(
        default_factory=list,
        description="IDs dos leads que ainda aguardam processamento.",
    )
    processing_ids: list[str] = Field(
        default_factory=list,
        description="IDs dos leads atualmente em processamento.",
    )
    completed_ids: list[str] = Field(
        default_factory=list,
        description="IDs dos leads cuja análise foi concluída com sucesso.",
    )
    failed_ids: list[str] = Field(
        default_factory=list,
        description="IDs dos leads cuja análise falhou.",
    )


class AnalysisLeadStatusResponse(BaseModel):
    lead_id: str = Field(
        description="Identificador do lead consultado.",
        examples=["5a3c1d3e-2f64-4d8d-8b89-1d0f4637f7f3"],
    )
    analysis_status: Literal["idle", "pending", "processing", "completed", "failed"] = Field(
        description="Status atual da análise do lead.",
        examples=["processing"],
    )
    analysis_error: str | None = Field(
        default=None,
        description="Mensagem padronizada de erro quando a análise termina em falha.",
        examples=["Timeout ao chamar provedor de IA"],
    )

    model_config = {"from_attributes": True}
