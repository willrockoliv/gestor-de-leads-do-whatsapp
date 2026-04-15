from pydantic import BaseModel, Field


class LLMAnalysisResult(BaseModel):
    temperature_score: int = Field(ge=0, le=100)
    current_stage: str
    conversation_summary: str
    qualitative_tips: str
    suggested_reply: str


class AnalysisResponse(BaseModel):
    id: str
    lead_id: str
    temperature_score: int
    current_stage: str | None
    conversation_summary: str
    qualitative_tips: str
    suggested_reply: str

    model_config = {"from_attributes": True}


class AnalyzeBatchResponse(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: list[dict]
