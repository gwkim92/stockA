from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable, Mapping


OPENAI_ADMIN_API_KEY_ENV = "OPENAI_ADMIN_API_KEY"
OPENAI_COST_STATUS_PATH_ENV = "STOCKANALYSIS_OPENAI_COST_STATUS_PATH"
DEFAULT_OPENAI_COST_STATUS_PATH = "/private/tmp/stockanalysis-runtime/openai-admin-cost-status.json"
OPENAI_COSTS_URL = "https://api.openai.com/v1/organization/costs"
BILLING_OVERVIEW_URL = "https://platform.openai.com/settings/organization/billing/overview"
DEFAULT_LOOKBACK_DAYS = 7
MAX_LOOKBACK_DAYS = 180

Urlopen = Callable[[urllib.request.Request, float], Any]


def openai_cost_status_path(env: Mapping[str, str] | None = None) -> Path:
    env_mapping = env if env is not None else os.environ
    return Path(str(env_mapping.get(OPENAI_COST_STATUS_PATH_ENV) or DEFAULT_OPENAI_COST_STATUS_PATH))


def build_default_openai_cost_status(env: Mapping[str, str] | None = None) -> dict[str, object]:
    env_mapping = env if env is not None else os.environ
    admin_key_configured = bool(str(env_mapping.get(OPENAI_ADMIN_API_KEY_ENV) or "").strip())
    status = "costs_not_checked" if admin_key_configured else "admin_key_missing"
    message = (
        "Admin key는 설정됐지만 아직 비용 조회 batch가 실행되지 않았다."
        if admin_key_configured
        else "Admin Costs API key가 없어 비용 조회를 실행할 수 없다."
    )
    return {
        "report_name": "openai_admin_cost_status",
        "status": status,
        "cost_known": False,
        "admin_api_key_configured": admin_key_configured,
        "lookback_days": DEFAULT_LOOKBACK_DAYS,
        "total_cost_usd": None,
        "latest_day_cost_usd": None,
        "currency": "usd",
        "period_start": "",
        "period_end": "",
        "last_checked_at": "",
        "error_code": "",
        "message": message,
        "billing_overview_url": BILLING_OVERVIEW_URL,
        "secret_free": True,
    }


def load_cached_openai_cost_status(env: Mapping[str, str] | None = None) -> dict[str, object]:
    env_mapping = env if env is not None else os.environ
    path = openai_cost_status_path(env_mapping)
    default = build_default_openai_cost_status(env_mapping)
    if not path.is_file():
        return default
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    merged = dict(default)
    for key in (
        "status",
        "cost_known",
        "admin_api_key_configured",
        "lookback_days",
        "total_cost_usd",
        "latest_day_cost_usd",
        "currency",
        "period_start",
        "period_end",
        "last_checked_at",
        "error_code",
        "message",
        "billing_overview_url",
        "secret_free",
    ):
        if key in payload:
            merged[key] = payload[key]
    merged["admin_api_key_configured"] = bool(str(env_mapping.get(OPENAI_ADMIN_API_KEY_ENV) or "").strip())
    merged["secret_free"] = True
    return merged


def refresh_openai_cost_status(
    *,
    env: Mapping[str, str] | None = None,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    execute: bool = False,
    output_path: Path | None = None,
    now: datetime | None = None,
    timeout_seconds: float = 10.0,
    urlopen: Urlopen | None = None,
) -> dict[str, object]:
    env_mapping = env if env is not None else os.environ
    bounded_days = min(max(int(lookback_days), 1), MAX_LOOKBACK_DAYS)
    checked_at = now or datetime.now(timezone.utc)
    admin_key = str(env_mapping.get(OPENAI_ADMIN_API_KEY_ENV) or "").strip()
    target_path = output_path or openai_cost_status_path(env_mapping)

    if not execute:
        return _status_payload(
            status="not_executed",
            cost_known=False,
            admin_api_key_configured=bool(admin_key),
            lookback_days=bounded_days,
            checked_at=checked_at,
            message="--execute가 없어 OpenAI 비용 API를 호출하지 않았다.",
        )
    if not admin_key:
        payload = _status_payload(
            status="admin_key_missing",
            cost_known=False,
            admin_api_key_configured=False,
            lookback_days=bounded_days,
            checked_at=checked_at,
            error_code="missing_admin_api_key",
            message="OPENAI_ADMIN_API_KEY가 없어 비용 조회를 실행할 수 없다.",
        )
        _write_status(payload, target_path)
        return payload

    start_time = int((checked_at - timedelta(days=bounded_days)).timestamp())
    query = urllib.parse.urlencode({"start_time": start_time, "limit": bounded_days})
    request = urllib.request.Request(
        f"{OPENAI_COSTS_URL}?{query}",
        headers={
            "Authorization": f"Bearer {admin_key}",
            "Content-Type": "application/json",
        },
        method="GET",
    )
    opener = urlopen or _default_urlopen
    try:
        response = opener(request, timeout_seconds)
        raw = response.read()
        parsed = json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        payload = _http_error_payload(
            exc=exc,
            admin_key_configured=True,
            lookback_days=bounded_days,
            checked_at=checked_at,
        )
        _write_status(payload, target_path)
        return payload
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        payload = _status_payload(
            status="costs_fetch_failed",
            cost_known=False,
            admin_api_key_configured=True,
            lookback_days=bounded_days,
            checked_at=checked_at,
            error_code="network_or_parse_error",
            message=f"OpenAI 비용 조회에 실패했다: {type(exc).__name__}",
        )
        _write_status(payload, target_path)
        return payload

    payload = _parse_costs_payload(
        parsed,
        admin_key_configured=True,
        lookback_days=bounded_days,
        checked_at=checked_at,
    )
    _write_status(payload, target_path)
    return payload


def _default_urlopen(request: urllib.request.Request, timeout_seconds: float) -> Any:
    return urllib.request.urlopen(request, timeout=timeout_seconds)


def _parse_costs_payload(
    payload: object,
    *,
    admin_key_configured: bool,
    lookback_days: int,
    checked_at: datetime,
) -> dict[str, object]:
    if not isinstance(payload, Mapping):
        return _status_payload(
            status="costs_parse_failed",
            cost_known=False,
            admin_api_key_configured=admin_key_configured,
            lookback_days=lookback_days,
            checked_at=checked_at,
            error_code="unexpected_response_shape",
            message="OpenAI 비용 응답 형식이 예상과 다르다.",
        )
    buckets = payload.get("data")
    if not isinstance(buckets, list):
        buckets = []
    total_usd = Decimal("0")
    latest_day_usd: Decimal | None = None
    latest_bucket_end = 0
    first_start = ""
    last_end = ""
    for bucket in buckets:
        if not isinstance(bucket, Mapping):
            continue
        bucket_start = _optional_int(bucket.get("start_time")) or 0
        bucket_end = _optional_int(bucket.get("end_time")) or 0
        if bucket_start and not first_start:
            first_start = _timestamp_to_iso_date(bucket_start)
        if bucket_end:
            last_end = _timestamp_to_iso_date(bucket_end)
        bucket_total = Decimal("0")
        results = bucket.get("results")
        if not isinstance(results, list):
            continue
        for result in results:
            if not isinstance(result, Mapping):
                continue
            amount = result.get("amount")
            if not isinstance(amount, Mapping):
                continue
            currency = str(amount.get("currency") or "").lower()
            if currency != "usd":
                continue
            value = _optional_decimal(amount.get("value"))
            if value is None:
                continue
            total_usd += value
            bucket_total += value
        if bucket_end >= latest_bucket_end:
            latest_bucket_end = bucket_end
            latest_day_usd = bucket_total

    return _status_payload(
        status="costs_available",
        cost_known=True,
        admin_api_key_configured=admin_key_configured,
        lookback_days=lookback_days,
        checked_at=checked_at,
        total_cost_usd=float(total_usd),
        latest_day_cost_usd=float(latest_day_usd or Decimal("0")),
        period_start=first_start,
        period_end=last_end,
        message="OpenAI Admin Costs API에서 최근 비용을 조회했다. 남은 잔액은 공식 Costs API가 반환하지 않는다.",
    )


def _http_error_payload(
    *,
    exc: urllib.error.HTTPError,
    admin_key_configured: bool,
    lookback_days: int,
    checked_at: datetime,
) -> dict[str, object]:
    if exc.code in {401, 403}:
        status = "admin_auth_failed"
        error_code = "admin_api_key_rejected"
        message = "OpenAI Admin key 인증 또는 권한이 거부됐다."
    elif exc.code == 429:
        status = "costs_rate_limited"
        error_code = "admin_costs_rate_limited"
        message = "OpenAI Admin Costs API rate limit에 걸렸다."
    else:
        status = "costs_api_error"
        error_code = f"http_{exc.code}"
        message = f"OpenAI Admin Costs API가 HTTP {exc.code}를 반환했다."
    return _status_payload(
        status=status,
        cost_known=False,
        admin_api_key_configured=admin_key_configured,
        lookback_days=lookback_days,
        checked_at=checked_at,
        error_code=error_code,
        message=message,
    )


def _status_payload(
    *,
    status: str,
    cost_known: bool,
    admin_api_key_configured: bool,
    lookback_days: int,
    checked_at: datetime,
    total_cost_usd: float | None = None,
    latest_day_cost_usd: float | None = None,
    period_start: str = "",
    period_end: str = "",
    error_code: str = "",
    message: str,
) -> dict[str, object]:
    return {
        "report_name": "openai_admin_cost_status",
        "status": status,
        "cost_known": cost_known,
        "admin_api_key_configured": admin_api_key_configured,
        "lookback_days": lookback_days,
        "total_cost_usd": total_cost_usd,
        "latest_day_cost_usd": latest_day_cost_usd,
        "currency": "usd",
        "period_start": period_start,
        "period_end": period_end,
        "last_checked_at": checked_at.astimezone(timezone.utc).isoformat(),
        "error_code": error_code,
        "message": message,
        "billing_overview_url": BILLING_OVERVIEW_URL,
        "secret_free": True,
    }


def _write_status(payload: Mapping[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _timestamp_to_iso_date(value: int) -> str:
    return datetime.fromtimestamp(value, tz=timezone.utc).date().isoformat()


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_decimal(value: object) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
