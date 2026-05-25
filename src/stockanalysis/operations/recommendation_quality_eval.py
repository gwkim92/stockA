from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_EVAL_NAME = "recommendation_quality_calibration"
DEFAULT_DATASET_VERSION = "recommendation-quality-live-v1"
DEFAULT_PIPELINE_NAME = "recommendation_quality_eval"
DEFAULT_MODEL_NAME = "deterministic-sql-v1"
DEFAULT_PROVIDER = "postgres"
DEFAULT_MIN_SAMPLE_SIZE = 20
DEFAULT_MIN_PROFESSIONAL_COVERAGE_RATE = 0.80
PROTECTED_CYCLE_STACK_COMPONENTS = (
    "macro_regime_score",
    "domain_cycle_score",
    "theme_cycle_score",
    "instrument_cycle_score",
    "cycle_conflict_penalty",
)
PROTECTED_FUNDAMENTAL_COMPONENTS = (
    "fundamental_quality_score",
    "valuation_margin_score",
    "peer_relative_score",
    "balance_sheet_risk_penalty",
    "thesis_consistency_score",
)
POSITIVE_OUTCOME_LABELS = ("positive", "outperform")


def parse_horizon_days(value: str | int) -> int:
    if isinstance(value, int):
        days = value
    else:
        text = str(value).strip().lower()
        if text.endswith("days"):
            text = text[:-4]
        elif text.endswith("day"):
            text = text[:-3]
        elif text.endswith("d"):
            text = text[:-1]
        days = int(text)
    if days < 1 or days > 3650:
        raise ValueError("horizon must be between 1 and 3650 days.")
    return days


def render_recommendation_quality_eval_sql(*, as_of_date: date, horizon_days: int) -> str:
    if horizon_days < 1 or horizon_days > 3650:
        raise ValueError("horizon_days must be between 1 and 3650.")
    target_date = sql_date(as_of_date)
    positive_labels = ", ".join(sql_literal(label) for label in POSITIVE_OUTCOME_LABELS)
    protected_cycle_components = ", ".join(sql_literal(name) for name in PROTECTED_CYCLE_STACK_COMPONENTS)
    protected_fundamental_components = ", ".join(sql_literal(name) for name in PROTECTED_FUNDAMENTAL_COMPONENTS)
    return f"""-- recommendation quality eval lookup
with recommendation_window as (
    select
        recommendation.recommendation_id,
        recommendation.instrument_id,
        instrument.primary_symbol,
        recommendation.bucket,
        recommendation.action,
        recommendation.total_score,
        batch.as_of_date,
        batch.strategy_name,
        batch.horizon_type,
        batch.universe_version
    from signal.recommendation recommendation
    join signal.recommendation_batch batch on batch.batch_id = recommendation.batch_id
    join ref.instrument instrument on instrument.instrument_id = recommendation.instrument_id
    where batch.as_of_date <= {target_date}
      and recommendation.status = 'active'
),
outcome_window as (
    select distinct on (outcome.recommendation_id)
        outcome.recommendation_id,
        outcome.measurement_start_date,
        outcome.measurement_end_date,
        outcome.horizon_days,
        outcome.absolute_return_pct,
        outcome.benchmark_return_pct,
        outcome.alpha_pct,
        outcome.max_drawdown_pct,
        outcome.outcome_label
    from performance.recommendation_outcome outcome
    join recommendation_window recommendation on recommendation.recommendation_id = outcome.recommendation_id
    where outcome.measurement_end_date <= {target_date}
      and outcome.horizon_days <= {horizon_days}
    order by outcome.recommendation_id, outcome.measurement_end_date desc
),
scored_recommendations as (
    select
        recommendation.*,
        outcome.outcome_label,
        outcome.absolute_return_pct,
        outcome.alpha_pct,
        outcome.max_drawdown_pct,
        case when outcome.outcome_label in ({positive_labels}) then true else false end as is_positive_outcome,
        case when outcome.recommendation_id is not null then true else false end as has_outcome
    from recommendation_window recommendation
    left join outcome_window outcome on outcome.recommendation_id = recommendation.recommendation_id
),
component_rows as (
    select
        recommendation.recommendation_id,
        recommendation.outcome_label,
        recommendation.is_positive_outcome,
        recommendation.has_outcome,
        component.component_name,
        component.component_score,
        component.component_weight
    from scored_recommendations recommendation
    join signal.recommendation_score_component component
      on component.recommendation_id = recommendation.recommendation_id
),
component_metrics as (
    select
        component_name,
        count(*)::integer as recommendation_count,
        count(*) filter (where has_outcome)::integer as outcome_count,
        avg(component_score)::numeric(18,8) as avg_component_score,
        avg(component_score) filter (where has_outcome and is_positive_outcome)::numeric(18,8) as avg_positive_score,
        avg(component_score) filter (where has_outcome and not is_positive_outcome)::numeric(18,8) as avg_non_positive_score,
        (
            coalesce(avg(component_score) filter (where has_outcome and is_positive_outcome), 0)
            - coalesce(avg(component_score) filter (where has_outcome and not is_positive_outcome), 0)
        )::numeric(18,8) as positive_score_spread,
        avg(component_weight)::numeric(18,8) as avg_component_weight,
        count(*) filter (where component_name in ({protected_cycle_components}) and coalesce(component_weight, 0) = 0)::integer as zero_weight_cycle_component_rows
    from component_rows
    group by component_name
),
latest_paper_validation as (
    select
        paper_validation_run_id,
        validation_date,
        status,
        recommendation_count,
        conflict_count,
        approved_action_count,
        created_at
    from trading.paper_validation_run
    where validation_date <= {target_date}
    order by validation_date desc, paper_validation_run_id desc
    limit 1
),
summary as (
    select
        count(*)::integer as recommendation_count,
        count(*) filter (where has_outcome)::integer as outcome_count,
        count(*) filter (where has_outcome and is_positive_outcome)::integer as positive_outcome_count,
        avg(absolute_return_pct) filter (where has_outcome)::numeric(18,8) as avg_absolute_return_pct,
        avg(alpha_pct) filter (where has_outcome and alpha_pct is not null)::numeric(18,8) as avg_alpha_pct,
        avg(max_drawdown_pct) filter (where has_outcome and max_drawdown_pct is not null)::numeric(18,8) as avg_max_drawdown_pct,
        min(as_of_date)::text as first_recommendation_date,
        max(as_of_date)::text as latest_recommendation_date
    from scored_recommendations
),
cycle_guardrail as (
    select
        count(*)::integer as cycle_component_row_count,
        count(*) filter (where coalesce(component_weight, 0) = 0)::integer as zero_weight_cycle_component_row_count,
        count(distinct component_name)::integer as observed_cycle_component_count
    from component_rows
    where component_name in ({protected_cycle_components})
),
fundamental_guardrail as (
    select
        count(*)::integer as fundamental_component_row_count,
        count(*) filter (where coalesce(component_weight, 0) = 0)::integer as zero_weight_fundamental_component_row_count,
        count(distinct component_name)::integer as observed_fundamental_component_count
    from component_rows
    where component_name in ({protected_fundamental_components})
),
professional_coverage_rows as (
    select
        recommendation.recommendation_id,
        recommendation.primary_symbol,
        exists (
            select 1
            from market.financial_metric_normalized metric
            where metric.instrument_id = recommendation.instrument_id
              and metric.as_of_date <= {target_date}
              and metric.metric_status = 'computed'
        ) as has_financial_metrics,
        exists (
            select 1
            from market.peer_relative_snapshot peer_snapshot
            where peer_snapshot.instrument_id = recommendation.instrument_id
              and peer_snapshot.as_of_date <= {target_date}
        ) as has_peer_relative,
        exists (
            select 1
            from market.valuation_snapshot valuation
            where valuation.instrument_id = recommendation.instrument_id
              and valuation.as_of_date <= {target_date}
        ) as has_valuation_snapshot,
        exists (
            select 1
            from research.industry_competitive_position position
            where position.instrument_id = recommendation.instrument_id
              and position.as_of_date <= {target_date}
        ) as has_industry_competitive_position,
        exists (
            select 1
            from research.equity_research_artifact artifact
            where artifact.instrument_id = recommendation.instrument_id
              and artifact.as_of_date <= {target_date}
        ) as has_equity_research_artifact,
        exists (
            select 1
            from signal.investment_thesis thesis
            where thesis.instrument_id = recommendation.instrument_id
              and thesis.status = 'active'
        ) as has_active_thesis
    from recommendation_window recommendation
),
professional_coverage as (
    select
        count(*)::integer as recommendation_count,
        count(*) filter (where has_financial_metrics)::integer as financial_metric_coverage_count,
        count(*) filter (where has_peer_relative)::integer as peer_relative_coverage_count,
        count(*) filter (where has_valuation_snapshot)::integer as valuation_coverage_count,
        count(*) filter (where has_industry_competitive_position)::integer as industry_position_coverage_count,
        count(*) filter (where has_equity_research_artifact)::integer as equity_research_coverage_count,
        count(*) filter (where has_active_thesis)::integer as thesis_coverage_count,
        count(*) filter (
            where has_financial_metrics
              and has_peer_relative
              and has_valuation_snapshot
              and has_industry_competitive_position
              and has_equity_research_artifact
              and has_active_thesis
        )::integer as complete_professional_coverage_count
    from professional_coverage_rows
),
professional_coverage_gaps as (
    select
        primary_symbol,
        array_remove(
            array[
                case when not has_financial_metrics then 'financial_metric_normalized' end,
                case when not has_peer_relative then 'peer_relative_snapshot' end,
                case when not has_valuation_snapshot then 'valuation_snapshot' end,
                case when not has_industry_competitive_position then 'industry_competitive_position' end,
                case when not has_equity_research_artifact then 'equity_research_artifact' end,
                case when not has_active_thesis then 'active_thesis' end
            ],
            null
        ) as missing_layers
    from professional_coverage_rows
    where not (
        has_financial_metrics
        and has_peer_relative
        and has_valuation_snapshot
        and has_industry_competitive_position
        and has_equity_research_artifact
        and has_active_thesis
    )
    order by primary_symbol
    limit 10
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'horizon_days', {horizon_days},
    'summary', (select row_to_json(summary) from summary),
    'component_metrics', coalesce((select json_agg(row_to_json(component_metrics) order by component_name) from component_metrics), '[]'::json),
    'cycle_weight_guardrail', (select row_to_json(cycle_guardrail) from cycle_guardrail),
    'fundamental_weight_guardrail', (select row_to_json(fundamental_guardrail) from fundamental_guardrail),
    'professional_analysis_coverage', (select row_to_json(professional_coverage) from professional_coverage),
    'professional_analysis_gap_examples',
        coalesce((select json_agg(row_to_json(professional_coverage_gaps)) from professional_coverage_gaps), '[]'::json),
    'paper_validation',
        coalesce((select row_to_json(latest_paper_validation) from latest_paper_validation), '{{}}'::json),
    'outcome_label_counts',
        coalesce(
            (
                select json_object_agg(outcome_label, label_count order by outcome_label)
                from (
                    select outcome_label, count(*)::integer as label_count
                    from scored_recommendations
                    where has_outcome
                    group by outcome_label
                ) labels
            ),
            '{{}}'::json
        )
)::text;"""


def render_recommendation_quality_eval_insert_sql(
    *,
    eval_name: str,
    dataset_version: str,
    provider: str,
    model_name: str,
    score_json: dict[str, object],
) -> str:
    score_text = json.dumps(score_json, ensure_ascii=False, sort_keys=True)
    return f"""insert into ai.eval_run (
    eval_name,
    dataset_version,
    provider,
    model_name,
    score_json
)
values (
    {sql_literal(eval_name)},
    {sql_literal(dataset_version)},
    {sql_literal(provider)},
    {sql_literal(model_name)},
    {sql_literal(score_text)}::jsonb
)
returning eval_run_id;"""


def load_recommendation_quality_eval_payload(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    horizon_days: int,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_recommendation_quality_eval_sql(as_of_date=as_of_date, horizon_days=horizon_days)
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Recommendation quality eval lookup did not return a JSON object.")
    return payload


def score_recommendation_quality_eval_payload(
    payload: dict[str, object],
    *,
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
    min_professional_coverage_rate: float = DEFAULT_MIN_PROFESSIONAL_COVERAGE_RATE,
) -> dict[str, object]:
    if min_sample_size < 1:
        raise ValueError("min_sample_size must be greater than 0.")
    if min_professional_coverage_rate < 0 or min_professional_coverage_rate > 1:
        raise ValueError("min_professional_coverage_rate must be between 0 and 1.")
    summary = _as_dict(payload.get("summary"))
    component_metrics = _as_list(payload.get("component_metrics"))
    guardrail = _as_dict(payload.get("cycle_weight_guardrail"))
    fundamental_guardrail = _as_dict(payload.get("fundamental_weight_guardrail"))
    professional_coverage = _as_dict(payload.get("professional_analysis_coverage"))
    professional_gap_examples = _as_list(payload.get("professional_analysis_gap_examples"))
    paper_validation = _as_dict(payload.get("paper_validation"))
    recommendation_count = _int(summary.get("recommendation_count"))
    outcome_count = _int(summary.get("outcome_count"))
    positive_count = _int(summary.get("positive_outcome_count"))
    cycle_row_count = _int(guardrail.get("cycle_component_row_count"))
    zero_weight_cycle_count = _int(guardrail.get("zero_weight_cycle_component_row_count"))
    fundamental_row_count = _int(fundamental_guardrail.get("fundamental_component_row_count"))
    zero_weight_fundamental_count = _int(
        fundamental_guardrail.get("zero_weight_fundamental_component_row_count")
    )
    cycle_weight_unchanged = cycle_row_count == zero_weight_cycle_count
    fundamental_weight_unchanged = fundamental_row_count == zero_weight_fundamental_count
    protected_weight_unchanged = cycle_weight_unchanged and fundamental_weight_unchanged
    outcome_coverage_rate = _ratio(outcome_count, recommendation_count)
    positive_outcome_rate = _ratio(positive_count, outcome_count)
    sample_status = "sufficient_sample" if outcome_count >= min_sample_size else "insufficient_sample"
    professional_recommendation_count = _int(professional_coverage.get("recommendation_count")) or recommendation_count
    complete_professional_coverage_count = _int(
        professional_coverage.get("complete_professional_coverage_count")
    )
    complete_professional_coverage_rate = _ratio(
        complete_professional_coverage_count,
        professional_recommendation_count,
    )
    professional_coverage_sufficient = (
        professional_recommendation_count > 0
        and complete_professional_coverage_rate >= min_professional_coverage_rate
    )
    professional_coverage_status = (
        "sufficient_coverage" if professional_coverage_sufficient else "insufficient_coverage"
    )
    component_scores = [_component_score(item) for item in component_metrics]
    strongest_components = sorted(
        component_scores,
        key=lambda item: (item["sample_status"] == "sufficient_sample", abs(float(item["positive_score_spread"] or 0))),
        reverse=True,
    )
    quality_status = (
        "ready_for_weight_review"
        if sample_status == "sufficient_sample" and protected_weight_unchanged and professional_coverage_sufficient
        else "needs_more_data"
    )
    return {
        "eval_name": DEFAULT_EVAL_NAME,
        "dataset_version": DEFAULT_DATASET_VERSION,
        "as_of_date": payload.get("as_of_date"),
        "horizon_days": payload.get("horizon_days"),
        "quality_status": quality_status,
        "sample_status": sample_status,
        "min_sample_size": min_sample_size,
        "recommendation_count": recommendation_count,
        "outcome_count": outcome_count,
        "outcome_coverage_rate": outcome_coverage_rate,
        "positive_outcome_count": positive_count,
        "positive_outcome_rate": positive_outcome_rate,
        "avg_absolute_return_pct": _decimal_text(summary.get("avg_absolute_return_pct")),
        "avg_alpha_pct": _decimal_text(summary.get("avg_alpha_pct")),
        "avg_max_drawdown_pct": _decimal_text(summary.get("avg_max_drawdown_pct")),
        "outcome_label_counts": payload.get("outcome_label_counts") if isinstance(payload.get("outcome_label_counts"), dict) else {},
        "cycle_weight_guardrail": {
            "cycle_component_row_count": cycle_row_count,
            "zero_weight_cycle_component_row_count": zero_weight_cycle_count,
            "cycle_weight_unchanged": cycle_weight_unchanged,
            "observed_cycle_component_count": _int(guardrail.get("observed_cycle_component_count")),
            "recommendation_scoring_mutated": False,
        },
        "fundamental_weight_guardrail": {
            "fundamental_component_row_count": fundamental_row_count,
            "zero_weight_fundamental_component_row_count": zero_weight_fundamental_count,
            "fundamental_weight_unchanged": fundamental_weight_unchanged,
            "observed_fundamental_component_count": _int(
                fundamental_guardrail.get("observed_fundamental_component_count")
            ),
            "recommendation_scoring_mutated": False,
        },
        "professional_analysis_coverage": {
            "status": professional_coverage_status,
            "min_complete_coverage_rate": round(min_professional_coverage_rate, 6),
            "recommendation_count": professional_recommendation_count,
            "complete_professional_coverage_count": complete_professional_coverage_count,
            "complete_professional_coverage_rate": complete_professional_coverage_rate,
            "layer_coverage": {
                "financial_metric_normalized": _coverage_layer(
                    professional_coverage,
                    key="financial_metric_coverage_count",
                    denominator=professional_recommendation_count,
                ),
                "peer_relative_snapshot": _coverage_layer(
                    professional_coverage,
                    key="peer_relative_coverage_count",
                    denominator=professional_recommendation_count,
                ),
                "valuation_snapshot": _coverage_layer(
                    professional_coverage,
                    key="valuation_coverage_count",
                    denominator=professional_recommendation_count,
                ),
                "industry_competitive_position": _coverage_layer(
                    professional_coverage,
                    key="industry_position_coverage_count",
                    denominator=professional_recommendation_count,
                ),
                "equity_research_artifact": _coverage_layer(
                    professional_coverage,
                    key="equity_research_coverage_count",
                    denominator=professional_recommendation_count,
                ),
                "active_thesis": _coverage_layer(
                    professional_coverage,
                    key="thesis_coverage_count",
                    denominator=professional_recommendation_count,
                ),
            },
            "gap_examples": [
                {
                    "symbol": str(item.get("primary_symbol") or "UNKNOWN"),
                    "missing_layers": _string_list(item.get("missing_layers")),
                }
                for item in professional_gap_examples
            ],
        },
        "paper_validation": {
            "latest_status": paper_validation.get("status"),
            "validation_date": paper_validation.get("validation_date"),
            "recommendation_count": _int(paper_validation.get("recommendation_count")),
            "conflict_count": _int(paper_validation.get("conflict_count")),
            "approved_action_count": _int(paper_validation.get("approved_action_count")),
        },
        "component_metrics": component_scores,
        "strongest_component_candidates": strongest_components[:5],
        "next_action": _next_action(
            sample_status=sample_status,
            cycle_weight_unchanged=cycle_weight_unchanged,
            fundamental_weight_unchanged=fundamental_weight_unchanged,
            professional_coverage_sufficient=professional_coverage_sufficient,
        ),
    }


def run_recommendation_quality_eval(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    horizon_days: int,
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
    min_professional_coverage_rate: float = DEFAULT_MIN_PROFESSIONAL_COVERAGE_RATE,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = load_recommendation_quality_eval_payload(
        config=config,
        as_of_date=as_of_date,
        horizon_days=horizon_days,
        executor=sql_executor,
    )
    score = score_recommendation_quality_eval_payload(
        payload,
        min_sample_size=min_sample_size,
        min_professional_coverage_rate=min_professional_coverage_rate,
    )
    report: dict[str, object] = {
        "report_name": "recommendation_quality_calibration",
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "horizon_days": horizon_days,
        "provider": DEFAULT_PROVIDER,
        "model_name": DEFAULT_MODEL_NAME,
        "score": score,
    }
    if not execute:
        return report
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "horizon_days": horizon_days,
            "min_sample_size": min_sample_size,
            "min_professional_coverage_rate": min_professional_coverage_rate,
            "evaluation_only": True,
            "recommendation_scoring_mutated": False,
        },
    )
    try:
        eval_run_id = int(
            sql_executor.execute_scalar(
                render_recommendation_quality_eval_insert_sql(
                    eval_name=DEFAULT_EVAL_NAME,
                    dataset_version=DEFAULT_DATASET_VERSION,
                    provider=DEFAULT_PROVIDER,
                    model_name=DEFAULT_MODEL_NAME,
                    score_json=score,
                )
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise
    return {
        **report,
        "status": "completed",
        "run_id": run_id,
        "eval_run_id": eval_run_id,
    }


def _component_score(item: dict[str, object]) -> dict[str, object]:
    outcome_count = _int(item.get("outcome_count"))
    return {
        "component_name": item.get("component_name"),
        "recommendation_count": _int(item.get("recommendation_count")),
        "outcome_count": outcome_count,
        "avg_component_score": _decimal_text(item.get("avg_component_score")),
        "avg_positive_score": _decimal_text(item.get("avg_positive_score")),
        "avg_non_positive_score": _decimal_text(item.get("avg_non_positive_score")),
        "positive_score_spread": _decimal_text(item.get("positive_score_spread")),
        "avg_component_weight": _decimal_text(item.get("avg_component_weight")),
        "sample_status": "has_outcomes" if outcome_count > 0 else "no_outcomes",
    }


def _next_action(
    *,
    sample_status: str,
    cycle_weight_unchanged: bool,
    fundamental_weight_unchanged: bool,
    professional_coverage_sufficient: bool,
) -> str:
    if not cycle_weight_unchanged:
        return "추천 cycle component weight가 이미 0이 아니다. 산식 변경 이력을 먼저 확인해야 한다."
    if not fundamental_weight_unchanged:
        return "추천 fundamental/valuation/peer component weight가 이미 0이 아니다. outcome 표본과 승인 이력 없이 산식에 반영됐는지 먼저 확인해야 한다."
    if not professional_coverage_sufficient:
        return "전문가식 분석 coverage가 부족하다. 재무지표, 피어 비교, 밸류에이션, 산업 경쟁 위치, 기업 리서치, active thesis를 먼저 보강해야 한다."
    if sample_status != "sufficient_sample":
        return "outcome 표본이 부족하다. 추천 산식 weight를 변경하지 말고 performance outcome을 더 쌓아야 한다."
    return "표본은 충분하다. component별 spread를 사람이 검토한 뒤 별도 weight 변경 task를 열 수 있다."


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


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


def _coverage_layer(payload: dict[str, object], *, key: str, denominator: int) -> dict[str, object]:
    covered_count = _int(payload.get(key))
    return {
        "covered_count": covered_count,
        "coverage_rate": _ratio(covered_count, denominator),
    }


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _decimal_text(value: object) -> str | None:
    if value is None:
        return None
    return str(Decimal(str(value)))
