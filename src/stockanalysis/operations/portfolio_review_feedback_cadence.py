from __future__ import annotations

import json
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


DEFAULT_EVAL_NAME = "portfolio_review_feedback_cadence"
DEFAULT_DATASET_VERSION = "portfolio-review-feedback-cadence-v1"
DEFAULT_PIPELINE_NAME = "portfolio_review_feedback_cadence"
DEFAULT_PROVIDER = "deterministic_portfolio_review_feedback_cadence"
DEFAULT_MODEL_NAME = "portfolio-review-feedback-cadence-v1"
DEFAULT_MIN_HORIZON_DAYS = 30


def render_portfolio_review_feedback_cadence_context_sql(
    *,
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME,
    as_of_date: date,
    min_horizon_days: int = DEFAULT_MIN_HORIZON_DAYS,
) -> str:
    if min_horizon_days < 1:
        raise ValueError("min_horizon_days must be positive.")
    return f"""-- portfolio review feedback cadence context lookup
with target_date as (
    select {sql_date(as_of_date)} as as_of_date
),
selected_history as (
    select eval_run.*
    from ai.eval_run eval_run
    where eval_run.eval_name = 'portfolio_review_decision_history'
      and eval_run.dataset_version = 'portfolio-review-decision-history-v1'
      and coalesce(eval_run.score_json->>'portfolio_name', {sql_literal(portfolio_name)}) = {sql_literal(portfolio_name)}
      and nullif(eval_run.score_json->>'as_of_date', '')::date <= (select as_of_date from target_date)
    order by
        nullif(eval_run.score_json->>'as_of_date', '')::date desc nulls last,
        eval_run.created_at desc,
        eval_run.eval_run_id desc
    limit 1
),
selected_feedback as (
    select eval_run.*
    from ai.eval_run eval_run
    where eval_run.eval_name = 'portfolio_review_decision_outcome_feedback'
      and eval_run.dataset_version = 'portfolio-review-decision-outcome-feedback-v1'
      and coalesce(eval_run.score_json->>'portfolio_name', {sql_literal(portfolio_name)}) = {sql_literal(portfolio_name)}
      and nullif(eval_run.score_json->>'as_of_date', '')::date <= (select as_of_date from target_date)
    order by
        nullif(eval_run.score_json->>'as_of_date', '')::date desc nulls last,
        eval_run.created_at desc,
        eval_run.eval_run_id desc
    limit 1
),
selected_calibration as (
    select eval_run.*
    from ai.eval_run eval_run
    where eval_run.eval_name = 'portfolio_review_feedback_calibration'
      and eval_run.dataset_version = 'portfolio-review-feedback-calibration-v1'
      and coalesce(eval_run.score_json->>'portfolio_name', {sql_literal(portfolio_name)}) = {sql_literal(portfolio_name)}
      and nullif(eval_run.score_json->>'as_of_date', '')::date <= (select as_of_date from target_date)
    order by
        nullif(eval_run.score_json->>'as_of_date', '')::date desc nulls last,
        eval_run.created_at desc,
        eval_run.eval_run_id desc
    limit 1
),
history_decisions as (
    select
        decision.ordinality::integer as decision_index,
        decision.value as decision_json,
        upper(decision.value->>'symbol') as symbol,
        nullif(regexp_replace(coalesce(decision.value->>'related_recommendation_id', ''), '[^0-9]', '', 'g'), '')::bigint
            as related_recommendation_id
    from selected_history history,
         lateral jsonb_array_elements(coalesce(history.score_json->'decisions', '[]'::jsonb))
             with ordinality as decision(value, ordinality)
),
instrument_lookup as (
    select
        decision.decision_index,
        decision.symbol,
        instrument.instrument_id
    from history_decisions decision
    left join ref.instrument instrument
      on upper(instrument.primary_symbol) = decision.symbol
),
recommendation_outcome_evidence as (
    select distinct decision.decision_index
    from history_decisions decision
    join performance.recommendation_outcome outcome
      on (
          decision.related_recommendation_id is not null
          and outcome.recommendation_id = decision.related_recommendation_id
      )
    where outcome.measurement_end_date <= (select as_of_date from target_date)
      and outcome.measurement_end_date >= (
          select nullif(score_json->>'as_of_date', '')::date from selected_history
      )
),
price_evidence as (
    select
        decision.decision_index,
        baseline.trade_date as baseline_trade_date,
        latest.trade_date as latest_trade_date
    from history_decisions decision
    left join instrument_lookup instrument on instrument.decision_index = decision.decision_index
    left join lateral (
        select trade_date
        from market.daily_price_bar price
        where price.instrument_id = instrument.instrument_id
          and price.trade_date <= (
              select nullif(score_json->>'as_of_date', '')::date from selected_history
          )
        order by trade_date desc
        limit 1
    ) baseline on true
    left join lateral (
        select trade_date
        from market.daily_price_bar price
        where price.instrument_id = instrument.instrument_id
          and price.trade_date <= (select as_of_date from target_date)
          and (baseline.trade_date is null or price.trade_date >= baseline.trade_date)
        order by trade_date desc
        limit 1
    ) latest on true
),
latest_paper_validation as (
    select validation.*
    from trading.paper_validation_run validation
    left join portfolio.portfolio portfolio on portfolio.portfolio_id = validation.portfolio_id
    where validation.validation_date <= (select as_of_date from target_date)
      and (
          portfolio.portfolio_name = {sql_literal(portfolio_name)}
          or validation.portfolio_id is null
      )
    order by validation.validation_date desc, validation.paper_validation_run_id desc
    limit 1
)
select json_build_object(
    'as_of_date', (select as_of_date::text from target_date),
    'portfolio_name', {sql_literal(portfolio_name)},
    'min_horizon_days', {int(min_horizon_days)},
    'history',
    coalesce(
        (
            select json_build_object(
                'status', 'loaded',
                'eval_run_id', eval_run_id,
                'created_at', created_at,
                'as_of_date', score_json->>'as_of_date',
                'portfolio_name', score_json->>'portfolio_name',
                'decision_status', score_json->>'decision_status',
                'decision_count', coalesce(nullif(score_json->>'decision_count', '')::integer, 0),
                'review_required_count', coalesce(nullif(score_json->>'review_required_count', '')::integer, 0),
                'latest_decisions', coalesce(score_json->'latest_decisions', '[]'::jsonb)
            )
            from selected_history
        ),
        json_build_object(
            'status', 'missing',
            'portfolio_name', {sql_literal(portfolio_name)},
            'decision_status', 'missing',
            'decision_count', 0,
            'review_required_count', 0,
            'latest_decisions', '[]'::json
        )
    ),
    'feedback',
    coalesce(
        (
            select json_build_object(
                'status', 'loaded',
                'eval_run_id', eval_run_id,
                'created_at', created_at,
                'as_of_date', score_json->>'as_of_date',
                'portfolio_name', score_json->>'portfolio_name',
                'source_history_eval_run_id', score_json->>'source_history_eval_run_id',
                'source_history_as_of_date', score_json->>'source_history_as_of_date',
                'min_horizon_days', coalesce(nullif(score_json->>'min_horizon_days', '')::integer, {int(min_horizon_days)}),
                'history_age_days', coalesce(nullif(score_json->>'history_age_days', '')::integer, 0),
                'feedback_status', score_json->>'feedback_status',
                'decision_count', coalesce(nullif(score_json->>'decision_count', '')::integer, 0),
                'too_early_count', coalesce(nullif(score_json->>'too_early_count', '')::integer, 0),
                'validated_count', coalesce(nullif(score_json->>'validated_count', '')::integer, 0),
                'contradicted_count', coalesce(nullif(score_json->>'contradicted_count', '')::integer, 0),
                'needs_more_data_count', coalesce(nullif(score_json->>'needs_more_data_count', '')::integer, 0)
            )
            from selected_feedback
        ),
        json_build_object(
            'status', 'missing',
            'portfolio_name', {sql_literal(portfolio_name)},
            'feedback_status', 'missing',
            'decision_count', 0,
            'too_early_count', 0,
            'validated_count', 0,
            'contradicted_count', 0,
            'needs_more_data_count', 0
        )
    ),
    'calibration',
    coalesce(
        (
            select json_build_object(
                'status', 'loaded',
                'eval_run_id', eval_run_id,
                'created_at', created_at,
                'as_of_date', score_json->>'as_of_date',
                'portfolio_name', score_json->>'portfolio_name',
                'calibration_status', score_json->>'calibration_status',
                'feedback_run_count', coalesce(nullif(score_json->>'feedback_run_count', '')::integer, 0),
                'decision_count', coalesce(nullif(score_json->>'decision_count', '')::integer, 0),
                'mature_decision_count', coalesce(nullif(score_json->>'mature_decision_count', '')::integer, 0),
                'too_early_count', coalesce(nullif(score_json->>'too_early_count', '')::integer, 0),
                'validated_count', coalesce(nullif(score_json->>'validated_count', '')::integer, 0),
                'contradicted_count', coalesce(nullif(score_json->>'contradicted_count', '')::integer, 0),
                'needs_more_data_count', coalesce(nullif(score_json->>'needs_more_data_count', '')::integer, 0),
                'latest_feedback_runs', coalesce(score_json->'latest_feedback_runs', '[]'::jsonb)
            )
            from selected_calibration
        ),
        json_build_object(
            'status', 'missing',
            'portfolio_name', {sql_literal(portfolio_name)},
            'calibration_status', 'missing',
            'feedback_run_count', 0,
            'decision_count', 0,
            'mature_decision_count', 0,
            'too_early_count', 0,
            'validated_count', 0,
            'contradicted_count', 0,
            'needs_more_data_count', 0,
            'latest_feedback_runs', '[]'::json
        )
    ),
    'evidence',
    json_build_object(
        'history_age_days',
            coalesce(
                ((select as_of_date from target_date) - (select nullif(score_json->>'as_of_date', '')::date from selected_history))::integer,
                0
            ),
        'decision_count', coalesce((select count(*)::integer from history_decisions), 0),
        'recommendation_link_count',
            coalesce((select count(*)::integer from history_decisions where related_recommendation_id is not null), 0),
        'recommendation_outcome_count',
            coalesce((select count(*)::integer from recommendation_outcome_evidence), 0),
        'price_evidence_count',
            coalesce(
                (
                    select count(*)::integer
                    from price_evidence
                    where baseline_trade_date is not null and latest_trade_date is not null
                ),
                0
            ),
        'paper_validation',
            coalesce(
                (
                    select json_build_object(
                        'paper_validation_run_id', paper_validation_run_id,
                        'validation_date', validation_date,
                        'status', status,
                        'recommendation_count', recommendation_count,
                        'conflict_count', conflict_count,
                        'approved_action_count', approved_action_count
                    )
                    from latest_paper_validation
                ),
                json_build_object(
                    'status', 'missing',
                    'recommendation_count', 0,
                    'conflict_count', 0,
                    'approved_action_count', 0
                )
            )
    )
)::text;"""


def load_portfolio_review_feedback_cadence_context(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    as_of_date: date,
    min_horizon_days: int = DEFAULT_MIN_HORIZON_DAYS,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_portfolio_review_feedback_cadence_context_sql(
                portfolio_name=portfolio_name,
                as_of_date=as_of_date,
                min_horizon_days=min_horizon_days,
            )
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Portfolio review feedback cadence lookup did not return a JSON object.")
    return payload


def build_portfolio_review_feedback_cadence(
    *,
    context: dict[str, object],
    portfolio_name: str,
    as_of_date: date,
    min_horizon_days: int = DEFAULT_MIN_HORIZON_DAYS,
) -> dict[str, object]:
    if min_horizon_days < 1:
        raise ValueError("min_horizon_days must be positive.")
    history = _as_dict(context.get("history"))
    feedback = _as_dict(context.get("feedback"))
    calibration = _as_dict(context.get("calibration"))
    evidence = _as_dict(context.get("evidence"))
    history_eval_run_id = _int(history.get("eval_run_id"))
    feedback_eval_run_id = _int(feedback.get("eval_run_id"))
    feedback_source_history_eval_run_id = _int(feedback.get("source_history_eval_run_id"))
    calibration_feedback_run_ids = {
        _int(item.get("eval_run_id"))
        for item in _as_list(calibration.get("latest_feedback_runs"))
        if _int(item.get("eval_run_id")) is not None
    }
    history_as_of_date = str(history.get("as_of_date") or "")
    feedback_as_of_date = str(feedback.get("as_of_date") or "")
    calibration_as_of_date = str(calibration.get("as_of_date") or "")
    history_age_days = _int(evidence.get("history_age_days")) or 0
    decision_count = _int(history.get("decision_count")) or _int(evidence.get("decision_count")) or 0
    feedback_is_latest = (
        history_eval_run_id is not None
        and feedback_eval_run_id is not None
        and feedback_source_history_eval_run_id == history_eval_run_id
    )
    feedback_is_stale_by_date = bool(feedback_as_of_date and feedback_as_of_date < as_of_date.isoformat())
    calibration_includes_latest_feedback = feedback_eval_run_id is not None and feedback_eval_run_id in calibration_feedback_run_ids
    calibration_is_stale_by_date = (
        bool(feedback_as_of_date and calibration_as_of_date)
        and calibration_as_of_date < feedback_as_of_date
    )

    cadence_status = _cadence_status(
        history_status=str(history.get("status") or "missing"),
        decision_count=decision_count,
        history_age_days=history_age_days,
        min_horizon_days=min_horizon_days,
        feedback_status=str(feedback.get("status") or "missing"),
        feedback_feedback_status=str(feedback.get("feedback_status") or "missing"),
        feedback_is_latest=feedback_is_latest,
        feedback_is_stale_by_date=feedback_is_stale_by_date,
        calibration_status=str(calibration.get("status") or "missing"),
        calibration_includes_latest_feedback=calibration_includes_latest_feedback,
        calibration_is_stale_by_date=calibration_is_stale_by_date,
        evidence=evidence,
    )
    commands = _commands(
        cadence_status=cadence_status,
        portfolio_name=portfolio_name,
        as_of_date=as_of_date,
        history_eval_run_id=history_eval_run_id,
    )

    return {
        "eval_name": DEFAULT_EVAL_NAME,
        "dataset_version": DEFAULT_DATASET_VERSION,
        "as_of_date": as_of_date.isoformat(),
        "portfolio_name": portfolio_name,
        "min_horizon_days": min_horizon_days,
        "cadence_status": cadence_status,
        "action_type": commands["action_type"],
        "should_run_now": commands["should_run_now"],
        "should_wait": commands["should_wait"],
        "wait_until": commands["wait_until"],
        "command": commands["command"],
        "follow_up_command": commands["follow_up_command"],
        "label": commands["label"],
        "reason": commands["reason"],
        "history": _history_summary(history),
        "feedback": _feedback_summary(feedback),
        "calibration": _calibration_summary(calibration),
        "evidence": _evidence_summary(evidence),
        "blocks_weight_review": True,
        "recommendation_scoring_mutated": False,
        "benchmark_definition_mutated": False,
        "portfolio_position_mutated": False,
        "automatic_weight_change_allowed": False,
        "automatic_rebalance_allowed": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "order_boundary": "read_only_no_order",
        "next_action": commands["label"],
    }


def render_portfolio_review_feedback_cadence_insert_sql(
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


def run_portfolio_review_feedback_cadence(
    *,
    config: RuntimeConfig,
    portfolio_name: str,
    as_of_date: date,
    min_horizon_days: int = DEFAULT_MIN_HORIZON_DAYS,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    context = load_portfolio_review_feedback_cadence_context(
        config=config,
        portfolio_name=portfolio_name,
        as_of_date=as_of_date,
        min_horizon_days=min_horizon_days,
        executor=sql_executor,
    )
    cadence = build_portfolio_review_feedback_cadence(
        context=context,
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
        "provider": DEFAULT_PROVIDER,
        "model_name": DEFAULT_MODEL_NAME,
        "cadence": cadence,
    }
    if not execute:
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "portfolio_name": portfolio_name,
            "as_of_date": as_of_date.isoformat(),
            "cadence_status": cadence["cadence_status"],
            "should_run_now": cadence["should_run_now"],
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
        },
    )
    try:
        eval_run_id = int(
            sql_executor.execute_scalar(
                render_portfolio_review_feedback_cadence_insert_sql(score_json=cadence)
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


def _cadence_status(
    *,
    history_status: str,
    decision_count: int,
    history_age_days: int,
    min_horizon_days: int,
    feedback_status: str,
    feedback_feedback_status: str,
    feedback_is_latest: bool,
    feedback_is_stale_by_date: bool,
    calibration_status: str,
    calibration_includes_latest_feedback: bool,
    calibration_is_stale_by_date: bool,
    evidence: dict[str, Any],
) -> str:
    if history_status != "loaded" or decision_count <= 0:
        return "missing_evidence_review_required"
    if history_age_days < min_horizon_days:
        return "wait_for_outcome_window"
    if not feedback_is_latest or feedback_status != "loaded" or feedback_is_stale_by_date:
        if _evidence_is_missing_for_mature_feedback(evidence):
            return "missing_evidence_review_required"
        return "run_feedback_now"
    if feedback_feedback_status == "needs_more_data" and _evidence_is_missing_for_mature_feedback(evidence):
        return "missing_evidence_review_required"
    if calibration_status != "loaded" or not calibration_includes_latest_feedback or calibration_is_stale_by_date:
        return "run_calibration_now"
    return "calibration_current"


def _evidence_is_missing_for_mature_feedback(evidence: dict[str, Any]) -> bool:
    decision_count = _int(evidence.get("decision_count")) or 0
    recommendation_link_count = _int(evidence.get("recommendation_link_count")) or 0
    recommendation_outcome_count = _int(evidence.get("recommendation_outcome_count")) or 0
    price_evidence_count = _int(evidence.get("price_evidence_count")) or 0
    paper_validation = _as_dict(evidence.get("paper_validation"))
    paper_validation_status = str(paper_validation.get("status") or "missing")
    if decision_count <= 0:
        return True
    has_recommendation_outcomes = recommendation_link_count == 0 or recommendation_outcome_count > 0
    has_price_evidence = price_evidence_count > 0
    has_paper_validation = paper_validation_status != "missing"
    return not (has_recommendation_outcomes or has_price_evidence or has_paper_validation)


def _commands(
    *,
    cadence_status: str,
    portfolio_name: str,
    as_of_date: date,
    history_eval_run_id: int | None,
) -> dict[str, object]:
    quoted_portfolio = f'"{portfolio_name}"'
    as_of = as_of_date.isoformat()
    history_command = (
        "stockanalysis-operations portfolio-review-decision-history-run "
        f"--env-file <ENV> --portfolio-name {quoted_portfolio} --as-of-date {as_of} --execute"
    )
    feedback_command = (
        "stockanalysis-operations portfolio-review-decision-outcome-feedback-run "
        f"--env-file <ENV> --portfolio-name {quoted_portfolio} --as-of-date {as_of}"
        + (f" --history-eval-run-id {history_eval_run_id}" if history_eval_run_id is not None else "")
        + " --execute"
    )
    calibration_command = (
        "stockanalysis-operations portfolio-review-feedback-calibration-run "
        f"--env-file <ENV> --portfolio-name {quoted_portfolio} --as-of-date {as_of} --execute"
    )
    if cadence_status == "missing_evidence_review_required":
        return {
            "action_type": "inspect_or_repair_evidence",
            "should_run_now": False,
            "should_wait": False,
            "wait_until": "",
            "command": history_command,
            "follow_up_command": feedback_command,
            "label": "검토 이력 또는 후속 근거를 먼저 보강한다.",
            "reason": "검토 결정, 가격, paper validation, recommendation outcome 중 필요한 근거가 부족하다.",
        }
    if cadence_status == "wait_for_outcome_window":
        return {
            "action_type": "wait",
            "should_run_now": False,
            "should_wait": True,
            "wait_until": "",
            "command": feedback_command,
            "follow_up_command": calibration_command,
            "label": "최소 관찰 기간이 끝날 때까지 기다린다.",
            "reason": "검토 결정이 아직 outcome feedback을 평가할 만큼 오래되지 않았다.",
        }
    if cadence_status == "run_feedback_now":
        return {
            "action_type": "execute_feedback",
            "should_run_now": True,
            "should_wait": False,
            "wait_until": "",
            "command": feedback_command,
            "follow_up_command": calibration_command,
            "label": "검토 결정 사후평가를 지금 실행한다.",
            "reason": "검토 이력이 성숙했지만 최신 feedback이 없거나 stale 상태다.",
        }
    if cadence_status == "run_calibration_now":
        return {
            "action_type": "execute_calibration",
            "should_run_now": True,
            "should_wait": False,
            "wait_until": "",
            "command": calibration_command,
            "follow_up_command": "",
            "label": "누적 calibration을 지금 실행한다.",
            "reason": "최신 feedback은 있으나 calibration이 없거나 최신 feedback을 포함하지 않는다.",
        }
    return {
        "action_type": "monitor",
        "should_run_now": False,
        "should_wait": True,
        "wait_until": "",
        "command": calibration_command,
        "follow_up_command": "",
        "label": "검토 feedback cadence는 현재 최신 상태다.",
        "reason": "최신 history, feedback, calibration이 서로 연결되어 있다.",
    }


def _history_summary(history: dict[str, Any]) -> dict[str, object]:
    return {
        "status": str(history.get("status") or "missing"),
        "eval_run_id": _int(history.get("eval_run_id")),
        "created_at": str(history.get("created_at") or ""),
        "as_of_date": str(history.get("as_of_date") or ""),
        "decision_status": str(history.get("decision_status") or "missing"),
        "decision_count": _int(history.get("decision_count")) or 0,
        "review_required_count": _int(history.get("review_required_count")) or 0,
    }


def _feedback_summary(feedback: dict[str, Any]) -> dict[str, object]:
    return {
        "status": str(feedback.get("status") or "missing"),
        "eval_run_id": _int(feedback.get("eval_run_id")),
        "created_at": str(feedback.get("created_at") or ""),
        "as_of_date": str(feedback.get("as_of_date") or ""),
        "source_history_eval_run_id": _int(feedback.get("source_history_eval_run_id")),
        "source_history_as_of_date": str(feedback.get("source_history_as_of_date") or ""),
        "feedback_status": str(feedback.get("feedback_status") or "missing"),
        "decision_count": _int(feedback.get("decision_count")) or 0,
        "too_early_count": _int(feedback.get("too_early_count")) or 0,
        "validated_count": _int(feedback.get("validated_count")) or 0,
        "contradicted_count": _int(feedback.get("contradicted_count")) or 0,
        "needs_more_data_count": _int(feedback.get("needs_more_data_count")) or 0,
    }


def _calibration_summary(calibration: dict[str, Any]) -> dict[str, object]:
    return {
        "status": str(calibration.get("status") or "missing"),
        "eval_run_id": _int(calibration.get("eval_run_id")),
        "created_at": str(calibration.get("created_at") or ""),
        "as_of_date": str(calibration.get("as_of_date") or ""),
        "calibration_status": str(calibration.get("calibration_status") or "missing"),
        "feedback_run_count": _int(calibration.get("feedback_run_count")) or 0,
        "decision_count": _int(calibration.get("decision_count")) or 0,
        "mature_decision_count": _int(calibration.get("mature_decision_count")) or 0,
        "too_early_count": _int(calibration.get("too_early_count")) or 0,
        "validated_count": _int(calibration.get("validated_count")) or 0,
        "contradicted_count": _int(calibration.get("contradicted_count")) or 0,
        "needs_more_data_count": _int(calibration.get("needs_more_data_count")) or 0,
        "latest_feedback_run_ids": [
            item
            for item in (
                _int(entry.get("eval_run_id"))
                for entry in _as_list(calibration.get("latest_feedback_runs"))
            )
            if item is not None
        ],
    }


def _evidence_summary(evidence: dict[str, Any]) -> dict[str, object]:
    paper_validation = _as_dict(evidence.get("paper_validation"))
    return {
        "history_age_days": _int(evidence.get("history_age_days")) or 0,
        "decision_count": _int(evidence.get("decision_count")) or 0,
        "recommendation_link_count": _int(evidence.get("recommendation_link_count")) or 0,
        "recommendation_outcome_count": _int(evidence.get("recommendation_outcome_count")) or 0,
        "price_evidence_count": _int(evidence.get("price_evidence_count")) or 0,
        "paper_validation": {
            "paper_validation_run_id": _int(paper_validation.get("paper_validation_run_id")),
            "validation_date": str(paper_validation.get("validation_date") or ""),
            "status": str(paper_validation.get("status") or "missing"),
            "recommendation_count": _int(paper_validation.get("recommendation_count")) or 0,
            "conflict_count": _int(paper_validation.get("conflict_count")) or 0,
            "approved_action_count": _int(paper_validation.get("approved_action_count")) or 0,
        },
    }


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None
