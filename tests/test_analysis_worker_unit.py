from unittest.mock import AsyncMock, patch

import pytest

from app.services.analysis_service import process_next_pending_lead


@pytest.mark.asyncio
async def test_process_next_pending_lead_marks_failed_on_timeout():
    db = object()

    with patch("app.services.analysis_service.claim_next_pending_lead", new=AsyncMock(return_value="lead-1")):
        with patch("app.services.analysis_service.process_lead_analysis", new=AsyncMock(side_effect=TimeoutError("LLM timeout"))):
            with patch("app.services.analysis_service._mark_analysis_failed", new=AsyncMock()) as mark_failed:
                processed = await process_next_pending_lead(db)

    assert processed is True
    mark_failed.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_next_pending_lead_returns_false_when_queue_empty():
    db = object()

    with patch("app.services.analysis_service.claim_next_pending_lead", new=AsyncMock(return_value=None)):
        with patch("app.services.analysis_service.process_lead_analysis", new=AsyncMock()) as process_analysis:
            processed = await process_next_pending_lead(db)

    assert processed is False
    process_analysis.assert_not_awaited()


@pytest.mark.asyncio
async def test_parse_retry_recovers_after_invalid_first_response():
    with patch(
        "app.services.analysis_service.call_llm",
        new=AsyncMock(
            return_value='{"temperature_score": 70, "current_stage": "Descoberta", '
            '"conversation_summary": "Resumo", "qualitative_tips": "Dicas", '
            '"suggested_reply": "Resposta"}'
        ),
    ) as retried_call:
        with patch(
            "app.services.analysis_service.parse_llm_response",
            side_effect=[
                ValueError("bad json"),
                type("Parsed", (), {
                    "temperature_score": 70,
                    "current_stage": "Descoberta",
                    "conversation_summary": "Resumo",
                    "qualitative_tips": "Dicas",
                    "suggested_reply": "Resposta",
                })(),
            ],
        ):
            from app.services.analysis_service import parse_llm_response_with_retry

            parsed = await parse_llm_response_with_retry(
                response_text="invalid-first",
                system_prompt="system",
                user_prompt="user",
                retries=1,
            )

    assert parsed.temperature_score == 70
    retried_call.assert_awaited_once()
