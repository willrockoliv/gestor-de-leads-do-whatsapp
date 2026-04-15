from app.services.webhook_service import (
    extract_phone,
    extract_message_text,
    ingest_message_sync,
)


def test_extract_phone():
    assert extract_phone("5511999999999@s.whatsapp.net") == "5511999999999"
    assert extract_phone("5521888888888@s.whatsapp.net") == "5521888888888"


def test_extract_message_text_conversation():
    msg = {"conversation": "Olá, tudo bem?"}
    assert extract_message_text(msg) == "Olá, tudo bem?"


def test_extract_message_text_extended():
    msg = {"extendedTextMessage": {"text": "Mensagem longa aqui"}}
    assert extract_message_text(msg) == "Mensagem longa aqui"


def test_extract_message_text_image():
    msg = {"imageMessage": {"caption": "Foto do produto"}}
    assert extract_message_text(msg) == "Foto do produto"


def test_extract_message_text_image_no_caption():
    msg = {"imageMessage": {}}
    assert extract_message_text(msg) == "[imagem]"


def test_extract_message_text_audio():
    msg = {"audioMessage": {"seconds": 10}}
    assert extract_message_text(msg) == "[áudio]"


def test_extract_message_text_document():
    msg = {"documentMessage": {"fileName": "orcamento.pdf"}}
    assert extract_message_text(msg) == "[documento]"


def test_extract_message_text_none():
    assert extract_message_text(None) == ""


def test_extract_message_text_unknown():
    msg = {"unknownType": {}}
    assert extract_message_text(msg) == "[mensagem não suportada]"


def test_ingest_sync_new_lead():
    result = ingest_message_sync(
        phone="5511999999999",
        push_name="João",
        content="Oi",
        from_me=False,
        lead_status=None,
    )
    assert result["discarded"] is False
    assert result["is_new_lead"] is True
    assert result["direction"] == "inbound"


def test_ingest_sync_active_lead():
    result = ingest_message_sync(
        phone="5511999999999",
        push_name="João",
        content="Oi",
        from_me=False,
        lead_status="active",
    )
    assert result["discarded"] is False
    assert result["is_new_lead"] is False


def test_ingest_sync_converted_lead():
    result = ingest_message_sync(
        phone="5511999999999",
        push_name="João",
        content="Oi",
        from_me=False,
        lead_status="converted",
    )
    assert result["discarded"] is True


def test_ingest_sync_lost_lead():
    result = ingest_message_sync(
        phone="5511999999999",
        push_name="João",
        content="Oi",
        from_me=False,
        lead_status="lost",
    )
    assert result["discarded"] is True


def test_ingest_sync_outbound():
    result = ingest_message_sync(
        phone="5511999999999",
        push_name=None,
        content="Olá!",
        from_me=True,
        lead_status="active",
    )
    assert result["direction"] == "outbound"
