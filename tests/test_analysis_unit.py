import json
import pytest

from app.services.analysis_service import (
    build_analysis_prompt_sync,
    parse_llm_response,
)
from app.schemas.analysis import LLMAnalysisResult


def test_build_prompt_sync():
    funnel = {"etapa_1": "Descoberta", "etapa_2": "Orçamento"}
    messages = [
        {"direction": "inbound", "content": "Oi, quero saber o preço"},
        {"direction": "outbound", "content": "Olá! O preço é R$100"},
        {"direction": "inbound", "content": "Achei caro, tem desconto?"},
    ]
    system, user = build_analysis_prompt_sync(funnel, messages)
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
