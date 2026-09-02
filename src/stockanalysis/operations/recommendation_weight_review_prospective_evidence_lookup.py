from __future__ import annotations

import json
from datetime import date

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations.recommendation_weight_review_prospective_evidence_contract import (
    DEFAULT_DATASET_VERSION,
    DEFAULT_EVAL_NAME,
    DEFAULT_MODEL_NAME,
    DEFAULT_PORTFOLIO_NAME,
    DEFAULT_PROVIDER,
    SOURCE_FEEDBACK_CALIBRATION_DATASET_VERSION,
    SOURCE_FEEDBACK_CALIBRATION_EVAL_NAME,
    SOURCE_FEEDBACK_DATASET_VERSION,
    SOURCE_FEEDBACK_EVAL_NAME,
    SOURCE_LINEAGE_DATASET_VERSION,
    SOURCE_LINEAGE_EVAL_NAME,
    SOURCE_OUTCOME_DATASET_VERSION,
    SOURCE_OUTCOME_EVAL_NAME,
    SOURCE_QUALITY_DATASET_VERSION,
    SOURCE_QUALITY_EVAL_NAME,
)


def render_prospective_evidence_bundle_lookup_sql(
    *,
    as_of_date: date,
    lineage_eval_run_id: int | None = None,
    portfolio_feedback_calibration_eval_run_id: int | None = None,
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME,
) -> str:
    if lineage_eval_run_id is not None and lineage_eval_run_id <= 0:
        raise ValueError("lineage_eval_run_id must be greater than 0.")
    if (
        portfolio_feedback_calibration_eval_run_id is not None
        and portfolio_feedback_calibration_eval_run_id <= 0
    ):
        raise ValueError(
            "portfolio_feedback_calibration_eval_run_id must be greater than 0."
        )
    clean_portfolio_name = portfolio_name.strip()
    if not clean_portfolio_name:
        raise ValueError("portfolio_name must not be empty.")

    lineage_id_filter = ""
    if lineage_eval_run_id is not None:
        lineage_id_filter = f"\n      and eval_run.eval_run_id = {lineage_eval_run_id}"
    feedback_calibration_id_filter = ""
    if portfolio_feedback_calibration_eval_run_id is not None:
        feedback_calibration_id_filter = (
            "\n      and eval_run.eval_run_id = "
            f"{portfolio_feedback_calibration_eval_run_id}"
        )

    as_of_sql = sql_date(as_of_date)
    portfolio_sql = sql_literal(clean_portfolio_name)
    lineage_score_date = _render_optional_score_date_expression("eval_run")
    source_score_date = _render_optional_score_date_expression("source_eval")
    feedback_score_date = _render_optional_score_date_expression("eval_run")
    feedback_artifact_score_date = _render_optional_score_date_expression("feedback_eval")

    return f"""-- recommendation weight review prospective evidence foundation v1 atomic lookup
with selected_lineage as (
    select
        eval_run.eval_run_id,
        eval_run.eval_name,
        eval_run.dataset_version,
        eval_run.provider,
        eval_run.model_name,
        eval_run.score_json,
        eval_run.created_at
    from ai.eval_run eval_run
    where eval_run.eval_name = {sql_literal(SOURCE_LINEAGE_EVAL_NAME)}
      and eval_run.dataset_version = {sql_literal(SOURCE_LINEAGE_DATASET_VERSION)}
      and eval_run.created_at::date <= {as_of_sql}
      and coalesce(eval_run.score_json->>'status', '') = 'reconciled_read_only'
      and coalesce(eval_run.score_json->>'lineage_reconciled', '') = 'true'
      and ({lineage_score_date} is null or {lineage_score_date} <= {as_of_sql}){lineage_id_filter}
    order by eval_run.created_at desc, eval_run.eval_run_id desc
    limit 1
),
lineage_refs as (
    select
        case
            when coalesce(selected_lineage.score_json #>> '{{canonical_chain,quality,eval_run_id}}', '') ~ '^[1-9][0-9]*$'
                then (selected_lineage.score_json #>> '{{canonical_chain,quality,eval_run_id}}')::bigint
            else null::bigint
        end as quality_eval_run_id,
        case
            when coalesce(selected_lineage.score_json #>> '{{canonical_chain,outcome,eval_run_id}}', '') ~ '^[1-9][0-9]*$'
                then (selected_lineage.score_json #>> '{{canonical_chain,outcome,eval_run_id}}')::bigint
            else null::bigint
        end as outcome_eval_run_id,
        coalesce(
            selected_lineage.score_json #> '{{cohort_filter_identity,required_filters}}',
            '{{}}'::jsonb
        ) as cohort_filters
    from selected_lineage
),
referenced_quality as (
    select
        source_eval.eval_run_id,
        source_eval.eval_name,
        source_eval.dataset_version,
        source_eval.provider,
        source_eval.model_name,
        source_eval.score_json,
        source_eval.created_at
    from ai.eval_run source_eval
    join lineage_refs refs on source_eval.eval_run_id = refs.quality_eval_run_id
    where source_eval.eval_name = {sql_literal(SOURCE_QUALITY_EVAL_NAME)}
      and source_eval.dataset_version = {sql_literal(SOURCE_QUALITY_DATASET_VERSION)}
      and source_eval.created_at::date <= {as_of_sql}
      and {source_score_date} is not null
      and {source_score_date} <= {as_of_sql}
    limit 1
),
referenced_outcome as (
    select
        source_eval.eval_run_id,
        source_eval.eval_name,
        source_eval.dataset_version,
        source_eval.provider,
        source_eval.model_name,
        source_eval.score_json,
        source_eval.created_at
    from ai.eval_run source_eval
    join lineage_refs refs on source_eval.eval_run_id = refs.outcome_eval_run_id
    where source_eval.eval_name = {sql_literal(SOURCE_OUTCOME_EVAL_NAME)}
      and source_eval.dataset_version = {sql_literal(SOURCE_OUTCOME_DATASET_VERSION)}
      and source_eval.created_at::date <= {as_of_sql}
      and {source_score_date} is not null
      and {source_score_date} <= {as_of_sql}
    limit 1
),
source_scope as (
    select
        refs.cohort_filters,
        {_render_optional_score_date_expression('quality_eval')} as quality_cutoff,
        {_render_optional_score_date_expression('outcome_eval')} as outcome_cutoff
    from lineage_refs refs
    left join referenced_quality quality_eval on true
    left join referenced_outcome outcome_eval on true
),
recommendation_rows as (
    select
        recommendation.recommendation_id,
        recommendation.batch_id,
        recommendation.instrument_id,
        instrument.primary_symbol,
        recommendation.thesis_id,
        recommendation.bucket,
        recommendation.action,
        recommendation.rank_position,
        recommendation.total_score,
        recommendation.recommended_weight,
        recommendation.status,
        batch.as_of_date as batch_as_of_date,
        batch.market_code,
        batch.strategy_name,
        batch.horizon_type,
        batch.universe_version,
        batch.source_run_id as batch_source_run_id,
        batch.created_at as batch_created_at,
        coalesce(
            (
                select json_agg(
                    json_build_object(
                        'component_name', component.component_name,
                        'component_score', component.component_score,
                        'component_weight', component.component_weight,
                        'explanation', component.explanation,
                        'created_at', component.created_at
                    )
                    order by component.component_name
                )
                from signal.recommendation_score_component component
                where component.recommendation_id = recommendation.recommendation_id
            ),
            '[]'::json
        ) as components
    from signal.recommendation recommendation
    join signal.recommendation_batch batch on batch.batch_id = recommendation.batch_id
    join ref.instrument instrument on instrument.instrument_id = recommendation.instrument_id
    cross join source_scope scope
    where scope.quality_cutoff is not null
      and batch.as_of_date <= scope.quality_cutoff
      and recommendation.status = 'active'
      and coalesce(scope.cohort_filters->>'market_code', '') <> ''
      and coalesce(scope.cohort_filters->>'strategy_name', '') <> ''
      and coalesce(scope.cohort_filters->>'horizon_type', '') <> ''
      and coalesce(scope.cohort_filters->>'universe_version', '') <> ''
      and batch.market_code = scope.cohort_filters->>'market_code'
      and batch.strategy_name = scope.cohort_filters->>'strategy_name'
      and batch.horizon_type = scope.cohort_filters->>'horizon_type'
      and coalesce(batch.universe_version, '') = scope.cohort_filters->>'universe_version'
),
outcome_rows as (
    select
        outcome.outcome_id,
        outcome.recommendation_id,
        outcome.measurement_start_date,
        outcome.measurement_end_date,
        outcome.horizon_days,
        outcome.entry_price,
        outcome.exit_price,
        outcome.absolute_return_pct,
        outcome.benchmark_code,
        outcome.benchmark_return_pct,
        outcome.alpha_pct,
        outcome.max_drawdown_pct,
        outcome.outcome_label,
        outcome.source_run_id,
        outcome.created_at
    from performance.recommendation_outcome outcome
    join recommendation_rows recommendation
      on recommendation.recommendation_id = outcome.recommendation_id
    cross join source_scope scope
    where outcome.measurement_end_date <= greatest(
        coalesce(scope.quality_cutoff, '-infinity'::date),
        coalesce(scope.outcome_cutoff, '-infinity'::date)
    )
),
selected_feedback_calibration as (
    select
        eval_run.eval_run_id,
        eval_run.eval_name,
        eval_run.dataset_version,
        eval_run.provider,
        eval_run.model_name,
        eval_run.score_json,
        eval_run.created_at
    from ai.eval_run eval_run
    where eval_run.eval_name = {sql_literal(SOURCE_FEEDBACK_CALIBRATION_EVAL_NAME)}
      and eval_run.dataset_version = {sql_literal(SOURCE_FEEDBACK_CALIBRATION_DATASET_VERSION)}
      and coalesce(eval_run.score_json->>'portfolio_name', {portfolio_sql}) = {portfolio_sql}
      and eval_run.created_at::date <= {as_of_sql}
      and {feedback_score_date} is not null
      and {feedback_score_date} <= {as_of_sql}{feedback_calibration_id_filter}
    order by
        {feedback_score_date} desc,
        eval_run.created_at desc,
        eval_run.eval_run_id desc
    limit 1
),
feedback_run_refs as (
    select distinct
        case
            when coalesce(run_ref.value->>'eval_run_id', '') ~ '^[1-9][0-9]*$'
                then (run_ref.value->>'eval_run_id')::bigint
            else null::bigint
        end as eval_run_id
    from selected_feedback_calibration calibration
    cross join lateral jsonb_array_elements(
        case
            when jsonb_typeof(calibration.score_json->'latest_feedback_runs') = 'array'
                then calibration.score_json->'latest_feedback_runs'
            else '[]'::jsonb
        end
    ) run_ref(value)
),
referenced_feedback_artifacts as (
    select
        feedback_eval.eval_run_id,
        feedback_eval.eval_name,
        feedback_eval.dataset_version,
        feedback_eval.provider,
        feedback_eval.model_name,
        feedback_eval.score_json,
        feedback_eval.created_at
    from ai.eval_run feedback_eval
    join feedback_run_refs refs on feedback_eval.eval_run_id = refs.eval_run_id
    where feedback_eval.eval_name = {sql_literal(SOURCE_FEEDBACK_EVAL_NAME)}
      and feedback_eval.dataset_version = {sql_literal(SOURCE_FEEDBACK_DATASET_VERSION)}
      and coalesce(feedback_eval.score_json->>'portfolio_name', {portfolio_sql}) = {portfolio_sql}
      and feedback_eval.created_at::date <= {as_of_sql}
      and {feedback_artifact_score_date} is not null
      and {feedback_artifact_score_date} <= {as_of_sql}
)
select json_build_object(
    'lineage', {_render_selected_eval_json('selected_lineage')},
    'referenced_quality', {_render_selected_eval_json('referenced_quality')},
    'referenced_outcome', {_render_selected_eval_json('referenced_outcome')},
    'recommendations', coalesce(
        (
            select json_agg(
                json_build_object(
                    'recommendation_id', recommendation_id,
                    'batch_id', batch_id,
                    'instrument_id', instrument_id,
                    'primary_symbol', primary_symbol,
                    'thesis_id', thesis_id,
                    'bucket', bucket,
                    'action', action,
                    'rank_position', rank_position,
                    'total_score', total_score,
                    'recommended_weight', recommended_weight,
                    'status', status,
                    'batch_as_of_date', batch_as_of_date,
                    'market_code', market_code,
                    'strategy_name', strategy_name,
                    'horizon_type', horizon_type,
                    'universe_version', universe_version,
                    'batch_source_run_id', batch_source_run_id,
                    'batch_created_at', batch_created_at,
                    'components', components
                )
                order by batch_as_of_date, recommendation_id
            )
            from recommendation_rows
        ),
        '[]'::json
    ),
    'outcomes', coalesce(
        (
            select json_agg(
                json_build_object(
                    'outcome_id', outcome_id,
                    'recommendation_id', recommendation_id,
                    'measurement_start_date', measurement_start_date,
                    'measurement_end_date', measurement_end_date,
                    'horizon_days', horizon_days,
                    'entry_price', entry_price,
                    'exit_price', exit_price,
                    'absolute_return_pct', absolute_return_pct,
                    'benchmark_code', benchmark_code,
                    'benchmark_return_pct', benchmark_return_pct,
                    'alpha_pct', alpha_pct,
                    'max_drawdown_pct', max_drawdown_pct,
                    'outcome_label', outcome_label,
                    'source_run_id', source_run_id,
                    'created_at', created_at
                )
                order by recommendation_id, measurement_end_date, outcome_id
            )
            from outcome_rows
        ),
        '[]'::json
    ),
    'feedback_calibration', {_render_selected_eval_json('selected_feedback_calibration')},
    'feedback_artifacts', coalesce(
        (
            select json_agg(
                json_build_object(
                    'eval_run_id', eval_run_id,
                    'eval_name', eval_name,
                    'dataset_version', dataset_version,
                    'provider', provider,
                    'model_name', model_name,
                    'score_json', score_json,
                    'created_at', created_at
                )
                order by created_at desc, eval_run_id desc
            )
            from referenced_feedback_artifacts
        ),
        '[]'::json
    )
)::text;"""


def render_prospective_evidence_foundation_eval_insert_sql(
    *,
    score_json: dict[str, object],
) -> str:
    score_text = json.dumps(
        score_json,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
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


def load_prospective_evidence_bundle(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    lineage_eval_run_id: int | None = None,
    portfolio_feedback_calibration_eval_run_id: int | None = None,
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_prospective_evidence_bundle_lookup_sql(
                as_of_date=as_of_date,
                lineage_eval_run_id=lineage_eval_run_id,
                portfolio_feedback_calibration_eval_run_id=(
                    portfolio_feedback_calibration_eval_run_id
                ),
                portfolio_name=portfolio_name,
            )
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Prospective evidence lookup did not return a JSON object.")
    return payload


def _render_optional_score_date_expression(alias: str) -> str:
    value = f"{alias}.score_json->>'as_of_date'"
    return (
        "case "
        f"when coalesce({value}, '') ~ "
        "'^[0-9]{4}-(0[1-9]|1[0-2])-([0-2][0-9]|3[0-1])$' "
        f"and to_char(to_date({value}, 'YYYY-MM-DD'), 'YYYY-MM-DD') = {value} "
        f"then to_date({value}, 'YYYY-MM-DD') "
        "else null::date end"
    )


def _render_selected_eval_json(cte_name: str) -> str:
    return f"""coalesce(
        (
            select json_build_object(
                'eval_run_id', {cte_name}.eval_run_id,
                'eval_name', {cte_name}.eval_name,
                'dataset_version', {cte_name}.dataset_version,
                'provider', {cte_name}.provider,
                'model_name', {cte_name}.model_name,
                'score_json', {cte_name}.score_json,
                'created_at', {cte_name}.created_at
            )
            from {cte_name}
        ),
        '{{}}'::json
    )"""
