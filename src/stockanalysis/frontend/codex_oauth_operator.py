from __future__ import annotations

import json
import os
import re
import selectors
import shlex
import subprocess
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Sequence


STATUS_PATH_ENV = "STOCKANALYSIS_CODEX_OAUTH_STATUS_PATH"
CODEX_COMMAND_ENV = "STOCKANALYSIS_CODEX_CLI_COMMAND"
CODEX_WORKDIR_ENV = "STOCKANALYSIS_CODEX_WORKDIR"
CODEX_TIMEOUT_ENV = "STOCKANALYSIS_CODEX_TIMEOUT_SECONDS"
CODEX_SMOKE_ENV_FILE_ENV = "STOCKANALYSIS_CODEX_OAUTH_SMOKE_ENV_FILE"
DATA_OPERATIONS_ENV_FILE_ENV = "STOCKANALYSIS_DATA_OPERATIONS_ENV_FILE"
DEVICE_AUTH_START_TIMEOUT_ENV = "STOCKANALYSIS_CODEX_OAUTH_DEVICE_AUTH_START_TIMEOUT_SECONDS"
NEWS_SMOKE_LIMIT_ENV = "STOCKANALYSIS_CODEX_OAUTH_NEWS_SMOKE_LIMIT"
ORDER_BOUNDARY = "read_only_no_order"
AUTH_URL_PATTERN = re.compile(r"https://[^\s'\"]+", re.IGNORECASE)
USER_CODE_PATTERN = re.compile(r"\b[A-Z0-9]{4,}(?:-[A-Z0-9]{4,})+\b")
AUTH_FAILURE_PATTERNS = (
    "token_invalidated",
    "refresh_token_invalidated",
    "401 unauthorized",
    "unauthorized",
    "login required",
    "not logged in",
    "expired",
)


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


CommandRunner = Callable[[Sequence[str], str | None, int, Path], CommandResult]


def load_codex_oauth_operator_status(
    *,
    repo_root: Path | str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    status_path = _status_path(repo_root=repo_root)
    payload = _read_status_payload(status_path)
    return _public_status(payload, status_path=status_path, now=now or _utc_now())


def start_codex_oauth_device_login(
    *,
    repo_root: Path | str | None = None,
    popen_factory: Callable[..., subprocess.Popen[Any]] = subprocess.Popen,
    now: datetime | None = None,
) -> dict[str, Any]:
    current_now = now or _utc_now()
    status_path = _status_path(repo_root=repo_root)
    existing = _read_status_payload(status_path)
    existing_status = _public_status(existing, status_path=status_path, now=current_now)
    if existing_status["status"] == "device_auth_pending":
        return existing_status

    command = [*_codex_base_command(), "login", "--device-auth"]
    started_at = _iso(current_now)
    process = popen_factory(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(_workdir(repo_root=repo_root)),
        text=False,
    )
    output = _collect_process_output(process, timeout_seconds=_device_auth_start_timeout_seconds())
    combined_output = "\n".join(part for part in (output.get("stdout", ""), output.get("stderr", "")) if part)
    auth_url = _extract_auth_url(combined_output)
    user_code = _extract_user_code(combined_output)
    expires_at = _iso(current_now + timedelta(minutes=15))
    event: dict[str, Any] = {
        "event_type": "device_auth_started",
        "status": "device_auth_pending" if auth_url and user_code else "device_auth_output_unrecognized",
        "started_at": started_at,
        "pid": process.pid,
        "auth_url": auth_url,
        "user_code": user_code,
        "expires_at": expires_at if auth_url and user_code else "",
        "output_excerpt": _diagnostic_excerpt(combined_output, 2400),
        "command": _redacted_command(command),
    }
    if not auth_url or not user_code:
        _terminate_process(process)
        event["pid"] = None
        event["next_action"] = "Codex CLI device auth 출력에서 URL/code를 찾지 못했다. 서버에서 codex login --device-auth 출력을 확인한다."
    else:
        event["next_action"] = "auth URL을 열고 user code를 입력한 뒤 smoke를 실행한다."
    payload = _append_event(existing, event, now=current_now)
    _write_status_payload(status_path, payload)
    return _public_status(payload, status_path=status_path, now=current_now)


def run_codex_oauth_direct_smoke(
    *,
    repo_root: Path | str | None = None,
    runner: CommandRunner | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    current_now = now or _utc_now()
    status_path = _status_path(repo_root=repo_root)
    payload = _read_status_payload(status_path)
    prompt = (
        "Return exactly this JSON object and no markdown: "
        '{"status":"ok","provider":"codex_oauth","order_boundary":"read_only_no_order"}'
    )
    command = [
        *_codex_base_command(),
        "-c",
        'approval_policy="never"',
        "--sandbox",
        "read-only",
        "--cd",
        str(_workdir(repo_root=repo_root)),
        "exec",
        "--skip-git-repo-check",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "-",
    ]
    event = _run_smoke_command(
        event_type="direct_smoke",
        command=command,
        input_text=prompt,
        runner=runner,
        repo_root=repo_root,
        now=current_now,
    )
    payload = _append_event(payload, event, now=current_now)
    _write_status_payload(status_path, payload)
    return _public_status(payload, status_path=status_path, now=current_now)


def run_codex_oauth_news_smoke(
    *,
    repo_root: Path | str | None = None,
    runner: CommandRunner | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    current_now = now or _utc_now()
    status_path = _status_path(repo_root=repo_root)
    payload = _read_status_payload(status_path)
    env_file = os.environ.get(CODEX_SMOKE_ENV_FILE_ENV) or os.environ.get(DATA_OPERATIONS_ENV_FILE_ENV) or ""
    if not env_file:
        event = {
            "event_type": "news_smoke",
            "status": "blocked_missing_env_file",
            "started_at": _iso(current_now),
            "finished_at": _iso(current_now),
            "error_code": "missing_env_file",
            "message": f"{CODEX_SMOKE_ENV_FILE_ENV} 또는 {DATA_OPERATIONS_ENV_FILE_ENV}가 필요하다.",
            "next_action": "서버 runtime env에 data operations env file 경로를 설정한다.",
        }
        payload = _append_event(payload, event, now=current_now)
        _write_status_payload(status_path, payload)
        return _public_status(payload, status_path=status_path, now=current_now)

    limit = str(max(1, int(os.environ.get(NEWS_SMOKE_LIMIT_ENV, "1"))))
    commands = [
        [
            "stockanalysis-operations",
            "news-rss-translation-run",
            "--env-file",
            env_file,
            "--provider",
            "codex_oauth",
            "--limit",
            limit,
            "--execute",
        ],
        [
            "stockanalysis-operations",
            "news-rss-ai-extract-run",
            "--env-file",
            env_file,
            "--provider",
            "codex_oauth",
            "--limit",
            limit,
            "--execute",
        ],
    ]
    step_events = [
        _run_smoke_command(
            event_type="news_smoke_step",
            command=command,
            input_text=None,
            runner=runner,
            repo_root=repo_root,
            now=current_now,
        )
        for command in commands
    ]
    failed = [event for event in step_events if event["status"] != "succeeded"]
    event = {
        "event_type": "news_smoke",
        "status": "succeeded" if not failed else "failed_auth_invalid" if _has_auth_failure(failed) else "failed",
        "started_at": step_events[0]["started_at"] if step_events else _iso(current_now),
        "finished_at": _iso(current_now),
        "step_events": step_events,
        "error_code": failed[0].get("error_code", "") if failed else "",
        "message": failed[0].get("message", "뉴스 번역/구조화 Codex OAuth smoke가 성공했다.") if failed else "뉴스 번역/구조화 Codex OAuth smoke가 성공했다.",
        "next_action": "성공한 smoke를 확인했다." if not failed else "Codex OAuth 재로그인 또는 CLI 오류 확인이 필요하다.",
    }
    payload = _append_event(payload, event, now=current_now)
    _write_status_payload(status_path, payload)
    return _public_status(payload, status_path=status_path, now=current_now)


def _run_smoke_command(
    *,
    event_type: str,
    command: Sequence[str],
    input_text: str | None,
    runner: CommandRunner | None,
    repo_root: Path | str | None,
    now: datetime,
) -> dict[str, Any]:
    started_at = _iso(now)
    timeout_seconds = _timeout_seconds()
    selected_runner = runner or _subprocess_runner
    try:
        result = selected_runner(command, input_text, timeout_seconds, _workdir(repo_root=repo_root))
    except subprocess.TimeoutExpired as exc:
        message = f"Codex OAuth smoke timed out after {timeout_seconds}s."
        return {
            "event_type": event_type,
            "status": "failed",
            "started_at": started_at,
            "finished_at": _iso(_utc_now()),
            "returncode": None,
            "error_code": "timeout",
            "message": message,
            "stdout_excerpt": _diagnostic_excerpt(str(getattr(exc, "stdout", "") or ""), 1200),
            "stderr_excerpt": _diagnostic_excerpt(str(getattr(exc, "stderr", "") or ""), 1200),
            "command": _redacted_command(command),
        }
    except Exception as exc:
        return {
            "event_type": event_type,
            "status": "failed",
            "started_at": started_at,
            "finished_at": _iso(_utc_now()),
            "returncode": None,
            "error_code": "command_error",
            "message": _diagnostic_excerpt(str(exc), 800),
            "command": _redacted_command(command),
        }

    diagnostic = "\n".join(part for part in (result.stderr, result.stdout) if part)
    auth_failure = _is_auth_failure(diagnostic)
    succeeded = result.returncode == 0
    return {
        "event_type": event_type,
        "status": "succeeded" if succeeded else "failed_auth_invalid" if auth_failure else "failed",
        "started_at": started_at,
        "finished_at": _iso(_utc_now()),
        "returncode": result.returncode,
        "error_code": "" if succeeded else "codex_oauth_auth_invalid" if auth_failure else "codex_oauth_smoke_failed",
        "message": "Codex OAuth smoke succeeded." if succeeded else _diagnostic_excerpt(diagnostic, 1200),
        "stdout_excerpt": _diagnostic_excerpt(result.stdout, 1200),
        "stderr_excerpt": _diagnostic_excerpt(result.stderr, 1200),
        "command": _redacted_command(command),
    }


def _subprocess_runner(command: Sequence[str], input_text: str | None, timeout_seconds: int, cwd: Path) -> CommandResult:
    completed = subprocess.run(
        list(command),
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
        cwd=str(cwd),
    )
    return CommandResult(
        returncode=int(completed.returncode),
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
    )


def _public_status(payload: dict[str, Any], *, status_path: Path, now: datetime) -> dict[str, Any]:
    events = [event for event in payload.get("events", []) if isinstance(event, dict)]
    latest_event = events[-1] if events else {}
    latest_smoke = next((event for event in reversed(events) if str(event.get("event_type", "")).endswith("smoke")), {})
    latest_device = next((event for event in reversed(events) if event.get("event_type") == "device_auth_started"), {})
    status = "unknown"
    if latest_event:
        status = _status_from_event(latest_event, now=now)
    if latest_smoke and latest_smoke.get("status") == "succeeded":
        status = "healthy"
    elif _status_from_event(latest_event, now=now) == "relogin_required":
        status = "relogin_required"
    elif _status_from_event(latest_event, now=now) in {"device_auth_pending", "device_code_expired"}:
        status = _status_from_event(latest_event, now=now)

    return {
        "status": status,
        "label": _status_label(status),
        "summary": _status_summary(status),
        "auth_url": str(latest_device.get("auth_url") or "") if status in {"device_auth_pending", "device_code_expired"} else "",
        "user_code": str(latest_device.get("user_code") or "") if status in {"device_auth_pending", "device_code_expired"} else "",
        "expires_at": str(latest_device.get("expires_at") or "") if status in {"device_auth_pending", "device_code_expired"} else "",
        "device_auth_pid": latest_device.get("pid") if status == "device_auth_pending" else None,
        "last_checked_at": str(payload.get("updated_at") or ""),
        "last_event_type": str(latest_event.get("event_type") or ""),
        "last_smoke_status": str(latest_smoke.get("status") or ""),
        "last_smoke_at": str(latest_smoke.get("finished_at") or latest_smoke.get("started_at") or ""),
        "last_error_code": str(latest_event.get("error_code") or ""),
        "last_error_summary": _diagnostic_excerpt(str(latest_event.get("message") or latest_event.get("output_excerpt") or ""), 800),
        "next_action": str(latest_event.get("next_action") or _next_action_for_status(status)),
        "status_path": str(status_path),
        "admin_action_required": True,
        "read_only": True,
        "broker_submit_allowed": False,
        "automatic_order_allowed": False,
        "order_boundary": ORDER_BOUNDARY,
    }


def _status_from_event(event: dict[str, Any], *, now: datetime) -> str:
    raw_status = str(event.get("status") or "")
    if raw_status == "succeeded":
        return "healthy"
    if raw_status == "device_auth_pending":
        expires_at = _parse_datetime(str(event.get("expires_at") or ""))
        if expires_at and expires_at <= now:
            return "device_code_expired"
        return "device_auth_pending"
    if raw_status in {"failed_auth_invalid", "device_auth_output_unrecognized"}:
        return "relogin_required"
    if raw_status in {"blocked_missing_env_file", "failed"}:
        return "failed"
    return "unknown"


def _status_label(status: str) -> str:
    labels = {
        "healthy": "정상",
        "device_auth_pending": "로그인 대기",
        "device_code_expired": "코드 만료",
        "relogin_required": "재로그인 필요",
        "failed": "실행 실패",
        "unknown": "미확인",
    }
    return labels.get(status, status)


def _status_summary(status: str) -> str:
    summaries = {
        "healthy": "최근 Codex OAuth smoke가 성공했다.",
        "device_auth_pending": "재로그인 device code가 발급됐다. auth URL에서 code를 입력한 뒤 smoke를 실행한다.",
        "device_code_expired": "발급된 device code가 만료됐다. 재로그인 시작을 다시 눌러 새 code를 받는다.",
        "relogin_required": "Codex OAuth 인증이 만료되었거나 로그인 출력 확인이 필요하다.",
        "failed": "Codex OAuth 작업 실행이 실패했다. 오류와 서버 환경을 확인한다.",
        "unknown": "아직 Codex OAuth 상태를 확인한 기록이 없다.",
    }
    return summaries.get(status, "Codex OAuth 상태를 확인한다.")


def _next_action_for_status(status: str) -> str:
    if status == "healthy":
        return "필요 시 뉴스 번역/구조화 smoke를 재실행해 운영 배치를 확인한다."
    if status == "device_auth_pending":
        return "auth URL을 열고 user code를 입력한 뒤 smoke를 실행한다."
    return "재로그인 시작을 누르고 device code 발급 여부를 확인한다."


def _append_event(payload: dict[str, Any], event: dict[str, Any], *, now: datetime) -> dict[str, Any]:
    events = [item for item in payload.get("events", []) if isinstance(item, dict)]
    events.append(event)
    return {
        "report_name": "codex_oauth_operator_status",
        "updated_at": _iso(now),
        "events": events[-25:],
    }


def _read_status_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_status_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def _status_path(*, repo_root: Path | str | None) -> Path:
    configured = os.environ.get(STATUS_PATH_ENV)
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(tempfile.gettempdir(), "stockanalysis-runtime", "codex-oauth-status.json").resolve()


def _workdir(*, repo_root: Path | str | None) -> Path:
    configured = os.environ.get(CODEX_WORKDIR_ENV)
    if configured:
        return Path(configured).expanduser().resolve()
    if repo_root is not None:
        return Path(repo_root).expanduser().resolve()
    return Path.cwd().resolve()


def _codex_base_command() -> list[str]:
    command_text = os.environ.get(CODEX_COMMAND_ENV, "codex").strip() or "codex"
    base_command = shlex.split(command_text)
    if not base_command:
        raise ValueError(f"{CODEX_COMMAND_ENV} must not be empty.")
    return base_command


def _timeout_seconds() -> int:
    return max(1, int(os.environ.get(CODEX_TIMEOUT_ENV, "300")))


def _device_auth_start_timeout_seconds() -> int:
    return max(3, int(os.environ.get(DEVICE_AUTH_START_TIMEOUT_ENV, "15")))


def _collect_process_output(process: subprocess.Popen[Any], *, timeout_seconds: int) -> dict[str, str]:
    selector = selectors.DefaultSelector()
    streams: list[tuple[str, Any]] = []
    if process.stdout is not None:
        streams.append(("stdout", process.stdout))
    if process.stderr is not None:
        streams.append(("stderr", process.stderr))
    for _, stream in streams:
        selector.register(stream, selectors.EVENT_READ)
    deadline = time.monotonic() + timeout_seconds
    chunks = {"stdout": [], "stderr": []}
    while time.monotonic() < deadline and selector.get_map():
        events = selector.select(timeout=0.25)
        if not events:
            if process.poll() is not None:
                break
            continue
        for key, _ in events:
            name = "stdout" if key.fileobj is process.stdout else "stderr"
            data = key.fileobj.read1(4096) if hasattr(key.fileobj, "read1") else key.fileobj.read(4096)
            if not data:
                try:
                    selector.unregister(key.fileobj)
                except Exception:
                    pass
                continue
            chunks[name].append(data.decode("utf-8", errors="replace") if isinstance(data, bytes) else str(data))
            combined = "\n".join(chunks["stdout"] + chunks["stderr"])
            if _extract_auth_url(combined) and _extract_user_code(combined):
                return {"stdout": "".join(chunks["stdout"]), "stderr": "".join(chunks["stderr"])}
    return {"stdout": "".join(chunks["stdout"]), "stderr": "".join(chunks["stderr"])}


def _terminate_process(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None:
        return
    try:
        process.terminate()
        process.wait(timeout=2)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass


def _extract_auth_url(text: str) -> str:
    for match in AUTH_URL_PATTERN.findall(text):
        if "device" in match.lower() or "openai" in match.lower():
            return match.rstrip(").,")
    return ""


def _extract_user_code(text: str) -> str:
    match = USER_CODE_PATTERN.search(text.upper())
    return match.group(0) if match else ""


def _is_auth_failure(text: str) -> bool:
    normalized = text.lower()
    return any(pattern in normalized for pattern in AUTH_FAILURE_PATTERNS)


def _has_auth_failure(events: list[dict[str, Any]]) -> bool:
    return any(event.get("status") == "failed_auth_invalid" or event.get("error_code") == "codex_oauth_auth_invalid" for event in events)


def _diagnostic_excerpt(text: str, limit: int) -> str:
    compact = re.sub(r"\s+", " ", (text or "").strip())
    if len(compact) <= limit:
        return compact
    return compact[: max(0, limit - 1)] + "…"


def _redacted_command(command: Sequence[str]) -> list[str]:
    redacted: list[str] = []
    skip_next = False
    for item in command:
        if skip_next:
            redacted.append("<redacted>")
            skip_next = False
            continue
        redacted.append(item)
        if item in {"--env-file"}:
            skip_next = True
    return redacted


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
