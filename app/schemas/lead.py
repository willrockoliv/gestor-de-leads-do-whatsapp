from datetime import datetime

from pydantic import BaseModel


class LeadListItem(BaseModel):
    id: str
    phone: str
    name: str | None
    status: str
    current_stage: str | None
    temperature_score: int | None
    analysis_status: str
    analysis_error: str | None = None
    is_processing: bool
    created_at: datetime
    updated_at: datetime
    conversation_time_minutes: float | None = None

    model_config = {"from_attributes": True}


class LeadDetail(LeadListItem):
    latest_analysis: "AnalysisSummary | None" = None


class AnalysisSummary(BaseModel):
    id: str
    temperature_score: int
    current_stage: str | None
    conversation_summary: str
    qualitative_tips: str
    suggested_reply: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LeadStatusUpdate(BaseModel):
    status: str  # "converted" or "lost"


class LeadStageUpdate(BaseModel):
    current_stage: str


class DashboardStats(BaseModel):
    total_active: int
    total_converted: int
    total_lost: int
    leads_by_stage: dict[str, int]
    avg_temperature: float | None


class MessageItem(BaseModel):
    id: str
    direction: str
    content: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class PaginatedMessages(BaseModel):
    items: list[MessageItem]
    total: int
    page: int
    page_size: int
