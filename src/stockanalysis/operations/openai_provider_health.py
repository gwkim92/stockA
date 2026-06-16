from __future__ import annotations

import os
from typing import Mapping

from stockanalysis.ai_agents.provider_health import build_openai_provider_health_visibility


def build_openai_provider_health_report(env: Mapping[str, str] | None = None) -> dict[str, object]:
    env_mapping = env if env is not None else os.environ
    health = build_openai_provider_health_visibility(env_mapping)
    status = str(health.get("status") or "unknown")
    cost_status = health.get("cost_status") if isinstance(health.get("cost_status"), Mapping) else {}
    return {
        "report_name": "openai_provider_health",
        "status": status,
        "provider": "agents_sdk_openai",
        "health": health,
        "fallback_required": status
        in {
            "openai_insufficient_quota",
            "openai_billing_unavailable",
            "openai_auth_invalid",
            "openai_provider_disabled",
            "missing_api_key",
        },
        "secret_free": True,
        "next_action": _next_action(status, str(cost_status.get("status") or "")),
    }


def _next_action(status: str, cost_status: str = "") -> str:
    if status in {"openai_insufficient_quota", "openai_billing_unavailable"}:
        return "잔액 또는 quota가 복구될 때까지 codex_oauth/local_rules fallback을 사용한다."
    if status == "openai_auth_invalid":
        return "OpenAI API key를 교체한 뒤 provider health TTL 이후 다시 시도한다."
    if status == "openai_provider_disabled":
        return "운영자가 직접 호출 차단 플래그를 해제하기 전까지 OpenAI API를 호출하지 않는다."
    if status == "missing_api_key":
        return "OpenAI API key 없이 codex_oauth/local_rules fallback으로 실행한다."
    if status == "key_configured_balance_unverified":
        if cost_status == "costs_available":
            return "최근 비용은 Admin Costs API 캐시로 확인한다. 남은 잔액은 Billing Overview에서 직접 확인한다."
        return "Admin Costs API refresh를 실행해 최근 비용 캐시를 만들고, 남은 잔액은 Billing Overview에서 확인한다."
    return "OpenAI provider health 상태를 확인한다."
