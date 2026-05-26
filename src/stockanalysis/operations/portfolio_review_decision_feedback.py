from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date
from typing import Any

from stockanalysis.frontend.live_adapter import DEFAULT_PORTFOLIO_NAME
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_EVAL_NAME = "portfolio_review_decision_outcome_feedback"
DEFAULT_DATASET_VERSION = "portfolio-review-decision-outcome-feedback-v1"
DEFAULT_PIPELINE_NAME = "portfolio_review_decision_outcome_feedback"
DEFAULT_PROVIDER = "deterministic_portfolio_review_feedback_policy"
DEFAULT_MODEL_NAME = "portfolio-review-decision-outcome-feedback-v1"
DEFAULT_MIN_HORIZON_DAYS = 30

CAUTION_DECISION_TYPES = frozenset(
    {
        "reduce_watch",
        "reduce_review",
        "add_blocked_until_evidence",
        "needs_thesis_update",
        "review_required",
        "overweight_review",
    }
)
HOLD_DECISION_TYPES = frozenset({"hold_with_thesis", "hold_review", "watch_small_position"})
POSITIVE_OUTCOME_LABELS = frozenset({"positive", "outperform"})
NEGATIVE_OUTCOME_LABELS = frozenset({"negative", "underperform"})


def render_portfolio_review_decision_history_lookup_sql(
    *,
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME,
    history_eval_run_id: int | None = None,
) -> str:
    id_filter = ""
    if history_eval_run_id is not None:
        id_filter = f"\n      and eval_run.eval_run_id = {int(history_eval_run_id)}"
    return f"""-- portfolio review decision history feedback source lookup
select coalesce(
    (
        select json_build_object(
            'eval_run_id', eval_run.eval_run_id,
            'created_at', eval_run.created_at,
            'eval_name', eval_run.eval_name,
            'dataset_version', eval_run.dataset_version,
            'score_json', eval_run.score_json
        )
        from ai.eval_run eval_run
        where eval_run.eval_name = 'portfolio_review_decision_history'
          and eval_run.dataset_version = 'portfolio-review-decision-history-v1'
          and coalesce(eval_run.score_json->>'portfolio_name', {sql_literal(portfolio_name)}) = {sql_literal(portfolio_name)}{id_filter}
        order by
            nullif(eval_run.score_json->>'as_of_date', '')::date desc nulls last,
            eval_run.created_at desc,
            eval_run.eval_run_id desc
        limit 1
    ),
    '{{}}'::json
)::text;"""


def render_portfolio_review_decision_feedback_evidence_sql(
    *,
    decision_inputs: list[dict[str, object]],
    portfolio_name: str,
    history_as_of_date: date,
    feedback_as_of_date: date,
) -> str:
    decision_text = json.dumps(decision_inputs, ensure_ascii=False, sort_keys=True)
    return f"""-- portfolio review decision outcome feedback evidence lookup
with selected_portfolio as (
    select portfolio_id, portfolio_name
    from portfolio.portfolio
    where portfolio_name = {sql_literal(portfolio_name)}
    order by portfolio_id
    limit 1
),
decision_inputs as (
    select
        (entry.value->>'decision_index')::integer as decision_index,
        upper(entry.value->>'symbol') as symbol,
        nullif(entry.value->>'decision_type', '') as decision_type,
        nullif(entry.value->>'decision_family', '') as decision_family,
        nullif(entry.value->>'related_recommendation_id', '')::bigint as related_recommendation_id,
        nullif(entry.value->>'related_thesis_id', '')::bigint as related_thesis_id
    from jsonb_array_elements({sql_literal(decision_text)}::jsonb) entry(value)
),
instrument_lookup as (
    select
        input.decision_index,
        instrument.instrument_id,
        instrument.primary_symbol
    from decision_inputs input
    left join ref.instrument instrument
      on upper(instrument.primary_symbol) = input.symbol
),
latest_recommendation_outcome as (
    select distinct on (input.decision_index)
        input.decision_index,
        outcome.outcome_id,
        outcome.recommendation_id,
        outcome.measurement_start_date,
        outcome.measurement_end_date,
        outcome.horizon_days,
        outcome.absolute_return_pct,
        outcome.benchmark_return_pct,
        outcome.alpha_pct,
        outcome.max_drawdown_pct,
        outcome.outcome_label
    from decision_inputs input
    left join signal.recommendation recommendation
      on (
          input.related_recommendation_id is not null
          and recommendation.recommendation_id = input.related_recommendation_id
      )
    left join ref.instrument recommended_instrument
      on recommended_instrument.instrument_id = recommendation.instrument_id
    join performance.recommendation_outcome outcome
      on (
          (
              input.related_recommendation_id is not null
              and outcome.recommendation_id = input.related_recommendation_id
          )
          or (
              input.related_recommendation_id is null
              and outcome.recommendation_id in (
                  select recommendation_by_symbol.recommendation_id
                  from signal.recommendation recommendation_by_symbol
                  join ref.instrument instrument_by_symbol
                    on instrument_by_symbol.instrument_id = recommendation_by_symbol.instrument_id
                  where upper(instrument_by_symbol.primary_symbol) = input.symbol
              )
          )
      )
    where outcome.measurement_end_date <= {sql_date(feedback_as_of_date)}
      and outcome.measurement_end_date >= {sql_date(history_as_of_date)}
      and (
          input.related_recommendation_id is null
          or recommended_instrument.primary_symbol is null
          or upper(recommended_instrument.primary_symbol) = input.symbol
      )
    order by input.decision_index, outcome.measurement_end_date desc, outcome.outcome_id desc
),
latest_thesis as (
    select distinct on (input.decision_index)
        input.decision_index,
        thesis.thesis_id,
        thesis.status,
        thesis.title,
        thesis.conviction_score,
        thesis.expected_holding_days,
        thesis.created_at,
        thesis.closed_at
    from decision_inputs input
    join signal.investment_thesis thesis
      on (
          (input.related_thesis_id is not null and thesis.thesis_id = input.related_thesis_id)
          or (
              input.related_thesis_id is null
              and thesis.instrument_id in (
                  select instrument_id
                  from ref.instrument
                  where upper(primary_symbol) = input.symbol
              )
          )
      )
    order by
        input.decision_index,
        case when thesis.status = 'active' then 0 else 1 end,
        thesis.created_at desc,
        thesis.thesis_id desc
),
latest_thesis_outcome as (
    select distinct on (input.decision_index)
        input.decision_index,
        outcome.outcome_id,
        outcome.thesis_id,
        outcome.measurement_start_date,
        outcome.measurement_end_date,
        outcome.holding_days,
        outcome.status,
        outcome.absolute_return_pct,
        outcome.benchmark_return_pct,
        outcome.alpha_pct,
        outcome.success_grade,
        outcome.summary
    from decision_inputs input
    join performance.thesis_outcome outcome
      on (
          (input.related_thesis_id is not null and outcome.thesis_id = input.related_thesis_id)
          or (
              input.related_thesis_id is null
              and outcome.thesis_id in (
                  select thesis.thesis_id
                  from signal.investment_thesis thesis
                  join ref.instrument instrument on instrument.instrument_id = thesis.instrument_id
                  where upper(instrument.primary_symbol) = input.symbol
              )
          )
      )
    where outcome.measurement_end_date <= {sql_date(feedback_as_of_date)}
      and outcome.measurement_end_date >= {sql_date(history_as_of_date)}
    order by input.decision_index, outcome.measurement_end_date desc, outcome.outcome_id desc
),
latest_paper_validation as (
    select validation.*
    from trading.paper_validation_run validation
    where validation.validation_date <= {sql_date(feedback_as_of_date)}
      and (
          validation.portfolio_id = (select portfolio_id from selected_portfolio)
          or validation.portfolio_id is null
      )
    order by validation.validation_date desc, validation.paper_validation_run_id desc
    limit 1
),
price_evidence as (
    select
        input.decision_index,
        baseline.trade_date as baseline_trade_date,
        baseline.adjusted_close as baseline_adjusted_close,
        latest.trade_date as latest_trade_date,
        latest.adjusted_close as latest_adjusted_close,
        case
            when baseline.adjusted_close is not null
             and baseline.adjusted_close <> 0
             and latest.adjusted_close is not null
                then ((latest.adjusted_close - baseline.adjusted_close) / baseline.adjusted_close)::numeric(12,6)
            else null
        end as price_return_pct
    from decision_inputs input
    left join instrument_lookup instrument on instrument.decision_index = input.decision_index
    left join lateral (
        select trade_date, adjusted_close
        from market.daily_price_bar price
        where price.instrument_id = instrument.instrument_id
          and price.trade_date <= {sql_date(history_as_of_date)}
        order by price.trade_date desc
        limit 1
    ) baseline on true
    left join lateral (
        select trade_date, adjusted_close
        from market.daily_price_bar price
        where price.instrument_id = instrument.instrument_id
          and price.trade_date <= {sql_date(feedback_as_of_date)}
          and (baseline.trade_date is null or price.trade_date >= baseline.trade_date)
        order by price.trade_date desc
        limit 1
    ) latest on true
)
select json_build_object(
    'as_of_date', {sql_literal(feedback_as_of_date.isoformat())},
    'history_as_of_date', {sql_literal(history_as_of_date.isoformat())},
    'portfolio_name', coalesce((select portfolio_name from selected_portfolio), {sql_literal(portfolio_name)}),
    'paper_validation',
    coalesce(
        (
            select json_build_object(
                'paper_validation_run_id', paper_validation_run_id,
                'validation_date', validation_date,
                'status', status,
                'recommendation_count', recommendation_count,
                'conflict_count', conflict_count,
                'approved_action_count', approved_action_count,
                'validated_symbols', validated_symbols,
                'blocked_reasons', blocked_reasons,
                'created_at', created_at
            )
            from latest_paper_validation
        ),
        '{{}}'::json
    ),
    'items',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'decision_index', input.decision_index,
                    'symbol', input.symbol,
                    'decision_type', input.decision_type,
                    'decision_family', input.decision_family,
                    'instrument_id', instrument.instrument_id,
                    'recommendation_outcome', json_strip_nulls(json_build_object(
                        'outcome_id', recommendation_outcome.outcome_id,
                        'recommendation_id', recommendation_outcome.recommendation_id,
                        'measurement_start_date', recommendation_outcome.measurement_start_date,
                        'measurement_end_date', recommendation_outcome.measurement_end_date,
                        'horizon_days', recommendation_outcome.horizon_days,
                        'absolute_return_pct', recommendation_outcome.absolute_return_pct,
                        'benchmark_return_pct', recommendation_outcome.benchmark_return_pct,
                        'alpha_pct', recommendation_outcome.alpha_pct,
                        'max_drawdown_pct', recommendation_outcome.max_drawdown_pct,
                        'outcome_label', recommendation_outcome.outcome_label
                    )),
                    'thesis', json_strip_nulls(json_build_object(
                        'thesis_id', thesis.thesis_id,
                        'status', thesis.status,
                        'title', thesis.title,
                        'conviction_score', thesis.conviction_score,
                        'expected_holding_days', thesis.expected_holding_days,
                        'created_at', thesis.created_at,
                        'closed_at', thesis.closed_at
                    )),
                    'thesis_outcome', json_strip_nulls(json_build_object(
                        'outcome_id', thesis_outcome.outcome_id,
                        'thesis_id', thesis_outcome.thesis_id,
                        'measurement_start_date', thesis_outcome.measurement_start_date,
                        'measurement_end_date', thesis_outcome.measurement_end_date,
                        'holding_days', thesis_outcome.holding_days,
                        'status', thesis_outcome.status,
                        'absolute_return_pct', thesis_outcome.absolute_return_pct,
                        'benchmark_return_pct', thesis_outcome.benchmark_return_pct,
                        'alpha_pct', thesis_outcome.alpha_pct,
                        'success_grade', thesis_outcome.success_grade,
                        'summary', thesis_outcome.summary
                    )),
                    'price_evidence', json_strip_nulls(json_build_object(
                        'baseline_trade_date', price.baseline_trade_date,
                        'baseline_adjusted_close', price.baseline_adjusted_close,
                        'latest_trade_date', price.latest_trade_date,
                        'latest_adjusted_close', price.latest_adjusted_close,
                        'price_return_pct', price.price_return_pct
                    ))
                )
                order by input.decision_index
            )
            from decision_inputs input
            left join instrument_lookup instrument on instrument.decision_index = input.decision_index
            left join latest_recommendation_outcome recommendation_outcome
              on recommendation_outcome.decision_index = input.decision_index
            left join latest_thesis thesis on thesis.decision_index = input.decision_index
            left join latest_thesis_outcome thesis_outcome
              on thesis_outcome.decision_index = input.decision_index
            left join price_evidence price on price.decision_index = input.decision_index
        ),
        '[]'::json
    )
)::text;"""


def load_portfolio_review_decision_history_eval(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    history_eval_run_id: int | None = None,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_portfolio_review_decision_history_lookup_sql(
                portfolio_name=portfolio_name,
                history_eval_run_id=history_eval_run_id,
            )
        )
    )
    return payload if isinstance(payload, dict) else {}


def load_portfolio_review_decision_feedback_evidence(
    *,
    config: RuntimeConfig,
    decision_inputs: list[dict[str, object]],
    portfolio_name: str,
    history_as_of_date: date,
    feedback_as_of_date: date,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_portfolio_review_decision_feedback_evidence_sql(
                decision_inputs=decision_inputs,
                portfolio_name=portfolio_name,
                history_as_of_date=history_as_of_date,
                feedback_as_of_date=feedback_as_of_date,
            )
        )
    )
    return payload if isinstance(payload, dict) else {}


def build_portfolio_review_decision_feedback(
    *,
    history_eval: dict[str, object],
    evidence: dict[str, object],
    portfolio_name: str,
    as_of_date: date,
    min_horizon_days: int = DEFAULT_MIN_HORIZON_DAYS,
) -> dict[str, object]:
    if min_horizon_days < 1:
        raise ValueError("min_horizon_days must be positive.")
    history = _as_dict(history_eval.get("score_json"))
    if not history:
        return _missing_history_feedback(portfolio_name=portfolio_name, as_of_date=as_of_date)

    history_date = _parse_date(str(history.get("as_of_date") or ""))
    age_days = (as_of_date - history_date).days if history_date is not None else 0
    raw_decisions = _as_list(history.get("decisions")) or _as_list(history.get("latest_decisions"))
    evidence_by_index = {
        int(_number(item.get("decision_index")) or 0): item
        for item in _as_list(evidence.get("items"))
    }
    paper_validation = _as_dict(evidence.get("paper_validation"))
    feedback_items = [
        _build_decision_feedback_item(
            index=index + 1,
            decision=decision,
            evidence=evidence_by_index.get(index + 1, {}),
            paper_validation=paper_validation,
            age_days=age_days,
            min_horizon_days=min_horizon_days,
        )
        for index, decision in enumerate(raw_decisions)
    ]
    status_counts = dict(Counter(str(item["feedback_status"]) for item in feedback_items))
    feedback_status = _overall_feedback_status(status_counts=status_counts, decision_count=len(feedback_items))

    return {
        "eval_name": DEFAULT_EVAL_NAME,
        "dataset_version": DEFAULT_DATASET_VERSION,
        "as_of_date": as_of_date.isoformat(),
        "portfolio_name": str(history.get("portfolio_name") or portfolio_name),
        "source_history_eval_run_id": _int(history_eval.get("eval_run_id")),
        "source_history_created_at": str(history_eval.get("created_at") or ""),
        "source_history_as_of_date": str(history.get("as_of_date") or ""),
        "min_horizon_days": min_horizon_days,
        "history_age_days": age_days,
        "feedback_status": feedback_status,
        "decision_count": len(feedback_items),
        "too_early_count": status_counts.get("too_early", 0),
        "validated_count": status_counts.get("validated", 0),
        "contradicted_count": status_counts.get("contradicted", 0),
        "needs_more_data_count": status_counts.get("needs_more_data", 0),
        "missing_history_count": 0,
        "status_counts": status_counts,
        "paper_validation": _paper_validation_summary(paper_validation),
        "top_feedback": feedback_items[0] if feedback_items else None,
        "items": feedback_items,
        "latest_items": feedback_items[:12],
        "guardrails": {
            "recommendation_scoring_mutated": False,
            "benchmark_definition_mutated": False,
            "portfolio_position_mutated": False,
            "automatic_rebalance_allowed": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "order_boundary": "read_only_no_order",
        },
        "next_action": _next_action(feedback_status),
    }


def render_portfolio_review_decision_feedback_insert_sql(
    *,
    score_json: dict[str, object],
    eval_name: str = DEFAULT_EVAL_NAME,
    dataset_version: str = DEFAULT_DATASET_VERSION,
    provider: str = DEFAULT_PROVIDER,
    model_name: str = DEFAULT_MODEL_NAME,
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


def run_portfolio_review_decision_feedback(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    as_of_date: date,
    history_eval_run_id: int | None = None,
    min_horizon_days: int = DEFAULT_MIN_HORIZON_DAYS,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    history_eval = load_portfolio_review_decision_history_eval(
        config=config,
        portfolio_name=portfolio_name,
        history_eval_run_id=history_eval_run_id,
        executor=sql_executor,
    )
    history = _as_dict(history_eval.get("score_json"))
    history_as_of_date = _parse_date(str(history.get("as_of_date") or "")) or as_of_date
    decision_inputs = _decision_inputs_from_history(history)
    evidence = (
        load_portfolio_review_decision_feedback_evidence(
            config=config,
            decision_inputs=decision_inputs,
            portfolio_name=portfolio_name,
            history_as_of_date=history_as_of_date,
            feedback_as_of_date=as_of_date,
            executor=sql_executor,
        )
        if decision_inputs
        else {
            "as_of_date": as_of_date.isoformat(),
            "history_as_of_date": history_as_of_date.isoformat(),
            "portfolio_name": portfolio_name,
            "paper_validation": {},
            "items": [],
        }
    )
    feedback = build_portfolio_review_decision_feedback(
        history_eval=history_eval,
        evidence=evidence,
        portfolio_name=portfolio_name,
        as_of_date=as_of_date,
        min_horizon_days=min_horizon_days,
    )
    report: dict[str, object] = {
        "report_name": DEFAULT_EVAL_NAME,
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "portfolio_name": portfolio_name,
        "as_of_date": as_of_date.isoformat(),
        "source_history_eval_run_id": feedback.get("source_history_eval_run_id"),
        "min_horizon_days": min_horizon_days,
        "provider": DEFAULT_PROVIDER,
        "model_name": DEFAULT_MODEL_NAME,
        "feedback": feedback,
    }
    if not execute:
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "portfolio_name": portfolio_name,
            "as_of_date": as_of_date.isoformat(),
            "history_eval_run_id": history_eval_run_id,
            "source_history_eval_run_id": feedback.get("source_history_eval_run_id"),
            "decision_count": feedback.get("decision_count"),
            "feedback_status": feedback.get("feedback_status"),
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
        },
    )
    try:
        eval_run_id = int(
            sql_executor.execute_scalar(
                render_portfolio_review_decision_feedback_insert_sql(score_json=feedback)
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


def _decision_inputs_from_history(history: dict[str, Any]) -> list[dict[str, object]]:
    raw_decisions = _as_list(history.get("decisions")) or _as_list(history.get("latest_decisions"))
    inputs: list[dict[str, object]] = []
    for index, decision in enumerate(raw_decisions, start=1):
        symbol = str(decision.get("symbol") or "").upper()
        if not symbol:
            continue
        inputs.append(
            {
                "decision_index": index,
                "symbol": symbol,
                "decision_type": str(decision.get("decision_type") or ""),
                "decision_family": str(decision.get("decision_family") or ""),
                "related_recommendation_id": _parse_opaque_id(decision.get("related_recommendation_id"), "recommendation"),
                "related_thesis_id": _parse_opaque_id(decision.get("related_thesis_id"), "thesis"),
            }
        )
    return inputs


def _build_decision_feedback_item(
    *,
    index: int,
    decision: dict[str, Any],
    evidence: dict[str, Any],
    paper_validation: dict[str, Any],
    age_days: int,
    min_horizon_days: int,
) -> dict[str, object]:
    symbol = str(decision.get("symbol") or "").upper()
    recommendation_outcome = _as_dict(evidence.get("recommendation_outcome"))
    thesis_outcome = _as_dict(evidence.get("thesis_outcome"))
    thesis = _as_dict(evidence.get("thesis"))
    price_evidence = _as_dict(evidence.get("price_evidence"))
    feedback_status, reason = _classify_decision_feedback(
        decision=decision,
        symbol=symbol,
        recommendation_outcome=recommendation_outcome,
        thesis_outcome=thesis_outcome,
        thesis=thesis,
        price_evidence=price_evidence,
        paper_validation=paper_validation,
        age_days=age_days,
        min_horizon_days=min_horizon_days,
    )
    return {
        "decision_index": index,
        "decision_family": str(decision.get("decision_family") or ""),
        "symbol": symbol,
        "decision_type": str(decision.get("decision_type") or ""),
        "decision_label": str(decision.get("decision_label") or ""),
        "source_decision": {
            "priority": _int(decision.get("priority")),
            "severity": str(decision.get("severity") or ""),
            "current_weight": _number(decision.get("current_weight")),
            "benchmark_weight": _number(decision.get("benchmark_weight")),
            "active_weight": _number(decision.get("active_weight")),
            "related_recommendation_id": _optional_text(decision.get("related_recommendation_id")),
            "related_thesis_id": _optional_text(decision.get("related_thesis_id")),
            "rationale": str(decision.get("rationale") or ""),
        },
        "feedback_status": feedback_status,
        "feedback_reason": reason,
        "evidence": {
            "recommendation_outcome": _compact_recommendation_outcome(recommendation_outcome),
            "thesis": _compact_thesis(thesis),
            "thesis_outcome": _compact_thesis_outcome(thesis_outcome),
            "price_evidence": _compact_price_evidence(price_evidence),
            "paper_validation": _paper_validation_symbol_summary(symbol=symbol, paper_validation=paper_validation),
        },
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "order_boundary": "read_only_no_order",
    }


def _classify_decision_feedback(
    *,
    decision: dict[str, Any],
    symbol: str,
    recommendation_outcome: dict[str, Any],
    thesis_outcome: dict[str, Any],
    thesis: dict[str, Any],
    price_evidence: dict[str, Any],
    paper_validation: dict[str, Any],
    age_days: int,
    min_horizon_days: int,
) -> tuple[str, str]:
    decision_type = str(decision.get("decision_type") or "")
    cautious = decision_type in CAUTION_DECISION_TYPES or str(decision.get("decision_family") or "") in {
        "benchmark_drift",
        "position_sizing",
    }
    hold_like = decision_type in HOLD_DECISION_TYPES
    outcome_signal = _outcome_signal(recommendation_outcome, thesis_outcome, price_evidence)
    paper_blocked = _paper_validation_blocks_symbol(symbol=symbol, paper_validation=paper_validation)
    paper_validated = _paper_validation_validates_symbol(symbol=symbol, paper_validation=paper_validation)
    thesis_closed = bool(thesis) and str(thesis.get("status") or "") in {"closed", "inactive", "expired"}

    if outcome_signal == "negative":
        if cautious:
            return "validated", "후속 성과가 부정적이어서 축소·증액금지·검토 판단이 보수적으로 맞았을 가능성이 높다."
        return "contradicted", "유지 또는 증액 가능 판단 이후 부정적 성과가 확인됐다."
    if outcome_signal == "positive":
        if cautious and not hold_like:
            return "contradicted", "후속 성과가 긍정적이어서 축소·증액금지 판단은 재검토가 필요하다."
        return "validated", "후속 성과가 긍정적이어서 유지 판단을 뒷받침한다."
    if paper_blocked:
        if cautious:
            return "validated", "후속 paper validation이 같은 종목의 거래 또는 안전 조건을 막아 보수적 검토 판단을 뒷받침한다."
        return "contradicted", "후속 paper validation이 같은 종목을 막았는데 기존 판단은 유지 쪽이었다."
    if paper_validated and not cautious:
        return "validated", "paper validation에서 종목이 검증 대상에 포함됐고 명확한 차단이 없다."
    if age_days < min_horizon_days:
        return "too_early", f"{min_horizon_days}일 최소 관찰 기간이 아직 끝나지 않았다."
    if thesis_closed and decision_type in {"needs_thesis_update", "add_blocked_until_evidence"}:
        return "validated", "투자 논리가 종료 또는 비활성 상태라 보강 전 증액 금지 판단을 뒷받침한다."
    return "needs_more_data", "성과 outcome, thesis outcome, paper validation, 가격 변화 중 결정적인 후속 근거가 아직 부족하다."


def _outcome_signal(
    recommendation_outcome: dict[str, Any],
    thesis_outcome: dict[str, Any],
    price_evidence: dict[str, Any],
) -> str:
    outcome_label = str(recommendation_outcome.get("outcome_label") or "").lower()
    if outcome_label in POSITIVE_OUTCOME_LABELS:
        return "positive"
    if outcome_label in NEGATIVE_OUTCOME_LABELS:
        return "negative"
    success_grade = str(thesis_outcome.get("success_grade") or thesis_outcome.get("status") or "").lower()
    if success_grade in {"success", "positive", "outperform"}:
        return "positive"
    if success_grade in {"failed", "negative", "underperform"}:
        return "negative"
    alpha_pct = _number(recommendation_outcome.get("alpha_pct"))
    absolute_return = _number(recommendation_outcome.get("absolute_return_pct"))
    if alpha_pct is not None:
        if alpha_pct > 0.02:
            return "positive"
        if alpha_pct < -0.02:
            return "negative"
    if absolute_return is not None:
        if absolute_return > 0.05:
            return "positive"
        if absolute_return < -0.05:
            return "negative"
    price_return = _number(price_evidence.get("price_return_pct"))
    if price_return is not None:
        if price_return > 0.05:
            return "positive"
        if price_return < -0.05:
            return "negative"
    return "unknown"


def _paper_validation_blocks_symbol(*, symbol: str, paper_validation: dict[str, Any]) -> bool:
    if not paper_validation:
        return False
    if int(_number(paper_validation.get("conflict_count")) or 0) <= 0:
        return False
    blocked_reasons = [str(item) for item in _as_list_or_scalars(paper_validation.get("blocked_reasons"))]
    if not blocked_reasons:
        return False
    upper_symbol = symbol.upper()
    return any(upper_symbol in reason.upper() for reason in blocked_reasons)


def _paper_validation_validates_symbol(*, symbol: str, paper_validation: dict[str, Any]) -> bool:
    validated_symbols = [str(item).upper() for item in _as_list_or_scalars(paper_validation.get("validated_symbols"))]
    return symbol.upper() in validated_symbols


def _overall_feedback_status(*, status_counts: dict[str, int], decision_count: int) -> str:
    if decision_count == 0:
        return "missing_decisions"
    if status_counts.get("contradicted", 0) > 0:
        return "has_contradictions"
    if status_counts.get("needs_more_data", 0) > 0:
        return "needs_more_data"
    if status_counts.get("too_early", 0) == decision_count:
        return "too_early"
    if status_counts.get("validated", 0) == decision_count:
        return "validated"
    return "mixed"


def _paper_validation_summary(paper_validation: dict[str, Any]) -> dict[str, object]:
    return {
        "paper_validation_run_id": _int(paper_validation.get("paper_validation_run_id")),
        "validation_date": str(paper_validation.get("validation_date") or ""),
        "status": str(paper_validation.get("status") or "missing"),
        "recommendation_count": _int(paper_validation.get("recommendation_count")),
        "conflict_count": _int(paper_validation.get("conflict_count")),
        "approved_action_count": _int(paper_validation.get("approved_action_count")),
    }


def _paper_validation_symbol_summary(*, symbol: str, paper_validation: dict[str, Any]) -> dict[str, object]:
    summary = _paper_validation_summary(paper_validation)
    summary.update(
        {
            "symbol_blocked": _paper_validation_blocks_symbol(symbol=symbol, paper_validation=paper_validation),
            "symbol_validated": _paper_validation_validates_symbol(symbol=symbol, paper_validation=paper_validation),
        }
    )
    return summary


def _compact_recommendation_outcome(outcome: dict[str, Any]) -> dict[str, object]:
    return {
        "outcome_id": _int(outcome.get("outcome_id")),
        "recommendation_id": _int(outcome.get("recommendation_id")),
        "measurement_end_date": str(outcome.get("measurement_end_date") or ""),
        "horizon_days": _int(outcome.get("horizon_days")),
        "absolute_return_pct": _number(outcome.get("absolute_return_pct")),
        "alpha_pct": _number(outcome.get("alpha_pct")),
        "outcome_label": str(outcome.get("outcome_label") or ""),
    }


def _compact_thesis(thesis: dict[str, Any]) -> dict[str, object]:
    return {
        "thesis_id": _int(thesis.get("thesis_id")),
        "status": str(thesis.get("status") or ""),
        "title": str(thesis.get("title") or ""),
        "conviction_score": _number(thesis.get("conviction_score")),
    }


def _compact_thesis_outcome(outcome: dict[str, Any]) -> dict[str, object]:
    return {
        "outcome_id": _int(outcome.get("outcome_id")),
        "thesis_id": _int(outcome.get("thesis_id")),
        "measurement_end_date": str(outcome.get("measurement_end_date") or ""),
        "holding_days": _int(outcome.get("holding_days")),
        "absolute_return_pct": _number(outcome.get("absolute_return_pct")),
        "alpha_pct": _number(outcome.get("alpha_pct")),
        "success_grade": str(outcome.get("success_grade") or ""),
        "summary": str(outcome.get("summary") or ""),
    }


def _compact_price_evidence(price: dict[str, Any]) -> dict[str, object]:
    return {
        "baseline_trade_date": str(price.get("baseline_trade_date") or ""),
        "baseline_adjusted_close": _number(price.get("baseline_adjusted_close")),
        "latest_trade_date": str(price.get("latest_trade_date") or ""),
        "latest_adjusted_close": _number(price.get("latest_adjusted_close")),
        "price_return_pct": _number(price.get("price_return_pct")),
    }


def _missing_history_feedback(*, portfolio_name: str, as_of_date: date) -> dict[str, object]:
    return {
        "eval_name": DEFAULT_EVAL_NAME,
        "dataset_version": DEFAULT_DATASET_VERSION,
        "as_of_date": as_of_date.isoformat(),
        "portfolio_name": portfolio_name,
        "source_history_eval_run_id": None,
        "feedback_status": "missing_history",
        "decision_count": 0,
        "too_early_count": 0,
        "validated_count": 0,
        "contradicted_count": 0,
        "needs_more_data_count": 0,
        "missing_history_count": 1,
        "status_counts": {"missing_history": 1},
        "paper_validation": _paper_validation_summary({}),
        "top_feedback": None,
        "items": [],
        "latest_items": [],
        "guardrails": {
            "recommendation_scoring_mutated": False,
            "benchmark_definition_mutated": False,
            "portfolio_position_mutated": False,
            "automatic_rebalance_allowed": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "order_boundary": "read_only_no_order",
        },
        "next_action": "portfolio-review-decision-history-run을 먼저 실행해 검토 결정 이력을 만든다.",
    }


def _next_action(feedback_status: str) -> str:
    if feedback_status == "too_early":
        return "성과 측정 window가 끝날 때까지 기다린 뒤 같은 feedback runner를 재실행한다."
    if feedback_status == "has_contradictions":
        return "contradicted 항목의 thesis, valuation, 포지션 크기 판단을 우선 재검토한다."
    if feedback_status == "needs_more_data":
        return "recommendation outcome backfill과 paper validation을 보강한 뒤 feedback을 다시 계산한다."
    if feedback_status == "validated":
        return "검토 판단이 후속 근거와 맞았다. 표본이 충분해질 때까지 weight 변경 없이 누적한다."
    if feedback_status == "missing_history":
        return "portfolio-review-decision-history-run을 먼저 실행한다."
    return "mixed feedback 항목을 검토하되 추천 weight는 변경하지 않는다."


def _parse_opaque_id(value: object, prefix: str) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = re.fullmatch(rf"{re.escape(prefix)}-(\d+)", text)
    if match:
        return int(match.group(1))
    if text.isdigit():
        return int(text)
    return None


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _as_list_or_scalars(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _int(value: object) -> int | None:
    number = _number(value)
    return int(number) if number is not None else None


def _number(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
