from __future__ import annotations

import json
from datetime import date
from typing import Any

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations.recommendation_outcome_backfill import (
    DEFAULT_OUTCOME_VERSION,
    run_recommendation_outcome_backfill,
)
from stockanalysis.operations.recommendation_quality_eval import (
    DEFAULT_MIN_PROFESSIONAL_COVERAGE_RATE,
    DEFAULT_MIN_SAMPLE_SIZE,
    POSITIVE_OUTCOME_LABELS,
    PROTECTED_CYCLE_STACK_COMPONENTS,
    PROTECTED_FUNDAMENTAL_COMPONENTS,
    run_recommendation_quality_eval,
)
from stockanalysis.performance.outcome import resolve_performance_schedule_horizon_days
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_REPORT_NAME = "recommendation_outcome_calibration_sample_expansion"
DEFAULT_PIPELINE_NAME = "recommendation_outcome_calibration_sample_expansion"
DEFAULT_EVAL_NAME = "recommendation_outcome_calibration_sample_expansion"
DEFAULT_DATASET_VERSION = "recommendation-outcome-calibration-sample-expansion-v1"
DEFAULT_PROVIDER = "postgres"
DEFAULT_MODEL_NAME = "deterministic-outcome-calibration-v1"
DEFAULT_EXAMPLE_LIMIT = 10


def render_recommendation_outcome_sample_audit_sql(
    *,
    as_of_date: date,
    horizon_days: tuple[int, ...],
    market_code: str | None = None,
    strategy_name: str | None = None,
    horizon_type: str | None = None,
    universe_version: str | None = None,
    example_limit: int = DEFAULT_EXAMPLE_LIMIT,
) -> str:
    resolved_horizon_days = resolve_performance_schedule_horizon_days(horizon_days)
    if example_limit < 0 or example_limit > 100:
        raise ValueError("example_limit must be between 0 and 100.")
    horizon_rows = ",\n        ".join(f"({horizon_day}::integer)" for horizon_day in resolved_horizon_days)
    positive_labels = ", ".join(sql_literal(label) for label in POSITIVE_OUTCOME_LABELS)
    protected_components = ", ".join(
        sql_literal(name) for name in (*PROTECTED_CYCLE_STACK_COMPONENTS, *PROTECTED_FUNDAMENTAL_COMPONENTS)
    )
    filter_conditions = _render_batch_filters(
        market_code=market_code,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        universe_version=universe_version,
    )
    return f"""-- recommendation outcome calibration sample audit lookup
with target_date as (
    select {sql_date(as_of_date)}::date as as_of_date
),
horizon_days(horizon_day) as (
    values
        {horizon_rows}
),
recommendation_window as (
    select
        recommendation.recommendation_id,
        recommendation.instrument_id,
        instrument.primary_symbol,
        recommendation.bucket,
        recommendation.action,
        recommendation.total_score,
        batch.as_of_date,
        batch.market_code,
        batch.strategy_name,
        batch.horizon_type,
        batch.universe_version,
        thesis.benchmark_code
    from signal.recommendation recommendation
    join signal.recommendation_batch batch on batch.batch_id = recommendation.batch_id
    join ref.instrument instrument on instrument.instrument_id = recommendation.instrument_id
    left join signal.investment_thesis thesis on thesis.thesis_id = recommendation.thesis_id
    join target_date target on batch.as_of_date <= target.as_of_date
    where recommendation.status = 'active'
      {filter_conditions}
),
recommendation_horizons as (
    select
        recommendation.*,
        horizon.horizon_day,
        (recommendation.as_of_date + horizon.horizon_day) as expected_measurement_end_date
    from recommendation_window recommendation
    join horizon_days horizon on true
),
classified_outcomes as (
    select
        recommendation.recommendation_id,
        recommendation.primary_symbol,
        recommendation.as_of_date,
        recommendation.market_code,
        recommendation.strategy_name,
        recommendation.horizon_type,
        recommendation.universe_version,
        recommendation.horizon_day,
        recommendation.expected_measurement_end_date,
        outcome.outcome_id,
        outcome.outcome_label,
        outcome.horizon_days as actual_horizon_days,
        outcome.measurement_end_date as actual_measurement_end_date,
        entry_price.trade_date as entry_price_date,
        exit_price.trade_date as exit_price_date,
        recommendation.benchmark_code,
        benchmark_instrument.instrument_id as benchmark_instrument_id,
        benchmark_entry.trade_date as benchmark_entry_date,
        benchmark_exit.trade_date as benchmark_exit_date,
        case
            when outcome.outcome_id is not null then 'outcome_recorded'
            when recommendation.expected_measurement_end_date > (select as_of_date from target_date) then 'not_due'
            when entry_price.trade_date is null then 'missing_entry_price'
            when exit_price.trade_date is null then 'missing_exit_price'
            else 'ready_for_backfill'
        end as sample_status,
        case
            when recommendation.benchmark_code is null then null
            when benchmark_instrument.instrument_id is null then 'benchmark_instrument_missing'
            when benchmark_entry.trade_date is null or benchmark_exit.trade_date is null then 'benchmark_price_missing'
            else null
        end as benchmark_warning
    from recommendation_horizons recommendation
    left join lateral (
        select trade_date
        from market.daily_price_bar
        where instrument_id = recommendation.instrument_id
          and trade_date <= recommendation.as_of_date
        order by trade_date desc
        limit 1
    ) entry_price on true
    left join lateral (
        select trade_date
        from market.daily_price_bar
        where instrument_id = recommendation.instrument_id
          and trade_date <= least(recommendation.expected_measurement_end_date, (select as_of_date from target_date))
          and (entry_price.trade_date is null or trade_date >= entry_price.trade_date)
        order by trade_date desc
        limit 1
    ) exit_price on true
    left join ref.instrument benchmark_instrument
      on benchmark_instrument.is_active = true
     and lower(benchmark_instrument.primary_symbol) = lower(recommendation.benchmark_code)
    left join lateral (
        select trade_date
        from market.daily_price_bar
        where instrument_id = benchmark_instrument.instrument_id
          and trade_date <= entry_price.trade_date
        order by trade_date desc
        limit 1
    ) benchmark_entry on true
    left join lateral (
        select trade_date
        from market.daily_price_bar
        where instrument_id = benchmark_instrument.instrument_id
          and trade_date <= exit_price.trade_date
        order by trade_date desc
        limit 1
    ) benchmark_exit on true
    left join lateral (
        select
            outcome_id,
            outcome_label,
            horizon_days,
            measurement_end_date
        from performance.recommendation_outcome outcome
        where outcome.recommendation_id = recommendation.recommendation_id
          and outcome.measurement_end_date <= least(recommendation.expected_measurement_end_date, (select as_of_date from target_date))
          and outcome.measurement_end_date >= recommendation.as_of_date
          and outcome.horizon_days between greatest(recommendation.horizon_day - 7, 0) and recommendation.horizon_day + 7
        order by abs(outcome.horizon_days - recommendation.horizon_day), outcome.measurement_end_date desc
        limit 1
    ) outcome on true
),
sample_summary as (
    select
        count(*)::integer as recommendation_horizon_count,
        count(distinct recommendation_id)::integer as recommendation_count,
        count(*) filter (where sample_status = 'outcome_recorded')::integer as outcome_count,
        count(*) filter (where sample_status = 'ready_for_backfill')::integer as ready_for_backfill_count,
        count(*) filter (where sample_status = 'not_due')::integer as not_due_count,
        count(*) filter (where sample_status = 'missing_entry_price')::integer as missing_entry_price_count,
        count(*) filter (where sample_status = 'missing_exit_price')::integer as missing_exit_price_count,
        count(*) filter (where benchmark_warning is not null)::integer as benchmark_warning_count,
        case
            when count(*) = 0 then 0::numeric
            else (count(*) filter (where sample_status = 'outcome_recorded')::numeric / count(*)::numeric)
        end as outcome_coverage_rate
    from classified_outcomes
),
horizon_coverage as (
    select
        horizon_day,
        count(*)::integer as recommendation_horizon_count,
        count(*) filter (where sample_status = 'outcome_recorded')::integer as outcome_count,
        count(*) filter (where sample_status = 'ready_for_backfill')::integer as ready_for_backfill_count,
        count(*) filter (where sample_status = 'not_due')::integer as not_due_count,
        count(*) filter (where sample_status in ('missing_entry_price', 'missing_exit_price'))::integer as price_gap_count
    from classified_outcomes
    group by horizon_day
),
missing_reason_counts as (
    select sample_status, count(*)::integer as row_count
    from classified_outcomes
    group by sample_status
),
missing_examples as (
    select
        primary_symbol,
        recommendation_id,
        as_of_date,
        horizon_day,
        expected_measurement_end_date,
        sample_status,
        benchmark_warning
    from classified_outcomes
    where sample_status <> 'outcome_recorded'
    order by
        case sample_status
            when 'ready_for_backfill' then 1
            when 'missing_exit_price' then 2
            when 'missing_entry_price' then 3
            when 'not_due' then 4
            else 5
        end,
        expected_measurement_end_date,
        primary_symbol
    limit {example_limit}
),
component_rows as (
    select
        recommendation.recommendation_id,
        component.component_name,
        component.component_score,
        component.component_weight,
        outcome.outcome_label,
        case when outcome.outcome_label in ({positive_labels}) then true else false end as is_positive_outcome,
        case when outcome.outcome_id is not null then true else false end as has_outcome
    from recommendation_window recommendation
    join signal.recommendation_score_component component on component.recommendation_id = recommendation.recommendation_id
    left join lateral (
        select outcome_id, outcome_label
        from performance.recommendation_outcome outcome
        where outcome.recommendation_id = recommendation.recommendation_id
          and outcome.measurement_end_date <= (select as_of_date from target_date)
        order by outcome.measurement_end_date desc, outcome.outcome_id desc
        limit 1
    ) outcome on true
    where component.component_name in ({protected_components})
),
component_diagnostics as (
    select
        component_name,
        count(*)::integer as component_row_count,
        count(*) filter (where has_outcome)::integer as outcome_count,
        count(*) filter (where coalesce(component_weight, 0) = 0)::integer as zero_weight_row_count,
        avg(component_score)::numeric(18,8) as avg_component_score,
        avg(component_score) filter (where has_outcome and is_positive_outcome)::numeric(18,8) as avg_positive_score,
        avg(component_score) filter (where has_outcome and not is_positive_outcome)::numeric(18,8) as avg_non_positive_score,
        (
            coalesce(avg(component_score) filter (where has_outcome and is_positive_outcome), 0)
            - coalesce(avg(component_score) filter (where has_outcome and not is_positive_outcome), 0)
        )::numeric(18,8) as positive_score_spread,
        avg(component_weight)::numeric(18,8) as avg_component_weight
    from component_rows
    group by component_name
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'horizon_days', (select json_agg(horizon_day order by horizon_day) from horizon_days),
    'filters', json_build_object(
        'market_code', {sql_literal(market_code) if market_code is not None else 'null::text'},
        'strategy_name', {sql_literal(strategy_name) if strategy_name is not None else 'null::text'},
        'horizon_type', {sql_literal(horizon_type) if horizon_type is not None else 'null::text'},
        'universe_version', {sql_literal(universe_version) if universe_version is not None else 'null::text'}
    ),
    'summary', (select row_to_json(sample_summary) from sample_summary),
    'horizon_coverage', coalesce((select json_agg(row_to_json(horizon_coverage) order by horizon_day) from horizon_coverage), '[]'::json),
    'missing_reason_counts',
        coalesce(
            (
                select json_object_agg(sample_status, row_count order by sample_status)
                from missing_reason_counts
            ),
            '{{}}'::json
        ),
    'missing_examples', coalesce((select json_agg(row_to_json(missing_examples)) from missing_examples), '[]'::json),
    'component_calibration_diagnostics',
        coalesce(
            (
                select json_agg(row_to_json(component_diagnostics) order by component_name)
                from component_diagnostics
            ),
            '[]'::json
        ),
    'guardrails', json_build_object(
        'recommendation_scoring_mutated', false,
        'automatic_order_allowed', false,
        'broker_submit_allowed', false,
        'outcome_policy', 'price_based_outcomes_only_no_synthetic_returns'
    )
)::text;"""


def render_recommendation_outcome_calibration_eval_insert_sql(*, score_json: dict[str, object]) -> str:
    score_text = json.dumps(score_json, ensure_ascii=False, sort_keys=True)
    return f"""insert into ai.eval_run (
    eval_name,
    dataset_version,
    provider,
    model_name,
    score_json
)
values (
    {sql_literal(DEFAULT_EVAL_NAME)},
    {sql_literal(DEFAULT_DATASET_VERSION)},
    {sql_literal(DEFAULT_PROVIDER)},
    {sql_literal(DEFAULT_MODEL_NAME)},
    {sql_literal(score_text)}::jsonb
)
returning eval_run_id;"""


def load_recommendation_outcome_sample_audit(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    horizon_days: tuple[int, ...],
    market_code: str | None = None,
    strategy_name: str | None = None,
    horizon_type: str | None = None,
    universe_version: str | None = None,
    example_limit: int = DEFAULT_EXAMPLE_LIMIT,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_recommendation_outcome_sample_audit_sql(
                as_of_date=as_of_date,
                horizon_days=horizon_days,
                market_code=market_code,
                strategy_name=strategy_name,
                horizon_type=horizon_type,
                universe_version=universe_version,
                example_limit=example_limit,
            )
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Recommendation outcome sample audit lookup did not return a JSON object.")
    return payload


def run_recommendation_outcome_calibration_sample_expansion(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    horizon_days: tuple[int, ...] = (),
    market_code: str | None = None,
    strategy_name: str | None = None,
    horizon_type: str | None = None,
    universe_version: str | None = None,
    outcome_version: str = DEFAULT_OUTCOME_VERSION,
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
    min_professional_coverage_rate: float = DEFAULT_MIN_PROFESSIONAL_COVERAGE_RATE,
    limit: int | None = None,
    example_limit: int = DEFAULT_EXAMPLE_LIMIT,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    resolved_horizon_days = resolve_performance_schedule_horizon_days(horizon_days)
    max_horizon_days = max(resolved_horizon_days)
    sample_audit_before = load_recommendation_outcome_sample_audit(
        config=config,
        as_of_date=as_of_date,
        horizon_days=resolved_horizon_days,
        market_code=market_code,
        strategy_name=strategy_name,
        horizon_type=horizon_type,
        universe_version=universe_version,
        example_limit=example_limit,
        executor=sql_executor,
    )
    base_report: dict[str, object] = {
        "report_name": DEFAULT_REPORT_NAME,
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "horizon_days": list(resolved_horizon_days),
        "filters": {
            "market_code": market_code,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "universe_version": universe_version,
            "outcome_version": outcome_version,
            "limit": limit,
        },
        "sample_audit_before": sample_audit_before,
        "recommendation_scoring_mutated": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "order_boundary": "read_only_no_order",
    }
    if not execute:
        backfill_preview = run_recommendation_outcome_backfill(
            config=config,
            due_on_date=as_of_date,
            horizon_days=resolved_horizon_days,
            market_code=market_code,
            strategy_name=strategy_name,
            horizon_type=horizon_type,
            universe_version=universe_version,
            outcome_version=outcome_version,
            limit=limit,
            execute=False,
            executor=sql_executor,
        )
        quality_preview = run_recommendation_quality_eval(
            config=config,
            as_of_date=as_of_date,
            horizon_days=max_horizon_days,
            min_sample_size=min_sample_size,
            min_professional_coverage_rate=min_professional_coverage_rate,
            execute=False,
            executor=sql_executor,
        )
        score = build_recommendation_outcome_calibration_score(
            as_of_date=as_of_date,
            horizon_days=resolved_horizon_days,
            sample_audit_before=sample_audit_before,
            sample_audit_after=sample_audit_before,
            backfill_report=backfill_preview,
            quality_report=quality_preview,
        )
        return {
            **base_report,
            "status": "planned",
            "backfill": backfill_preview,
            "quality_eval": quality_preview,
            "score": score,
        }

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "horizon_days": list(resolved_horizon_days),
            "market_code": market_code,
            "strategy_name": strategy_name,
            "horizon_type": horizon_type,
            "universe_version": universe_version,
            "outcome_version": outcome_version,
            "limit": limit,
            "min_sample_size": min_sample_size,
            "min_professional_coverage_rate": min_professional_coverage_rate,
            "recommendation_scoring_mutated": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
        },
    )
    try:
        backfill_report = run_recommendation_outcome_backfill(
            config=config,
            due_on_date=as_of_date,
            horizon_days=resolved_horizon_days,
            market_code=market_code,
            strategy_name=strategy_name,
            horizon_type=horizon_type,
            universe_version=universe_version,
            outcome_version=outcome_version,
            limit=limit,
            execute=True,
            executor=sql_executor,
        )
        sample_audit_after = load_recommendation_outcome_sample_audit(
            config=config,
            as_of_date=as_of_date,
            horizon_days=resolved_horizon_days,
            market_code=market_code,
            strategy_name=strategy_name,
            horizon_type=horizon_type,
            universe_version=universe_version,
            example_limit=example_limit,
            executor=sql_executor,
        )
        quality_report = run_recommendation_quality_eval(
            config=config,
            as_of_date=as_of_date,
            horizon_days=max_horizon_days,
            min_sample_size=min_sample_size,
            min_professional_coverage_rate=min_professional_coverage_rate,
            execute=True,
            executor=sql_executor,
        )
        score = build_recommendation_outcome_calibration_score(
            as_of_date=as_of_date,
            horizon_days=resolved_horizon_days,
            sample_audit_before=sample_audit_before,
            sample_audit_after=sample_audit_after,
            backfill_report=backfill_report,
            quality_report=quality_report,
        )
        eval_run_id = int(sql_executor.execute_scalar(render_recommendation_outcome_calibration_eval_insert_sql(score_json=score)))
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return {
        **base_report,
        "status": "completed",
        "run_id": run_id,
        "eval_run_id": eval_run_id,
        "sample_audit_after": sample_audit_after,
        "backfill": backfill_report,
        "quality_eval": quality_report,
        "score": score,
    }


def build_recommendation_outcome_calibration_score(
    *,
    as_of_date: date,
    horizon_days: tuple[int, ...],
    sample_audit_before: dict[str, object],
    sample_audit_after: dict[str, object],
    backfill_report: dict[str, object],
    quality_report: dict[str, object],
) -> dict[str, object]:
    after_summary = _as_dict(sample_audit_after.get("summary"))
    before_summary = _as_dict(sample_audit_before.get("summary"))
    quality_score = _as_dict(quality_report.get("score"))
    outcome_count = _int(after_summary.get("outcome_count"))
    ready_for_backfill_count = _int(after_summary.get("ready_for_backfill_count"))
    missing_entry_count = _int(after_summary.get("missing_entry_price_count"))
    missing_exit_count = _int(after_summary.get("missing_exit_price_count"))
    quality_status = str(quality_score.get("quality_status") or "unknown")
    sample_status = str(quality_score.get("sample_status") or "unknown")
    status = _calibration_status(
        outcome_count=outcome_count,
        ready_for_backfill_count=ready_for_backfill_count,
        missing_entry_count=missing_entry_count,
        missing_exit_count=missing_exit_count,
        quality_status=quality_status,
    )
    return {
        "eval_name": DEFAULT_EVAL_NAME,
        "dataset_version": DEFAULT_DATASET_VERSION,
        "as_of_date": as_of_date.isoformat(),
        "horizon_days": list(horizon_days),
        "status": status,
        "quality_status": quality_status,
        "sample_status": sample_status,
        "sample_audit_before": sample_audit_before,
        "sample_audit_after": sample_audit_after,
        "backfill_summary": _backfill_summary(backfill_report),
        "quality_eval_score": quality_score,
        "component_calibration_diagnostics": _as_list(sample_audit_after.get("component_calibration_diagnostics")),
        "outcome_delta": {
            "outcome_count_before": _int(before_summary.get("outcome_count")),
            "outcome_count_after": outcome_count,
            "outcome_count_added_or_found": max(outcome_count - _int(before_summary.get("outcome_count")), 0),
            "ready_for_backfill_count_after": ready_for_backfill_count,
        },
        "recommendation_scoring_mutated": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "order_boundary": "read_only_no_order",
        "next_action": _next_action(
            status=status,
            quality_score=quality_score,
            ready_for_backfill_count=ready_for_backfill_count,
            missing_entry_count=missing_entry_count,
            missing_exit_count=missing_exit_count,
        ),
    }


def _calibration_status(
    *,
    outcome_count: int,
    ready_for_backfill_count: int,
    missing_entry_count: int,
    missing_exit_count: int,
    quality_status: str,
) -> str:
    if ready_for_backfill_count > 0:
        return "backfill_candidates_remain"
    if missing_entry_count > 0 or missing_exit_count > 0:
        return "price_history_gaps_remain"
    if quality_status == "ready_for_weight_review":
        return "ready_for_manual_weight_review"
    if outcome_count > 0:
        return "collect_more_outcomes_keep_weights"
    return "no_outcome_sample_available"


def _next_action(
    *,
    status: str,
    quality_score: dict[str, object],
    ready_for_backfill_count: int,
    missing_entry_count: int,
    missing_exit_count: int,
) -> str:
    if status == "backfill_candidates_remain":
        return f"성과 검증 후보 {ready_for_backfill_count}개가 남아 있다. 같은 runner를 --execute로 다시 실행하거나 가격 데이터 누락을 먼저 보강한다."
    if status == "price_history_gaps_remain":
        return f"가격 이력 누락 때문에 성과 산출이 막힌 항목이 있다. entry gap {missing_entry_count}개, exit gap {missing_exit_count}개를 가격 수집으로 보강한다."
    if status == "ready_for_manual_weight_review":
        return "표본과 coverage 기준은 충족했다. 그래도 자동 weight 변경은 금지이며 별도 manual/pilot weight task가 필요하다."
    next_action = quality_score.get("next_action")
    if isinstance(next_action, str) and next_action:
        return next_action
    return "성과 표본을 더 쌓고 recommendation-quality-eval-run 결과를 다시 확인한다."


def _backfill_summary(report: dict[str, object]) -> dict[str, object]:
    return {
        "status": report.get("status"),
        "mode": report.get("mode"),
        "candidate_count": _int(report.get("candidate_count")),
        "missing_outcome_count": _int(report.get("missing_outcome_count")),
        "recommendation_outcome_count": _int(report.get("recommendation_outcome_count")),
        "thesis_outcome_count": _int(report.get("thesis_outcome_count")),
        "succeeded_candidate_count": _int(report.get("succeeded_candidate_count")),
        "failed_candidate_count": _int(report.get("failed_candidate_count")),
        "run_id": report.get("run_id"),
    }


def _render_batch_filters(
    *,
    market_code: str | None,
    strategy_name: str | None,
    horizon_type: str | None,
    universe_version: str | None,
) -> str:
    conditions: list[str] = []
    if market_code is not None:
        conditions.append(f"and batch.market_code = {sql_literal(market_code)}")
    if strategy_name is not None:
        conditions.append(f"and batch.strategy_name = {sql_literal(strategy_name)}")
    if horizon_type is not None:
        conditions.append(f"and batch.horizon_type = {sql_literal(horizon_type)}")
    if universe_version is not None:
        conditions.append(f"and batch.universe_version = {sql_literal(universe_version)}")
    return "\n      ".join(conditions)


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _int(value: object) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
