from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Mapping


AI_PROVIDER_HEALTH_PATH_ENV = "STOCKANALYSIS_AI_PROVIDER_HEALTH_PATH"
OPENAI_HEALTH_TTL_SECONDS_ENV = "STOCKANALYSIS_OPENAI_HEALTH_TTL_SECONDS"
OPENAI_ADMIN_API_KEY_ENV = "OPENAI_ADMIN_API_KEY"
DEFAULT_AI_PROVIDER_HEALTH_PATH = "/private/tmp/stockanalysis-runtime/ai-provider-health.json"
DEFAULT_OPENAI_HEALTH_TTL_SECONDS = 21600
OPENAI_PROVIDER = "agents_sdk_openai"
OPENAI_FALLBACK_BLOCKING_CODES = frozenset(
    {
        "openai_insufficient_quota",
        "openai_billing_unavailable",
        "openai_auth_invalid",
        "openai_provider_disabled",
    }
)


@dataclass(frozen=True)
class CachedProviderBlock:
    provider: str
    status: str
    error_code: str
    message: str
    last_checked_at: str
    next_retry_at: str
    fallback_provider: str
    local_fallback_provider: str


def provider_health_path(env: Mapping[str, str] | None = None) -> Path:
    env_mapping = env if env is not None else os.environ
    return Path(str(env_mapping.get(AI_PROVIDER_HEALTH_PATH_ENV) or DEFAULT_AI_PROVIDER_HEALTH_PATH))


def record_provider_failure(
    *,
    provider: str,
    error_code: str,
    message: str,
    fallback_provider: str,
    local_fallback_provider: str,
    retryable: bool,
    env: Mapping[str, str] | None = None,
    now: datetime | None = None,
) -> dict[str, object]:
    env_mapping = env if env is not None else os.environ
    checked_at = now or datetime.now(timezone.utc)
    ttl_seconds = _ttl_seconds(env_mapping)
    next_retry_at = checked_at + timedelta(seconds=ttl_seconds if retryable else ttl_seconds)
    payload = {
        "provider": provider,
        "status": "fallback_required",
        "error_code": error_code,
        "message": message,
        "last_checked_at": checked_at.isoformat(),
        "next_retry_at": next_retry_at.isoformat(),
        "fallback_provider": fallback_provider,
        "local_fallback_provider": local_fallback_provider,
        "retryable": retryable,
        "health_ttl_seconds": ttl_seconds,
    }
    path = provider_health_path(env_mapping)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def load_cached_openai_provider_block(
    *,
    env: Mapping[str, str] | None = None,
    now: datetime | None = None,
) -> CachedProviderBlock | None:
    env_mapping = env if env is not None else os.environ
    path = provider_health_path(env_mapping)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    provider = str(payload.get("provider") or "")
    error_code = str(payload.get("error_code") or "")
    if provider != OPENAI_PROVIDER or error_code not in OPENAI_FALLBACK_BLOCKING_CODES:
        return None
    next_retry_at = _parse_datetime(str(payload.get("next_retry_at") or ""))
    if next_retry_at is not None and (now or datetime.now(timezone.utc)) >= next_retry_at:
        return None
    return CachedProviderBlock(
        provider=provider,
        status=str(payload.get("status") or "fallback_required"),
        error_code=error_code,
        message=str(payload.get("message") or "OpenAI provider is blocked by cached provider health."),
        last_checked_at=str(payload.get("last_checked_at") or ""),
        next_retry_at=str(payload.get("next_retry_at") or ""),
        fallback_provider=str(payload.get("fallback_provider") or "codex_oauth"),
        local_fallback_provider=str(payload.get("local_fallback_provider") or "local_rules"),
    )


def build_openai_provider_health_visibility(env: Mapping[str, str] | None = None) -> dict[str, object]:
    env_mapping = env if env is not None else os.environ
    cached = load_cached_openai_provider_block(env=env_mapping)
    api_key_configured = bool(str(env_mapping.get("OPENAI_API_KEY") or "").strip())
    admin_key_configured = bool(str(env_mapping.get(OPENAI_ADMIN_API_KEY_ENV) or "").strip())
    if cached is not None:
        return {
            "status": cached.error_code,
            "label": "OpenAI 사용 불가",
            "balance_known": False,
            "balance_check_method": "cached_provider_error",
            "remaining_balance_usd": None,
            "api_key_configured": api_key_configured,
            "admin_api_key_configured": admin_key_configured,
            "last_checked_at": cached.last_checked_at,
            "next_retry_at": cached.next_retry_at,
            "fallback_provider": cached.fallback_provider,
            "local_fallback_provider": cached.local_fallback_provider,
            "message": cached.message,
        }
    if not api_key_configured:
        return {
            "status": "missing_api_key",
            "label": "OpenAI 키 없음",
            "balance_known": False,
            "balance_check_method": "not_available",
            "remaining_balance_usd": None,
            "api_key_configured": False,
            "admin_api_key_configured": admin_key_configured,
            "last_checked_at": "",
            "next_retry_at": "",
            "fallback_provider": "codex_oauth",
            "local_fallback_provider": "local_rules",
            "message": "OpenAI API key가 없어 fallback provider를 사용한다.",
        }
    return {
        "status": "key_configured_balance_unverified",
        "label": "잔액 미확인",
        "balance_known": False,
        "balance_check_method": "admin_costs_api_required_or_provider_error_cache",
        "remaining_balance_usd": None,
        "api_key_configured": True,
        "admin_api_key_configured": admin_key_configured,
        "last_checked_at": "",
        "next_retry_at": "",
        "fallback_provider": "codex_oauth",
        "local_fallback_provider": "local_rules",
        "message": (
            "일반 API key만으로 남은 잔액을 확정 조회하지 않는다. "
            "Admin API costs 조회 또는 실제 provider 실패 캐시로 상태를 판단한다."
        ),
    }


def _ttl_seconds(env: Mapping[str, str]) -> int:
    raw = str(env.get(OPENAI_HEALTH_TTL_SECONDS_ENV) or "").strip()
    if not raw:
        return DEFAULT_OPENAI_HEALTH_TTL_SECONDS
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_OPENAI_HEALTH_TTL_SECONDS
    return max(60, value)


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed
