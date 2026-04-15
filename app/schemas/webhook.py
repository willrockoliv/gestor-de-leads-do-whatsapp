from pydantic import BaseModel
from datetime import datetime


class WebhookMessageKey(BaseModel):
    remoteJid: str
    fromMe: bool
    id: str


class WebhookMessageData(BaseModel):
    key: WebhookMessageKey
    message: dict | None = None
    pushName: str | None = None
    messageTimestamp: int | None = None


class WebhookPayload(BaseModel):
    event: str
    instance: str | None = None
    data: WebhookMessageData


class MessageResponse(BaseModel):
    id: str
    lead_id: str
    direction: str
    content: str
    timestamp: datetime

    model_config = {"from_attributes": True}
