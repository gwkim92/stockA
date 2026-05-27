from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


ALERT_DESTINATION_MODE_ENV = "STOCKANALYSIS_ALERT_DESTINATION_MODE"
ALERT_DESTINATION_URL_ENV = "STOCKANALYSIS_ALERT_DESTINATION_URL"
ALERT_WEBHOOK_URL_ENV = "STOCKANALYSIS_ALERT_WEBHOOK_URL"
DISCORD_WEBHOOK_URL_ENV = "STOCKANALYSIS_DISCORD_WEBHOOK_URL"
SLACK_WEBHOOK_URL_ENV = "STOCKANALYSIS_SLACK_WEBHOOK_URL"
NTFY_TOPIC_URL_ENV = "STOCKANALYSIS_NTFY_TOPIC_URL"
ALERT_DESTINATION_STATUS_PATH_ENV = "STOCKANALYSIS_ALERT_DESTINATION_STATUS_PATH"
DEFAULT_ALERT_TITLE = "Stockanalysis 운영 알림 테스트"
DEFAULT_ALERT_MESSAGE = "Stockanalysis alert destination reachability test."
SUPPORTED_DESTINATION_TYPES = ("webhook", "ntfy", "discord", "slack")


@dataclass(frozen=True)
class AlertHttpResult:
    status_code: int
    response_header_count: int = 0


AlertHttpPoster = Callable[[str, bytes, Mapping[str, str], float], AlertHttpResult]


def build_alert_destination_test_report(
    *,
    env: Mapping[str, str],
    execute: bool,
    now: datetime | None = None,
    title: str = DEFAULT_ALERT_TITLE,
    message: str = DEFAULT_ALERT_MESSAGE,
    destination_type: str | None = None,
    mode: str | None = None,
    timeout_seconds: float = 10.0,
    http_post: AlertHttpPoster | None = None,
) -> dict[str, object]:
    generated_at = _format_dt(now or datetime.now(timezone.utc))
    selected_type = _safe_token(destination_type or env.get("STOCKANALYSIS_ALERT_DESTINATION_TYPE") or "webhook")
    selected_mode = _safe_token(mode or env.get(ALERT_DESTINATION_MODE_ENV) or selected_type)
    target_url = _target_url_for_type(env=env, destination_type=selected_type)
    target_configured = bool(target_url)
    supported = selected_type in SUPPORTED_DESTINATION_TYPES

    status = "dry_run_not_sent"
    http_status_code: int | None = None
    http_status_class = "not_sent"
    error_type = ""

    if not supported:
        status = "unsupported_destination_type"
    elif not target_configured:
        status = "missing_target"
    elif execute:
        poster = http_post or _post_alert
        body, headers = _request_body_and_headers(
            destination_type=selected_type,
            title=title,
            message=message,
        )
        try:
            result = poster(target_url, body, headers, timeout_seconds)
            http_status_code = int(result.status_code)
            http_status_class = f"{http_status_code // 100}xx"
            status = "passed" if 200 <= http_status_code < 300 else "failed"
        except HTTPError as exc:
            http_status_code = int(exc.code)
            http_status_class = f"{http_status_code // 100}xx"
            status = "failed"
            error_type = "http_error"
        except (TimeoutError, URLError, OSError, socket.timeout):
            status = "failed"
            error_type = "network_error"

    last_test_status = "passed" if status == "passed" else ("not_executed" if not execute else "failed")
    report: dict[str, object] = {
        "report_name": "alert_destination_test",
        "generated_at": generated_at,
        "mode": selected_mode,
        "destination_type": selected_type,
        "target_configured": target_configured,
        "target_host": _safe_target_host(target_url),
        "execute": execute,
        "last_test_status": last_test_status,
        "last_tested_at": generated_at if execute else "",
        "status": status,
        "http_status_code": http_status_code,
        "http_status_class": http_status_class,
        "error_type": error_type,
        "secret_redaction": "destination_url_and_tokens_not_recorded",
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "order_boundary": "read_only_no_order",
    }
    return report


def _target_url_for_type(*, env: Mapping[str, str], destination_type: str) -> str:
    candidates: tuple[str, ...]
    if destination_type == "ntfy":
        candidates = (NTFY_TOPIC_URL_ENV, ALERT_DESTINATION_URL_ENV, ALERT_WEBHOOK_URL_ENV)
    elif destination_type == "discord":
        candidates = (DISCORD_WEBHOOK_URL_ENV, ALERT_DESTINATION_URL_ENV, ALERT_WEBHOOK_URL_ENV)
    elif destination_type == "slack":
        candidates = (SLACK_WEBHOOK_URL_ENV, ALERT_DESTINATION_URL_ENV, ALERT_WEBHOOK_URL_ENV)
    else:
        candidates = (ALERT_DESTINATION_URL_ENV, ALERT_WEBHOOK_URL_ENV)
    for key in candidates:
        value = str(env.get(key) or "").strip()
        if value:
            return value
    return ""


def _request_body_and_headers(*, destination_type: str, title: str, message: str) -> tuple[bytes, dict[str, str]]:
    if destination_type == "ntfy":
        return message.encode("utf-8"), {
            "Title": title,
            "Priority": "default",
            "Tags": "stockanalysis",
            "X-Cache": "no",
        }
    if destination_type == "discord":
        body = json.dumps({"content": f"**{title}**\n{message}"}, ensure_ascii=False).encode("utf-8")
        return body, {"Content-Type": "application/json"}
    if destination_type == "slack":
        body = json.dumps({"text": f"{title}\n{message}"}, ensure_ascii=False).encode("utf-8")
        return body, {"Content-Type": "application/json"}
    body = json.dumps(
        {"title": title, "message": message, "service": "stockanalysis"},
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    return body, {"Content-Type": "application/json"}


def _post_alert(url: str, body: bytes, headers: Mapping[str, str], timeout_seconds: float) -> AlertHttpResult:
    request = Request(url, data=body, headers=dict(headers), method="POST")
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - operator-owned URL from repo-outside env.
        return AlertHttpResult(
            status_code=int(response.status),
            response_header_count=len(response.headers),
        )


def _format_dt(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_token(value: object) -> str:
    text = str(value or "").strip().lower()
    return "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in text)[:64] or "unknown"


def _safe_target_host(url: str) -> str:
    if not url:
        return ""
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        return "unsupported_scheme"
    return parsed.hostname or ""
