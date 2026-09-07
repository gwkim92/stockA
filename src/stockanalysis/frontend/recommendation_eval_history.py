"""Stored evaluation history only: never reconstruct history from mutable sources."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.psql import PsqlCommandExecutor

API_PATH = "/api/recommendation-evaluations"
CONTRACT_VERSION = "recommendation-eval-history-v1"
EVAL_NAME = "recommendation_quality_calibration"
MAX_ID = 9223372036854775807
_ID = re.compile(r"[1-9][0-9]{0,18}\Z", re.ASCII)


class EvaluationHistoryError(RuntimeError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class HistoryRequest:
    eval_run_id: int | None = None
    limit: int = 25
    cursor: int | None = None


def is_evaluation_history_path(api_path: str) -> bool:
    path = urlsplit(api_path).path
    return path == API_PATH or path.startswith(API_PATH + "/")


def _invalid() -> EvaluationHistoryError:
    return EvaluationHistoryError("Invalid evaluation history selector or pagination.", code="FrontendPaginationInvalid")


def _positive_id(value: object) -> int:
    if not isinstance(value, str) or _ID.fullmatch(value) is None:
        raise _invalid()
    result = int(value)
    if result > MAX_ID:
        raise _invalid()
    return result


def parse_evaluation_history_request(api_path: str) -> HistoryRequest:
    try:
        parsed = urlsplit(api_path)
        if parsed.scheme or parsed.netloc or parsed.fragment:
            raise _invalid()
        if parsed.path == API_PATH:
            run_id = None
            direction = "before"
        else:
            prefix = API_PATH + "/eval-run-"
            if not parsed.path.startswith(prefix):
                raise _invalid()
            run_id = _positive_id(parsed.path[len(prefix):])
            direction = "after"
        pairs = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True, errors="strict", max_num_fields=2)
        values: dict[str, str] = {}
        for key, value in pairs:
            if key not in {"limit", direction} or key in values:
                raise _invalid()
            values[key] = value
        limit = _positive_id(values["limit"]) if "limit" in values else 25
        if limit > 100:
            raise _invalid()
        cursor = _positive_id(values[direction]) if direction in values else None
        return HistoryRequest(run_id, limit, cursor)
    except (ValueError, UnicodeError) as exc:
        raise _invalid() from exc


SCHEMA_READINESS_SQL = """select (
    pg_catalog.to_regclass('ai.eval_run') is not null
    and pg_catalog.to_regclass('ai.recommendation_eval_snapshot') is not null
    and (select count(*) from pg_catalog.pg_attribute
         where attrelid = pg_catalog.to_regclass('ai.eval_run')
           and attname in ('pipeline_run_id', 'as_of_date', 'horizon_days', 'config_json')
           and not attisdropped) = 4
)::text;"""

_RUN_JSON = """json_build_object(
    'eval_run_id', e.eval_run_id::text,
    'eval_name', e.eval_name,
    'dataset_version', e.dataset_version,
    'provider', e.provider,
    'model_name', e.model_name,
    'created_at', e.created_at,
    'pipeline_run_id', e.pipeline_run_id::text,
    'as_of_date', e.as_of_date,
    'horizon_days', e.horizon_days,
    'stored_score', e.score_json,
    'stored_config', e.config_json,
    'snapshot_count', (select count(*) from ai.recommendation_eval_snapshot s where s.eval_run_id = e.eval_run_id)
)"""

_SNAPSHOT_JSON = """json_build_object(
    'snapshot_id', s.snapshot_id::text,
    'eval_run_id', s.eval_run_id::text,
    'snapshot_schema_version', s.snapshot_schema_version,
    'source_recommendation_id', s.source_recommendation_id::text,
    'source_batch_id', s.source_batch_id::text,
    'source_thesis_id', s.source_thesis_id::text,
    'source_outcome_id', s.source_outcome_id::text,
    'primary_symbol', s.primary_symbol,
    'recommendation_action', s.recommendation_action,
    'recommendation_total_score', s.recommendation_total_score,
    'selected_outcome_alpha_pct', s.selected_outcome_alpha_pct,
    'snapshot_sha256', s.snapshot_sha256,
    'snapshot_json', s.snapshot_json,
    'created_at', s.created_at
)"""


def render_evaluation_history_sql(request: HistoryRequest) -> str:
    # Validate even direct/internal callers; no caller-supplied SQL fragments.
    if type(request.limit) is not int or not 1 <= request.limit <= 100:
        raise _invalid()
    for identifier in (request.eval_run_id, request.cursor):
        if identifier is not None and (type(identifier) is not int or not 1 <= identifier <= MAX_ID):
            raise _invalid()
    if request.eval_run_id is None:
        cursor_sql = f"and e.eval_run_id < {request.cursor}" if request.cursor is not None else ""
        return f"""with page as (
    select e.* from ai.eval_run e
    where e.eval_name = '{EVAL_NAME}' {cursor_sql}
    order by e.eval_run_id desc limit {request.limit + 1}
)
select json_build_object('runs', coalesce((
    select json_agg({_RUN_JSON} order by e.eval_run_id desc) from page e
), '[]'::json))::text;"""
    cursor_sql = f"and s.snapshot_id > {request.cursor}" if request.cursor is not None else ""
    return f"""with selected_run as (
    select e.* from ai.eval_run e
    where e.eval_name = '{EVAL_NAME}' and e.eval_run_id = {request.eval_run_id}
), page as (
    select s.* from ai.recommendation_eval_snapshot s
    join selected_run e on e.eval_run_id = s.eval_run_id
    where true {cursor_sql}
    order by s.snapshot_id asc limit {request.limit + 1}
)
select json_build_object(
    'run', (select {_RUN_JSON} from selected_run e),
    'snapshots', coalesce((select json_agg({_SNAPSHOT_JSON} order by s.snapshot_id asc) from page s), '[]'::json)
)::text;"""


def _unavailable() -> EvaluationHistoryError:
    return EvaluationHistoryError("Stored evaluation history is unavailable; no history was reconstructed.", code="FrontendLiveReadUnavailable")


def _run_metadata(raw: object) -> dict[str, Any]:
    if not isinstance(raw, dict) or raw.get("eval_name") != EVAL_NAME:
        raise _unavailable()
    run = dict(raw)
    _positive_id(run.get("eval_run_id"))
    pipeline_id = run.get("pipeline_run_id")
    if pipeline_id is not None:
        _positive_id(pipeline_id)
    count = run.get("snapshot_count")
    if type(count) is not int or count < 0:
        raise _unavailable()
    config = run.get("stored_config")
    expected = config.get("snapshot_count") if isinstance(config, dict) else None
    version = config.get("snapshot_schema_version") if isinstance(config, dict) else None
    if expected is None and not version and count == 0:
        state = "legacy_unavailable"
    elif type(expected) is not int or expected < 0 or not isinstance(version, str) or not version or expected != count:
        state = "count_mismatch"
    else:
        state = "recorded_empty" if count == 0 else "recorded"
    run.update(snapshot_state=state, expected_snapshot_count=expected, snapshot_schema_version=version)
    return run


def _page(rows: object, request: HistoryRequest, *, key: str, descending: bool) -> tuple[list[dict[str, Any]], str | None]:
    if not isinstance(rows, list) or len(rows) > request.limit + 1:
        raise _unavailable()
    ids: list[int] = []
    for row in rows:
        if not isinstance(row, dict):
            raise _unavailable()
        identifier = _positive_id(row.get(key))
        if request.cursor is not None and (identifier >= request.cursor if descending else identifier <= request.cursor):
            raise _unavailable()
        ids.append(identifier)
    if ids != sorted(set(ids), reverse=descending):
        raise _unavailable()
    returned = rows[:request.limit]
    cursor = returned[-1][key] if len(rows) > request.limit else None
    return returned, cursor


def resolve_evaluation_history(
    api_path: str,
    *,
    source: str,
    config: RuntimeConfig | None = None,
    executor: Any | None = None,
) -> dict[str, Any]:
    request = parse_evaluation_history_request(api_path)
    if source not in {"live", "auto"}:
        raise _unavailable()
    try:
        if executor is None:
            runtime = config or RuntimeConfig.from_env()
            if not runtime.psql_command:
                raise _unavailable()
            executor = PsqlCommandExecutor.from_config(runtime)
        ready = executor.execute_scalar(SCHEMA_READINESS_SQL)
        if str(ready).strip().lower() not in {"true", "t"}:
            raise _unavailable()
        raw = json.loads(executor.execute_scalar(render_evaluation_history_sql(request)))
        if not isinstance(raw, dict):
            raise _unavailable()
        result: dict[str, Any] = {
            "contract_version": CONTRACT_VERSION,
            "source": "live",
            "read_only": True,
            "order_boundary": "read_only_no_order",
            "broker_submit_allowed": False,
            "history_basis": "evaluation_time_snapshot_not_recommendation_creation_time",
            "snapshot_hash_verification": "not_performed",
        }
        if request.eval_run_id is None:
            rows, cursor = _page(raw.get("runs"), request, key="eval_run_id", descending=True)
            result["runs"] = [_run_metadata(row) for row in rows]
            direction = "before"
        else:
            if raw.get("run") is None:
                raise EvaluationHistoryError("The requested recommendation evaluation was not found.", code="FrontendApiPathNotFound")
            run = _run_metadata(raw["run"])
            if run["eval_run_id"] != str(request.eval_run_id):
                raise _unavailable()
            rows, cursor = _page(raw.get("snapshots"), request, key="snapshot_id", descending=False)
            for row in rows:
                if row.get("eval_run_id") != run["eval_run_id"]:
                    raise _unavailable()
                for key in ("source_recommendation_id", "source_batch_id"):
                    _positive_id(row.get(key))
                for key in ("source_thesis_id", "source_outcome_id"):
                    if row.get(key) is not None:
                        _positive_id(row[key])
            result.update(run=run, snapshots=rows)
            direction = "after"
        result["pagination"] = {
            "limit": request.limit,
            "returned_count": len(rows),
            "has_more": cursor is not None,
            "next_cursor": cursor,
            "cursor_parameter": direction,
            "scope": "returned_page_only",
        }
        return result
    except EvaluationHistoryError as exc:
        if exc.code == "FrontendPaginationInvalid":
            # A malformed stored response is a server/source problem, not a bad request.
            raise _unavailable() from exc
        raise
    except Exception as exc:
        # Never echo connection strings, SQL, driver errors or source payloads.
        raise _unavailable() from exc
