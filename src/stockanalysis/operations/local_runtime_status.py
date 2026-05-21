from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from stockanalysis.operations.cadence import DATA_OPERATIONS_ARTIFACT_ROOT_ENV
from stockanalysis.operations.env_file import load_env_file_values
from stockanalysis.operations.env_readiness import DATABASE_URL_ENV, PSQL_COMMAND_ENV
from stockanalysis.operations.path_policy import resolve_repo_root


DEFAULT_LOCAL_RUNTIME_ROOT = Path("/private/tmp/stockanalysis-runtime")
DEFAULT_FRONTEND_API_URL = "http://127.0.0.1:8787"
DEFAULT_NEXT_COCKPIT_URL = "http://127.0.0.1:3001"

UrlProbe = Callable[[str, float], dict[str, object]]


def build_local_first_runtime_status_report(
    *,
    repo_root: str | Path | None = None,
    runtime_root: str | Path = DEFAULT_LOCAL_RUNTIME_ROOT,
    frontend_api_env_file: str | Path | None = None,
    data_operations_env_file: str | Path | None = None,
    frontend_api_url: str = DEFAULT_FRONTEND_API_URL,
    next_url: str = DEFAULT_NEXT_COCKPIT_URL,
    http_timeout_seconds: float = 2.0,
    skip_http_probes: bool = False,
    url_probe: UrlProbe | None = None,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    root = Path(runtime_root).expanduser().resolve()
    repo = resolve_repo_root(repo_root)
    frontend_env_path = Path(frontend_api_env_file).expanduser().resolve() if frontend_api_env_file else root / "frontend-api.env"
    data_env_path = (
        Path(data_operations_env_file).expanduser().resolve()
        if data_operations_env_file
        else root / "data-operations.env"
    )
    frontend_env = _env_file_summary(frontend_env_path, repo_root=repo, label="frontend_api_env_file")
    data_env = _env_file_summary(data_env_path, repo_root=repo, label="data_operations_env_file")
    merged_env_names = set(frontend_env["env_names"]) | set(data_env["env_names"])
    database_boundary = _database_boundary(merged_env_names)
    artifact_root_configured = DATA_OPERATIONS_ARTIFACT_ROOT_ENV in merged_env_names
    components = [
        {
            "component": "runtime_root",
            "status": "ok" if root.is_dir() else "missing",
            "path": str(root),
            "message": "local runtime root exists" if root.is_dir() else "local runtime root has not been created yet",
        },
        frontend_env,
        data_env,
        {
            "component": "database_boundary",
            "status": "ok" if database_boundary != "missing" else "missing",
            "boundary": database_boundary,
            "message": (
                "database boundary is configured"
                if database_boundary != "missing"
                else f"configure {DATABASE_URL_ENV} or {PSQL_COMMAND_ENV} in a repo-outside env file"
            ),
        },
        {
            "component": "artifact_root",
            "status": "ok" if artifact_root_configured else "missing",
            "env_name": DATA_OPERATIONS_ARTIFACT_ROOT_ENV,
            "message": (
                "artifact root env is configured"
                if artifact_root_configured
                else f"configure {DATA_OPERATIONS_ARTIFACT_ROOT_ENV} in data operations env"
            ),
        },
        _endpoint_component(
            component="frontend_api_live",
            url=_join_url(frontend_api_url, "/__live"),
            skip_http_probes=skip_http_probes,
            timeout_seconds=http_timeout_seconds,
            url_probe=url_probe,
        ),
        _endpoint_component(
            component="next_cockpit",
            url=_join_url(next_url, "/data-health"),
            skip_http_probes=skip_http_probes,
            timeout_seconds=http_timeout_seconds,
            url_probe=url_probe,
        ),
    ]
    overall_status = _overall_status(components)
    return {
        "report_name": "local_first_runtime_status",
        "generated_at": _format_timestamp(generated_at or datetime.now(timezone.utc)),
        "runtime_mode": "local_first",
        "overall_status": overall_status,
        "repo_root": str(repo),
        "runtime_root": str(root),
        "codex_host_mutation_allowed": False,
        "launchagents_install_allowed": False,
        "why_launchagents_blocked": [
            "LaunchAgents are persistent host mutations that keep running after this Codex session ends.",
            "They can execute commands with repo-outside env files and API credentials unattended.",
            "A wrong interval or command can repeatedly spend API quota or write bad data.",
            "Install, rollback, and disable commands require explicit human review before host mutation.",
            "The current local-first goal only needs manual operations worker runs and status visibility.",
        ],
        "components": components,
        "manual_commands": _manual_commands(root),
        "next_actions": _next_actions(components),
        "security": {
            "env_values_redacted": True,
            "env_value_policy": "env names and configured boundaries only; no secret values are emitted",
            "repo_inside_env_files_allowed": False,
        },
    }


def probe_http_url(url: str, timeout_seconds: float) -> dict[str, object]:
    request = Request(url, headers={"User-Agent": "stockanalysis-local-runtime-status/1"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            status_code = int(response.getcode())
            response.read(256)
    except HTTPError as exc:
        return {
            "ok": False,
            "status": "unreachable",
            "status_code": int(exc.code),
            "error": f"http_{exc.code}",
        }
    except URLError as exc:
        if isinstance(exc.reason, PermissionError):
            return {
                "ok": False,
                "status": "probe_blocked",
                "status_code": 0,
                "error": "local_network_permission_denied",
            }
        return {
            "ok": False,
            "status": "unreachable",
            "status_code": 0,
            "error": exc.reason.__class__.__name__,
        }
    except PermissionError:
        return {
            "ok": False,
            "status": "probe_blocked",
            "status_code": 0,
            "error": "local_network_permission_denied",
        }
    except TimeoutError:
        return {
            "ok": False,
            "status": "unreachable",
            "status_code": 0,
            "error": "timeout",
        }
    return {
        "ok": 200 <= status_code < 400,
        "status": "ok" if 200 <= status_code < 400 else "unreachable",
        "status_code": status_code,
        "error": "",
    }


def _env_file_summary(path: Path, *, repo_root: Path, label: str) -> dict[str, object]:
    repo_outside = not (path == repo_root or path.is_relative_to(repo_root))
    if not path.is_file():
        return {
            "component": label,
            "status": "missing",
            "path": str(path),
            "repo_outside": repo_outside,
            "env_names": [],
            "message": "env file does not exist",
        }
    if not repo_outside:
        return {
            "component": label,
            "status": "security_risk",
            "path": str(path),
            "repo_outside": False,
            "env_names": [],
            "message": "env file must be outside the repository",
        }
    try:
        values = load_env_file_values(path)
    except ValueError as exc:
        return {
            "component": label,
            "status": "invalid",
            "path": str(path),
            "repo_outside": True,
            "env_names": [],
            "message": str(exc),
        }
    return {
        "component": label,
        "status": "ok",
        "path": str(path),
        "repo_outside": True,
        "env_names": sorted(values),
        "message": "env file exists; values are redacted",
    }


def _database_boundary(env_names: set[str]) -> str:
    has_database_url = DATABASE_URL_ENV in env_names
    has_psql_command = PSQL_COMMAND_ENV in env_names
    if has_database_url and has_psql_command:
        return "database_url_and_legacy_psql_command"
    if has_database_url:
        return "database_url"
    if has_psql_command:
        return "legacy_psql_command"
    return "missing"


def _endpoint_component(
    *,
    component: str,
    url: str,
    skip_http_probes: bool,
    timeout_seconds: float,
    url_probe: UrlProbe | None,
) -> dict[str, object]:
    if skip_http_probes:
        return {
            "component": component,
            "status": "not_checked",
            "url": url,
            "message": "http probe skipped by request",
        }
    probe = url_probe or probe_http_url
    result = probe(url, timeout_seconds)
    status = str(result.get("status", "unreachable"))
    return {
        "component": component,
        "status": status,
        "url": url,
        "status_code": int(result.get("status_code", 0)),
        "message": _endpoint_message(status=status, ok=bool(result.get("ok")), error=str(result.get("error", ""))),
    }


def _overall_status(components: list[dict[str, object]]) -> str:
    statuses = {str(component["status"]) for component in components}
    if statuses & {"security_risk", "invalid"}:
        return "blocked"
    if statuses & {"missing", "unreachable"}:
        return "needs_attention"
    return "ready"


def _endpoint_message(*, status: str, ok: bool, error: str) -> str:
    if ok:
        return "endpoint reachable"
    if status == "probe_blocked":
        return "endpoint probe blocked by current sandbox; retry from the host shell"
    return f"endpoint unreachable: {error or 'unknown'}"


def _next_actions(components: list[dict[str, object]]) -> list[str]:
    actions: list[str] = []
    by_component = {str(component["component"]): component for component in components}
    if by_component["runtime_root"]["status"] == "missing":
        actions.append("create /private/tmp/stockanalysis-runtime or run the local bootstrap path")
    if by_component["frontend_api_env_file"]["status"] != "ok":
        actions.append("prepare repo-outside frontend-api.env")
    if by_component["data_operations_env_file"]["status"] != "ok":
        actions.append("prepare repo-outside data-operations.env")
    if by_component["database_boundary"]["status"] == "missing":
        actions.append("configure STOCKANALYSIS_DATABASE_URL or STOCKANALYSIS_PSQL_COMMAND")
    if by_component["artifact_root"]["status"] == "missing":
        actions.append(f"configure {DATA_OPERATIONS_ARTIFACT_ROOT_ENV}")
    if by_component["frontend_api_live"]["status"] == "unreachable":
        actions.append("start FastAPI read-only backend on 127.0.0.1:8787")
    if by_component["next_cockpit"]["status"] == "unreachable":
        actions.append("start Next.js cockpit on 127.0.0.1:3001")
    if not actions:
        actions.append("run manual market/news/AI ingest smoke through stockanalysis-operations")
    return actions


def _manual_commands(runtime_root: Path) -> list[dict[str, str]]:
    data_env = runtime_root / "data-operations.env"
    frontend_env = runtime_root / "frontend-api.env"
    return [
        {
            "name": "check local runtime status",
            "command": "stockanalysis-operations local-runtime-status",
        },
        {
            "name": "check data operations env readiness",
            "command": f"stockanalysis-operations env-readiness --env-file {data_env}",
        },
        {
            "name": "run market price daily manually",
            "command": f"stockanalysis-operations market-price-daily-run --env-file {data_env} --skip-if-fresh",
        },
        {
            "name": "run news RSS daily manually",
            "command": f"stockanalysis-operations news-rss-daily-run --env-file {data_env}",
        },
        {
            "name": "run Codex OAuth news AI evidence manually",
            "command": f"stockanalysis-operations news-rss-ai-extract-run --env-file {data_env} --provider codex_oauth --limit 10 --execute",
        },
        {
            "name": "start local FastAPI read-only backend",
            "command": f"PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/run_frontend_api_server.sh --env-file {frontend_env}",
        },
        {
            "name": "start local Next cockpit",
            "command": "cd apps/web && npm run dev -- --hostname 127.0.0.1 --port 3001",
        },
    ]


def _join_url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + path


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
