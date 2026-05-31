import uuid

from app.models import (Analysis, Lead, LeadStatus, Message, MessageDirection,
                        SessionStatus, Tenant, User, WhatsAppSession)


def test_tenant_creation():
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Loja Teste",
        funnel_config={"etapa_1": "Descoberta", "etapa_2": "Orçamento"},
    )
    assert tenant.name == "Loja Teste"
    assert tenant.funnel_config["etapa_1"] == "Descoberta"


def test_user_creation():
    tenant_id = uuid.uuid4()
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email="user@test.com",
        hashed_password="hashed",
    )
    assert user.email == "user@test.com"
    assert user.tenant_id == tenant_id


def test_whatsapp_session_creation():
    session = WhatsAppSession(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        status=SessionStatus.disconnected,
    )
    assert session.status == SessionStatus.disconnected


def test_lead_creation():
    lead = Lead(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        phone="5511999999999",
        name="João",
        status=LeadStatus.active,
        is_processing=False,
    )
    assert lead.phone == "5511999999999"
    assert lead.status == LeadStatus.active
    assert lead.is_processing is False


def test_lead_status_enum():
    assert LeadStatus.active == "active"
    assert LeadStatus.converted == "converted"
    assert LeadStatus.lost == "lost"


def test_message_creation():
    msg = Message(
        id=uuid.uuid4(),
        lead_id=uuid.uuid4(),
        direction=MessageDirection.inbound,
        content="Olá, quero saber o preço",
    )
    assert msg.direction == MessageDirection.inbound
    assert "preço" in msg.content


def test_analysis_creation():
    analysis = Analysis(
        id=uuid.uuid4(),
        lead_id=uuid.uuid4(),
        temperature_score=75,
        current_stage="Orçamento Enviado",
        conversation_summary="Cliente perguntou sobre preço",
        qualitative_tips="Lead demonstra alta intenção de compra",
        suggested_reply="Olá! O valor é R$100. Posso te ajudar?",
    )
    assert analysis.temperature_score == 75
    assert analysis.current_stage == "Orçamento Enviado"


def test_message_direction_enum():
    assert MessageDirection.inbound == "inbound"
    assert MessageDirection.outbound == "outbound"


def test_lead_defaults():
    """SQLAlchemy defaults only apply at DB INSERT. Test nullable fields are None on construction."""
    lead = Lead(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        phone="5511888888888",
    )
    assert lead.temperature_score is None
    assert lead.current_stage is None
    assert lead.name is None
