from datetime import datetime

from pydantic import BaseModel


class WhatsAppSessionResponse(BaseModel):
    session_id: str
    status: str


class QRCodeResponse(BaseModel):
    status: str
    qr_code: str | None = None
    phone: str | None = None


class ConnectionStatusResponse(BaseModel):
    status: str
    phone: str | None = None
    connected_since: datetime | None = None
