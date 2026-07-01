"""Executa benchmark de analise IA para lote de leads e gera relatorio.

Uso:
  PYTHONPATH=. python3 frontend/tests/scripts/run_analysis_benchmark.py

Premissas:
- backend ja em execucao
- usuario benchmark sera criado automaticamente se nao existir
- analise via Ollama direto, conforme .env atual
"""

from __future__ import annotations

import asyncio
import os
import statistics
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.models import AnalysisStatus, Lead, User

API_BASE_URL = os.getenv("BENCHMARK_API_BASE", "http://localhost:8000")
BENCHMARK_EMAIL = os.getenv("BENCHMARK_EMAIL", "benchmark@teste.com")
BENCHMARK_PASSWORD = os.getenv("BENCHMARK_PASSWORD", "123456")
POLL_INTERVAL_SECONDS = float(os.getenv("BENCHMARK_POLL_INTERVAL", "2"))
TIMEOUT_SECONDS = int(os.getenv("BENCHMARK_TIMEOUT_SECONDS", "3600"))


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _login(client: httpx.AsyncClient) -> str:
    resp = await client.post(
        "/auth/login",
        json={"email": BENCHMARK_EMAIL, "password": BENCHMARK_PASSWORD},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


async def _ensure_benchmark_user_exists(client: httpx.AsyncClient) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == BENCHMARK_EMAIL))
        existing = result.scalar_one_or_none()

    if existing is not None:
        return

    resp = await client.post(
        "/auth/register",
        json={
            "email": BENCHMARK_EMAIL,
            "password": BENCHMARK_PASSWORD,
            "business_name": "Tenant Benchmark IA",
        },
    )
    resp.raise_for_status()


async def _enqueue_all(client: httpx.AsyncClient, token: str) -> dict[str, Any]:
    resp = await client.post(
        "/leads/analyze-all",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    return resp.json()


async def _poll_until_done(client: httpx.AsyncClient, token: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    deadline = time.monotonic() + TIMEOUT_SECONDS
    history: list[dict[str, Any]] = []

    while True:
        resp = await client.get(
            "/leads/analyze/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        payload = resp.json()

        snapshot = {
            "ts": _iso_now(),
            "pending": payload["counts"]["pending"],
            "processing": payload["counts"]["processing"],
            "completed": payload["counts"]["completed"],
            "failed": payload["counts"]["failed"],
        }
        history.append(snapshot)
        print(snapshot)

        if snapshot["pending"] == 0 and snapshot["processing"] == 0:
            return payload, history

        if time.monotonic() >= deadline:
            raise TimeoutError("Benchmark atingiu timeout antes de concluir a fila")

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def _fetch_latency_report() -> dict[str, Any]:
    async with AsyncSessionLocal() as session:
        user_result = await session.execute(select(User).where(User.email == BENCHMARK_EMAIL))
        user = user_result.scalar_one_or_none()
        if user is None:
            raise RuntimeError("Usuario benchmark nao encontrado")

        leads_result = await session.execute(
            select(Lead).where(Lead.tenant_id == user.tenant_id)
        )
        leads = list(leads_result.scalars().all())

    completed_latencies: list[float] = []
    failed_count = 0
    error_samples: list[str] = []

    for lead in leads:
        if lead.analysis_status == AnalysisStatus.completed and lead.analysis_requested_at and lead.analysis_completed_at:
            delta = lead.analysis_completed_at - lead.analysis_requested_at
            completed_latencies.append(delta.total_seconds())
        elif lead.analysis_status == AnalysisStatus.failed:
            failed_count += 1
            if lead.analysis_error:
                error_samples.append(lead.analysis_error)

    completed_count = len(completed_latencies)
    total = len(leads)
    p50 = statistics.median(completed_latencies) if completed_latencies else None
    p95 = None
    if completed_count >= 2:
        sorted_lat = sorted(completed_latencies)
        idx = int((0.95 * (completed_count - 1)))
        p95 = sorted_lat[idx]

    avg = statistics.mean(completed_latencies) if completed_latencies else None
    max_latency = max(completed_latencies) if completed_latencies else None

    return {
        "total_leads": total,
        "completed": completed_count,
        "failed": failed_count,
        "failed_ratio": (failed_count / total) if total else 0.0,
        "latency_p50_s": p50,
        "latency_p95_s": p95,
        "latency_avg_s": avg,
        "latency_max_s": max_latency,
        "error_samples": error_samples[:5],
    }


async def main() -> None:
    print("benchmark_started_at", _iso_now())
    print("api_base", API_BASE_URL)
    print("email", BENCHMARK_EMAIL)

    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        await _ensure_benchmark_user_exists(client)
        token = await _login(client)
        enqueue_result = await _enqueue_all(client, token)
        print("enqueue_result", enqueue_result)

        final_status, history = await _poll_until_done(client, token)
        print("final_status_counts", final_status["counts"])
        print("poll_points", len(history))

    report = await _fetch_latency_report()
    print("report", report)

    go_no_go = {
        "criterion_latency_p95_le_30s": report["latency_p95_s"] is not None and report["latency_p95_s"] <= 30,
        "criterion_no_oom": "manual_check_required",
        "criterion_failure_ratio_lt_15pct": report["failed_ratio"] < 0.15,
    }
    print("go_no_go", go_no_go)
    print("benchmark_finished_at", _iso_now())


if __name__ == "__main__":
    asyncio.run(main())
