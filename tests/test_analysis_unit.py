import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.schemas.analysis import LLMAnalysisResult
from app.services.analysis_service import (
    build_analysis_prompt,
    parse_llm_response,
    _is_noise_only_message,
    _filter_noise_messages,
    _detect_conversion_intent,
)


def test_build_prompt_sync():
    funnel = {"etapa_1": "Descoberta", "etapa_2": "Orçamento"}
    now = datetime.now(timezone.utc)
    messages = [
        SimpleNamespace(
            direction=SimpleNamespace(value="inbound"),
            content="Oi, quero saber o preço",
            timestamp=now,
        ),
        SimpleNamespace(
            direction=SimpleNamespace(value="outbound"),
            content="Olá! O preço é R$100",
            timestamp=now,
        ),
        SimpleNamespace(
            direction=SimpleNamespace(value="inbound"),
            content="Achei caro, tem desconto?",
            timestamp=now,
        ),
    ]
    system, user = build_analysis_prompt(funnel, messages)
    assert "Descoberta" in system
    assert "Orçamento" in system
    assert "[LEAD]: Oi, quero saber o preço" in user
    assert "[VENDEDOR]: Olá! O preço é R$100" in user
    assert "[LEAD]: Achei caro, tem desconto?" in user


def test_parse_llm_response_valid():
    response = json.dumps({
        "temperature_score": 75,
        "current_stage": "Descoberta",
        "conversation_summary": "Cliente perguntou sobre preço",
        "qualitative_tips": "Lead demonstra interesse",
        "suggested_reply": "Posso fazer um desconto especial!",
    })
    result = parse_llm_response(response)
    assert isinstance(result, LLMAnalysisResult)
    assert result.temperature_score == 75
    assert result.current_stage == "Descoberta"


def test_parse_llm_response_with_markdown():
    response = """```json
{
    "temperature_score": 50,
    "current_stage": "Orçamento",
    "conversation_summary": "Resumo",
    "qualitative_tips": "Dicas",
    "suggested_reply": "Resposta"
}
```"""
    result = parse_llm_response(response)
    assert result.temperature_score == 50


def test_parse_llm_response_invalid_score():
    response = json.dumps({
        "temperature_score": 150,
        "current_stage": "X",
        "conversation_summary": "Y",
        "qualitative_tips": "Z",
        "suggested_reply": "W",
    })
    with pytest.raises(Exception):
        parse_llm_response(response)


def test_parse_llm_response_invalid_json():
    with pytest.raises(Exception):
        parse_llm_response("not json at all")


def test_parse_llm_response_missing_field():
    response = json.dumps({
        "temperature_score": 50,
        "current_stage": "X",
        # missing: conversation_summary, qualitative_tips, suggested_reply
    })
    with pytest.raises(Exception):
        parse_llm_response(response)


def test_parse_llm_response_score_boundaries():
    for score in [0, 50, 100]:
        response = json.dumps({
            "temperature_score": score,
            "current_stage": "Etapa",
            "conversation_summary": "Resumo",
            "qualitative_tips": "Dicas",
            "suggested_reply": "Resposta",
        })
        result = parse_llm_response(response)
        assert result.temperature_score == score

def test_parse_llm_response_normalizes_array_fields():
    """Test that LLM responses with arrays are normalized to strings."""
    response = json.dumps({
        "temperature_score": 80,
        "current_stage": "Negociação",  # string is OK
        "conversation_summary": ["resumo parte 1", "resumo parte 2"],  # array -> string
        "qualitative_tips": ["dica 1", "dica 2", "dica 3"],  # array -> string
        "suggested_reply": "Resposta simples",  # string is OK
    })
    result = parse_llm_response(response)
    assert isinstance(result.conversation_summary, str)
    assert isinstance(result.qualitative_tips, str)
    assert "resumo parte 1" in result.conversation_summary
    assert "resumo parte 2" in result.conversation_summary
    assert "dica 1" in result.qualitative_tips
    assert "dica 2" in result.qualitative_tips
    assert "dica 3" in result.qualitative_tips


def test_parse_llm_response_all_arrays():
    """Test that all text fields can be normalized from arrays."""
    response = json.dumps({
        "temperature_score": 75,
        "current_stage": ["Descoberta"],  # array
        "conversation_summary": ["Cliente", "quer", "comprar"],  # array
        "qualitative_tips": ["seja rápido", "ofereça desconto"],  # array
        "suggested_reply": ["Olá", "tudo bem"],  # array
    })
    result = parse_llm_response(response)
    assert result.temperature_score == 75
    assert isinstance(result.current_stage, str)
    assert isinstance(result.conversation_summary, str)
    assert isinstance(result.qualitative_tips, str)
    assert isinstance(result.suggested_reply, str)
    assert "Descoberta" in result.current_stage
    assert "Cliente" in result.conversation_summary
    assert "seja rápido" in result.qualitative_tips


# Tests for noise filtering
def test_is_noise_only_message_common_placeholders():
    """Test detection of common placeholder messages."""
    noise_messages = [
        "[imagem]",
        "[vídeo]",
        "[áudio]",
        "[sticker]",
        "[mensagem não suportada]",
        "[arquivo]",
        "[contato]",
        "[localização]",
        "[chamada de áudio]",
        "[chamada de vídeo]",
    ]
    for msg in noise_messages:
        assert _is_noise_only_message(msg) is True


def test_is_noise_only_message_case_insensitive():
    """Test that noise detection is case-insensitive."""
    assert _is_noise_only_message("[IMAGEM]") is True
    assert _is_noise_only_message("[Vídeo]") is True
    assert _is_noise_only_message("  [MENSAGEM NÃO SUPORTADA]  ") is True


def test_is_noise_only_message_long_urls():
    """Test detection of very long URLs (likely accidental/bot-generated)."""
    short_url = "https://example.com/page"
    long_url = "https://www.google.com/search?q=test&" + "a=b&" * 200  # > 500 chars
    
    assert _is_noise_only_message(short_url) is False
    assert _is_noise_only_message(long_url) is True


def test_is_noise_only_message_meaningful_content():
    """Test that meaningful messages are not filtered."""
    meaningful_messages = [
        "Oi, quero saber o preço",
        "Olá! O preço é R$100",
        "quero contratar seu serviço",
        "Achei caro, tem desconto?",
        "[imagem] veja essa foto do produto",  # Has context beyond placeholder
        "Enviou [vídeo] mostrando como funciona",  # Has context
    ]
    for msg in meaningful_messages:
        assert _is_noise_only_message(msg) is False


def test_filter_noise_messages():
    """Test filtering of noise messages from a conversation."""
    now = datetime.now(timezone.utc)
    messages = [
        SimpleNamespace(content="[imagem]", direction=SimpleNamespace(value="inbound"), timestamp=now),
        SimpleNamespace(content="Oi, tudo bem?", direction=SimpleNamespace(value="inbound"), timestamp=now),
        SimpleNamespace(content="[vídeo]", direction=SimpleNamespace(value="outbound"), timestamp=now),
        SimpleNamespace(content="Sim, tudo certo!", direction=SimpleNamespace(value="outbound"), timestamp=now),
        SimpleNamespace(content="[mensagem não suportada]", direction=SimpleNamespace(value="inbound"), timestamp=now),
        SimpleNamespace(content="quero comprar", direction=SimpleNamespace(value="inbound"), timestamp=now),
    ]
    
    filtered = _filter_noise_messages(messages)
    
    assert len(filtered) == 3
    assert filtered[0].content == "Oi, tudo bem?"
    assert filtered[1].content == "Sim, tudo certo!"
    assert filtered[2].content == "quero comprar"


def test_detect_conversion_intent_found():
    """Test detection of conversion intent with keywords."""
    now = datetime.now(timezone.utc)
    messages = [
        SimpleNamespace(content="Oi", direction=SimpleNamespace(value="inbound"), timestamp=now),
        SimpleNamespace(content="Qual é o valor?", direction=SimpleNamespace(value="inbound"), timestamp=now),
        SimpleNamespace(content="goste! quero contratar seu serviço", direction=SimpleNamespace(value="inbound"), timestamp=now),
    ]
    
    assert _detect_conversion_intent(messages) is True


def test_detect_conversion_intent_multiple_keywords():
    """Test detection with various conversion keywords."""
    now = datetime.now(timezone.utc)
    
    keywords_to_test = [
        "quero contratar",
        "quer contratar",
        "vou contratar",
        "desejo contratar",
        "vamos contratar",
        "quero comprar",
        "quer comprar",
        "vou comprar",
        "gostei e quero",
        "adorei e quero",
        "fechado",
        "combinado",
    ]
    
    for keyword in keywords_to_test:
        messages = [
            SimpleNamespace(content="Oi", direction=SimpleNamespace(value="inbound"), timestamp=now),
            SimpleNamespace(content=keyword, direction=SimpleNamespace(value="inbound"), timestamp=now),
        ]
        assert _detect_conversion_intent(messages) is True, f"Failed to detect keyword: {keyword}"


def test_detect_conversion_intent_not_found():
    """Test when no conversion intent is present."""
    now = datetime.now(timezone.utc)
    messages = [
        SimpleNamespace(content="Qual é o valor?", direction=SimpleNamespace(value="inbound"), timestamp=now),
        SimpleNamespace(content="Tem desconto?", direction=SimpleNamespace(value="inbound"), timestamp=now),
        SimpleNamespace(content="Me envia mais informações", direction=SimpleNamespace(value="inbound"), timestamp=now),
    ]
    
    assert _detect_conversion_intent(messages) is False


def test_detect_conversion_intent_only_checks_inbound():
    """Test that only inbound (LEAD) messages are checked."""
    now = datetime.now(timezone.utc)
    messages = [
        SimpleNamespace(content="Oi", direction=SimpleNamespace(value="inbound"), timestamp=now),
        SimpleNamespace(content="quero contratar", direction=SimpleNamespace(value="outbound"), timestamp=now),  # VENDEDOR said it, not lead
        SimpleNamespace(content="Tem desconto?", direction=SimpleNamespace(value="inbound"), timestamp=now),
    ]
    
    # Vendedor saying "quero contratar" doesn't count as lead conversion intent
    assert _detect_conversion_intent(messages) is False


def test_detect_conversion_intent_last_10_messages():
    """Test that conversion detection only checks last 10 inbound messages."""
    now = datetime.now(timezone.utc)
    messages = [
        SimpleNamespace(content="quero contratar", direction=SimpleNamespace(value="inbound"), timestamp=now),  # Position 0
    ]
    
    # Add 15 more inbound messages after (pushing the conversion keyword out of last 10)
    for i in range(15):
        messages.append(
            SimpleNamespace(content=f"Mensagem {i}", direction=SimpleNamespace(value="inbound"), timestamp=now)
        )
    
    # The conversion keyword is at position 0, now at position 0 of 16 total
    # Last 10 inbound are positions 6-15
    # So it should NOT be detected
    assert _detect_conversion_intent(messages) is False
    
    # But if we add conversion keyword in last 10, it should be detected
    messages_with_recent = messages[:6] + [
        SimpleNamespace(content="vou contratar", direction=SimpleNamespace(value="inbound"), timestamp=now),
    ]
    assert _detect_conversion_intent(messages_with_recent) is True


def test_detect_conversion_intent_case_insensitive():
    """Test that keyword detection is case-insensitive."""
    now = datetime.now(timezone.utc)
    messages = [
        SimpleNamespace(content="QUERO CONTRATAR", direction=SimpleNamespace(value="inbound"), timestamp=now),
    ]
    
    assert _detect_conversion_intent(messages) is True
    
    messages_mixed = [
        SimpleNamespace(content="GosTeI e QueRo Comprar", direction=SimpleNamespace(value="inbound"), timestamp=now),
    ]
    
    assert _detect_conversion_intent(messages_mixed) is True


def test_filter_and_detect_combined():
    """Integration test: filter noise then detect conversion in clean messages."""
    now = datetime.now(timezone.utc)
    messages = [
        SimpleNamespace(content="[imagem]", direction=SimpleNamespace(value="inbound"), timestamp=now),
        SimpleNamespace(content="DETRAN-SP: Descumprimento...", direction=SimpleNamespace(value="inbound"), timestamp=now),
        SimpleNamespace(content="0 🇩🇪⚽️", direction=SimpleNamespace(value="inbound"), timestamp=now),
        SimpleNamespace(content="[mensagem não suportada]", direction=SimpleNamespace(value="inbound"), timestamp=now),
        SimpleNamespace(content="goste! quero contratar seu serviço", direction=SimpleNamespace(value="inbound"), timestamp=now),
        SimpleNamespace(content="goste! quero contratar seu serviço", direction=SimpleNamespace(value="inbound"), timestamp=now),
    ]
    
    # Filter noise
    filtered = _filter_noise_messages(messages)
    assert len(filtered) == 4  # Only pure placeholders removed, meaningful messages remain
    
    # Detect conversion in filtered messages
    assert _detect_conversion_intent(filtered) is True
