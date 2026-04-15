import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Text, Boolean, Integer, Float, ForeignKey, Enum, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LeadStatus(str, enum.Enum):
    active = "active"
    converted = "converted"
    lost = "lost"


class MessageDirection(str, enum.Enum):
    inbound = "inbound"
    outbound = "outbound"


class SessionStatus(str, enum.Enum):
    connected = "connected"
    disconnected = "disconnected"


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    funnel_config: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    users: Mapped[list["User"]] = relationship(back_populates="tenant")
    leads: Mapped[list["Lead"]] = relationship(back_populates="tenant")
    whatsapp_sessions: Mapped[list["WhatsAppSession"]] = relationship(back_populates="tenant")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tenant: Mapped["Tenant"] = relationship(back_populates="users")


class WhatsAppSession(Base):
    __tablename__ = "whatsapp_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), default=SessionStatus.disconnected
    )
    connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="whatsapp_sessions")


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    phone: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[LeadStatus] = mapped_column(Enum(LeadStatus), default=LeadStatus.active, insert_default=LeadStatus.active, index=True)
    current_stage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    temperature_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_processing: Mapped[bool] = mapped_column(Boolean, default=False, insert_default=False)
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    tenant: Mapped["Tenant"] = relationship(back_populates="leads")
    messages: Mapped[list["Message"]] = relationship(back_populates="lead", order_by="Message.timestamp")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="lead", order_by="Analysis.created_at.desc()")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("leads.id"), index=True)
    direction: Mapped[MessageDirection] = mapped_column(Enum(MessageDirection))
    content: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lead: Mapped["Lead"] = relationship(back_populates="messages")


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("leads.id"), index=True)
    temperature_score: Mapped[int] = mapped_column(Integer)
    current_stage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    conversation_summary: Mapped[str] = mapped_column(Text)
    qualitative_tips: Mapped[str] = mapped_column(Text)
    suggested_reply: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lead: Mapped["Lead"] = relationship(back_populates="analyses")
