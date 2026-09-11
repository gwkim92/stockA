"""Read stored recommendation measurements independently of portfolio attribution."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit

from stockanalysis.frontend.recommendation_eval_history import EVAL_NAME, EvaluationHistoryError, MAX_ID
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.performance.outcome_window import outcome_window_match_sql

API_PATH = "/api/recommendation-outcomes"
VERSION = "recommendation-outcome-explorer-v1"
HORIZONS = (30, 90, 180, 365)


def invalid():
    return EvaluationHistoryError("Invalid recommendation outcome filters or cursor.", code="FrontendPaginationInvalid")


def unavailable():
    return EvaluationHistoryError("Stored recommendation outcomes are unavailable.", code="FrontendLiveReadUnavailable")


@dataclass(frozen=True)
class OutcomeRequest:
    symbol: str = ""
    from_date: str = ""
    to_date: str = ""
    horizon: str = ""
    benchmark: str = ""
    alpha: str = ""
    before: str = ""
    through: str = ""
    limit: int = 25

    def filters(self):
        return {k: v for k, v in asdict(self).items() if k not in {"before", "through", "limit"}}


def valid_date(value: str):
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise invalid()
    date.fromisoformat(value)


def valid_id(value: str, *, zero=False):
    if not re.fullmatch(r"0|[1-9][0-9]{0,18}" if zero else r"[1-9][0-9]{0,18}", value) or int(value) > MAX_ID:
        raise invalid()


def parse_outcome_request(path: str) -> OutcomeRequest:
    try:
        if any(ord(c) <= 32 or ord(c) == 127 for c in path):
            raise invalid()
        parsed = urlsplit(path)
        if parsed.path != API_PATH or parsed.scheme or parsed.netloc or parsed.fragment:
            raise invalid()
        values = {}
        for k, v in parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True, errors="strict", max_num_fields=9):
            if k not in OutcomeRequest.__dataclass_fields__ or k in values:
                raise invalid()
            values[k] = v
        symbol = values.get("symbol", "").upper()
        if symbol and not re.fullmatch(r"[A-Z0-9][A-Z0-9._-]{0,19}", symbol):
            raise invalid()
        values["symbol"] = symbol
        for key in ("from_date", "to_date"):
            if values.get(key):
                valid_date(values[key])
        if values.get("from_date") and values.get("to_date") and values["from_date"] > values["to_date"]:
            raise invalid()
        if values.get("horizon", "") not in {"", "other", *(str(h) for h in HORIZONS)}:
            raise invalid()
        if values.get("alpha", "") not in {"", "positive", "negative", "zero", "missing"}:
            raise invalid()
        benchmark = values.get("benchmark", "")
        if benchmark and not re.fullmatch(r"[A-Za-z0-9_^][A-Za-z0-9 ^&._/-]{0,63}", benchmark):
            raise invalid()
        if values.get("before"):
            day, identifier = values["before"].split(":")
            valid_date(day); valid_id(identifier)
        if values.get("through"):
            valid_id(values["through"], zero=True)
        if "limit" in values:
            valid_id(values["limit"])
            values["limit"] = int(values["limit"])
            if values["limit"] > 100:
                raise invalid()
        return OutcomeRequest(**values)
    except (ValueError, UnicodeError) as exc:
        raise invalid() from exc


def render_recommendation_outcomes_sql(request: OutcomeRequest) -> str:
    request = parse_outcome_request(API_PATH + "?" + urlencode(asdict(request)))
    conditions = []
    if request.symbol:
        conditions.append(f"upper(symbol) = {sql_literal(request.symbol)}")
    if request.from_date:
        conditions.append(f"recommendation_date >= {sql_literal(request.from_date)}::date")
    if request.to_date:
        conditions.append(f"recommendation_date <= {sql_literal(request.to_date)}::date")
    if request.horizon:
        conditions.append("nominal_horizon is null" if request.horizon == "other" else f"nominal_horizon = {int(request.horizon)}")
    if request.benchmark:
        conditions.append("benchmark_code is null" if request.benchmark == "_missing" else f"upper(benchmark_code) = upper({sql_literal(request.benchmark)})")
    if request.alpha:
        conditions.append({"positive": "alpha_pct > 0", "negative": "alpha_pct < 0", "zero": "alpha_pct = 0", "missing": "alpha_pct is null"}[request.alpha])
    where = " and ".join(conditions) or "true"
    ceiling = request.through or "coalesce((select max(outcome_id) from performance.recommendation_outcome), 0)"
    cursor = "true"
    if request.before:
        day, identifier = request.before.split(":")
        cursor = f"(measurement_end_date, outcome_id) < ({sql_literal(day)}::date, {int(identifier)}::bigint)"
    horizon_case = "case " + " ".join(
        "when " + outcome_window_match_sql(recommendation_id="r.recommendation_id", recommendation_date="b.as_of_date",
            horizon_days=str(h), end_date="o.measurement_end_date", alias="o") + f" then {h}"
        for h in HORIZONS) + " end"
    return f"""with ceiling as (select {ceiling}::bigint as id), population as (
    select o.*, b.as_of_date as recommendation_date, b.strategy_name, b.market_code,
        r.action as recommendation_action, r.total_score as recommendation_score,
        r.thesis_id, i.primary_symbol as symbol, i.currency_code, {horizon_case} as nominal_horizon
    from performance.recommendation_outcome o
    join signal.recommendation r using (recommendation_id)
    join signal.recommendation_batch b using (batch_id)
    join ref.instrument i using (instrument_id)
    where o.outcome_id <= (select id from ceiling)
), filtered as (select * from population where {where}), page as (
    select * from filtered where {cursor}
    order by measurement_end_date desc, outcome_id desc limit {request.limit + 1}
), page_rows as (
    select p.*, saved.snapshot
    from page p
    left join lateral (
        select json_build_object('eval_run_id',s.eval_run_id::text,'snapshot_id',s.snapshot_id::text,
            'as_of_date',e.as_of_date,'recorded_at',s.created_at) as snapshot
        from ai.recommendation_eval_snapshot s join ai.eval_run e using (eval_run_id)
        where s.source_outcome_id = p.outcome_id and s.source_recommendation_id = p.recommendation_id
            and e.eval_name = {sql_literal(EVAL_NAME)}
        order by s.created_at desc, s.snapshot_id desc limit 1
    ) saved on true
)
select json_build_object(
    'through', (select id::text from ceiling),
    'summary', (select json_build_object('measurement_count',count(*),'recommendation_count',count(distinct recommendation_id),
        'symbol_count',count(distinct symbol),'missing_alpha_count',count(*) filter(where alpha_pct is null),
        'first_recommendation_date',min(recommendation_date),'last_recommendation_date',max(recommendation_date)) from filtered),
    'benchmarks', coalesce((select json_agg(benchmark_code order by benchmark_code nulls last)
        from (select distinct benchmark_code from population) b),'[]'::json),
    'rows', coalesce((select json_agg(json_build_object(
        'outcome_id',outcome_id::text,'recommendation_id',recommendation_id::text,'thesis_id',thesis_id::text,
        'symbol',symbol,'currency_code',currency_code,'strategy_name',strategy_name,'market_code',market_code,
        'recommendation_date',recommendation_date,'recommendation_action',recommendation_action,'recommendation_score',recommendation_score,
        'measurement_start_date',measurement_start_date,'measurement_end_date',measurement_end_date,
        'horizon_days',horizon_days,'nominal_horizon',nominal_horizon,
        'entry_price',entry_price,'exit_price',exit_price,'absolute_return_pct',absolute_return_pct,
        'benchmark_code',benchmark_code,'benchmark_return_pct',benchmark_return_pct,'alpha_pct',alpha_pct,
        'max_drawdown_pct',max_drawdown_pct,'outcome_label',outcome_label,'recorded_at',created_at,
        'source_run_id',source_run_id::text,'evaluation_snapshot',snapshot
    ) order by measurement_end_date desc,outcome_id desc) from page_rows),'[]'::json)
)::text;"""


def resolve_recommendation_outcomes(path: str, *, source: str, config=None, executor=None):
    request = parse_outcome_request(path)
    if source not in {"live", "auto"}:
        raise unavailable()
    try:
        if executor is None:
            executor = PsqlCommandExecutor.from_config(config or RuntimeConfig.from_env())
        raw = json.loads(executor.execute_scalar(render_recommendation_outcomes_sql(request)))
        valid_id(raw["through"], zero=True)
        rows = raw["rows"]
        if not isinstance(rows, list) or len(rows) > request.limit + 1:
            raise unavailable()
        keys = []
        for row in rows:
            valid_id(row["outcome_id"]); valid_id(row["recommendation_id"])
            valid_date(row["measurement_end_date"])
            keys.append((row["measurement_end_date"], int(row["outcome_id"])))
            if int(row["outcome_id"]) > int(raw["through"]):
                raise unavailable()
        if keys != sorted(set(keys), reverse=True):
            raise unavailable()
        if request.before:
            day, identifier = request.before.split(":")
            if any(key >= (day, int(identifier)) for key in keys):
                raise unavailable()
        summary = raw["summary"]
        for field in ("measurement_count", "recommendation_count", "symbol_count", "missing_alpha_count"):
            if type(summary[field]) is not int or summary[field] < 0:
                raise unavailable()
        if summary["measurement_count"] < len(rows):
            raise unavailable()
        shown = rows[:request.limit]
        next_cursor = f"{shown[-1]['measurement_end_date']}:{shown[-1]['outcome_id']}" if len(rows) > request.limit else None
        return {"contract_version": VERSION, "source": "live", "read_only": True,
                "generated_at": datetime.now(timezone.utc).isoformat(), "filters": request.filters(),
                "summary": summary, "benchmarks": raw["benchmarks"], "rows": shown,
                "pagination": {"limit": request.limit, "returned_count": len(shown), "through": raw["through"],
                               "has_more": next_cursor is not None, "next_cursor": next_cursor},
                "record_basis": "stored_measurements_with_current_recommendation_links",
                "horizon_tolerance_days": 7}
    except Exception as exc:
        # Do not turn failed reads into zero outcomes, or expose SQL/credentials.
        raise unavailable() from exc
