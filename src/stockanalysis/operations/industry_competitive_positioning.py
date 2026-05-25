from __future__ import annotations

import json
from datetime import date

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_PIPELINE_NAME = "industry_competitive_positioning"
DEFAULT_MODEL_NAME = "deterministic-industry-competitive-positioning-v1"
DEFAULT_METHODOLOGY = "peer-financial-porter-proxy-v1"
DEFAULT_MIN_METRIC_COVERAGE = 3


def render_industry_competitive_positioning_preview_sql(
    *,
    as_of_date: date,
    min_metric_coverage: int = DEFAULT_MIN_METRIC_COVERAGE,
) -> str:
    _validate_args(min_metric_coverage=min_metric_coverage)
    return f"""-- industry competitive positioning preview
with active_peer_members as (
    select
        member.peer_group_id,
        member.instrument_id
    from ref.peer_group_member member
    join ref.peer_group peer_group on peer_group.peer_group_id = member.peer_group_id
    where peer_group.status = 'active'
      and member.valid_from <= {sql_date(as_of_date)}
      and (member.valid_to is null or member.valid_to >= {sql_date(as_of_date)})
),
latest_peer_rows as (
    select distinct on (snapshot.instrument_id, snapshot.peer_group_id, snapshot.metric_code)
        snapshot.instrument_id,
        snapshot.peer_group_id,
        snapshot.metric_code,
        snapshot.percentile_rank
    from market.peer_relative_snapshot snapshot
    join active_peer_members member
      on member.instrument_id = snapshot.instrument_id
     and member.peer_group_id = snapshot.peer_group_id
    where snapshot.as_of_date <= {sql_date(as_of_date)}
      and snapshot.relative_signal <> 'insufficient_data'
    order by
        snapshot.instrument_id,
        snapshot.peer_group_id,
        snapshot.metric_code,
        snapshot.as_of_date desc,
        snapshot.peer_snapshot_id desc
),
existing_positions as (
    select *
    from research.industry_competitive_position position
    where position.as_of_date = {sql_date(as_of_date)}
      and position.methodology = {sql_literal(DEFAULT_METHODOLOGY)}
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'model_name', {sql_literal(DEFAULT_MODEL_NAME)},
    'methodology', {sql_literal(DEFAULT_METHODOLOGY)},
    'min_metric_coverage', {int(min_metric_coverage)},
    'candidate_instrument_count', (select count(distinct instrument_id)::integer from active_peer_members),
    'candidate_peer_group_count', (select count(distinct peer_group_id)::integer from active_peer_members),
    'latest_peer_metric_count', (select count(*)::integer from latest_peer_rows),
    'existing_position_count', (select count(*)::integer from existing_positions)
)::text;"""


def render_industry_competitive_positioning_upsert_sql(
    *,
    as_of_date: date,
    source_run_id: int,
    min_metric_coverage: int = DEFAULT_MIN_METRIC_COVERAGE,
) -> str:
    _validate_args(min_metric_coverage=min_metric_coverage)
    source_run = f"{int(source_run_id)}::bigint"
    return f"""-- industry competitive positioning upsert
with active_peer_members as (
    select
        member.peer_group_id,
        peer_group.group_code,
        peer_group.name as peer_group_name,
        member.instrument_id
    from ref.peer_group_member member
    join ref.peer_group peer_group on peer_group.peer_group_id = member.peer_group_id
    where peer_group.status = 'active'
      and member.valid_from <= {sql_date(as_of_date)}
      and (member.valid_to is null or member.valid_to >= {sql_date(as_of_date)})
),
peer_counts as (
    select
        peer_group_id,
        count(distinct instrument_id)::integer as peer_count
    from active_peer_members
    group by peer_group_id
),
latest_peer_rows as (
    select distinct on (snapshot.instrument_id, snapshot.peer_group_id, snapshot.metric_code)
        snapshot.instrument_id,
        snapshot.peer_group_id,
        snapshot.metric_code,
        snapshot.percentile_rank
    from market.peer_relative_snapshot snapshot
    join active_peer_members member
      on member.instrument_id = snapshot.instrument_id
     and member.peer_group_id = snapshot.peer_group_id
    where snapshot.as_of_date <= {sql_date(as_of_date)}
      and snapshot.relative_signal <> 'insufficient_data'
    order by
        snapshot.instrument_id,
        snapshot.peer_group_id,
        snapshot.metric_code,
        snapshot.as_of_date desc,
        snapshot.peer_snapshot_id desc
),
sector_membership as (
    select distinct on (membership.instrument_id)
        membership.instrument_id,
        node.node_id as sector_node_id,
        node.code as sector_code,
        node.name as sector_name
    from ref.instrument_classification_membership membership
    join ref.classification_node node on node.node_id = membership.node_id
    where membership.membership_type = 'sector_membership'
      and node.taxonomy_family = 'internal_theme'
      and node.node_type = 'sector'
      and node.status = 'active'
      and membership.valid_from <= {sql_date(as_of_date)}
      and (membership.valid_to is null or membership.valid_to >= {sql_date(as_of_date)})
    order by membership.instrument_id, membership.confidence desc nulls last, membership.valid_from desc
),
metric_inputs as (
    select
        member.instrument_id,
        member.peer_group_id,
        member.group_code,
        member.peer_group_name,
        count(row.metric_code)::integer as metric_coverage_count,
        avg(row.percentile_rank) filter (
            where row.metric_code in ('gross_margin', 'operating_margin')
        ) as pricing_power_raw,
        avg(row.percentile_rank) filter (
            where row.metric_code in ('operating_margin', 'net_margin', 'free_cash_flow_margin', 'roe')
        ) as profitability_raw,
        avg(row.percentile_rank) filter (
            where row.metric_code = 'revenue_growth_yoy'
        ) as growth_position_raw,
        avg(
            case
                when row.metric_code in ('leverage_ratio', 'liabilities_to_assets') then 1::numeric - row.percentile_rank
                when row.metric_code = 'accrual_ratio' then 1::numeric - row.percentile_rank
                else null::numeric
            end
        ) as financial_strength_raw,
        avg(row.percentile_rank) filter (
            where row.metric_code = 'capex_intensity'
        ) as capacity_cycle_risk_raw
    from active_peer_members member
    left join latest_peer_rows row
      on row.instrument_id = member.instrument_id
     and row.peer_group_id = member.peer_group_id
    group by
        member.instrument_id,
        member.peer_group_id,
        member.group_code,
        member.peer_group_name
),
scored_inputs as (
    select
        input.instrument_id,
        input.peer_group_id,
        input.group_code,
        input.peer_group_name,
        sector.sector_node_id,
        sector.sector_code,
        sector.sector_name,
        coalesce(peer_counts.peer_count, 0)::integer as peer_count,
        input.metric_coverage_count,
        (coalesce(input.pricing_power_raw, 0.5000))::numeric(5,4) as pricing_power_score,
        (coalesce(input.profitability_raw, 0.5000))::numeric(5,4) as profitability_score,
        (coalesce(input.growth_position_raw, 0.5000))::numeric(5,4) as growth_position_score,
        (coalesce(input.financial_strength_raw, 0.5000))::numeric(5,4) as financial_strength_score,
        (coalesce(input.capacity_cycle_risk_raw, 0.5000))::numeric(5,4) as capacity_cycle_risk_score,
        case
            when coalesce(peer_counts.peer_count, 0) >= 8 then 0.7500::numeric
            when coalesce(peer_counts.peer_count, 0) >= 4 then 0.6000::numeric
            when coalesce(peer_counts.peer_count, 0) >= 2 then 0.4500::numeric
            else null::numeric
        end as rivalry_risk_score
    from metric_inputs input
    join peer_counts on peer_counts.peer_group_id = input.peer_group_id
    left join sector_membership sector on sector.instrument_id = input.instrument_id
),
candidate_rows as (
    select
        score.instrument_id,
        score.peer_group_id,
        score.sector_node_id,
        {sql_date(as_of_date)} as as_of_date,
        {sql_literal(DEFAULT_METHODOLOGY)} as methodology,
        case
            when score.peer_count < 2 or score.metric_coverage_count < {int(min_metric_coverage)} then 'insufficient_data'
            when moat.moat_score >= 0.7500 then 'leader'
            when moat.moat_score >= 0.6000 then 'advantaged'
            when moat.moat_score >= 0.4000 then 'in_line'
            else 'challenged'
        end as competitive_position,
        case when score.peer_count >= 2 and score.metric_coverage_count >= {int(min_metric_coverage)} then moat.moat_score else null::numeric end as moat_score,
        case when score.metric_coverage_count > 0 then score.pricing_power_score else null::numeric end as pricing_power_score,
        case when score.metric_coverage_count > 0 then score.profitability_score else null::numeric end as profitability_score,
        case when score.metric_coverage_count > 0 then score.growth_position_score else null::numeric end as growth_position_score,
        case when score.metric_coverage_count > 0 then score.financial_strength_score else null::numeric end as financial_strength_score,
        score.rivalry_risk_score,
        case when score.metric_coverage_count > 0 then (1::numeric - score.pricing_power_score)::numeric(5,4) else null::numeric end as buyer_power_risk_score,
        case when score.metric_coverage_count > 0 then (1::numeric - score.profitability_score)::numeric(5,4) else null::numeric end as supplier_power_risk_score,
        case when score.metric_coverage_count > 0 then (1::numeric - score.growth_position_score)::numeric(5,4) else null::numeric end as substitute_threat_risk_score,
        case
            when score.metric_coverage_count = 0 then null::numeric
            when score.pricing_power_score >= 0.7000 and score.profitability_score >= 0.7000 then 0.3500::numeric
            when score.pricing_power_score <= 0.3500 or score.profitability_score <= 0.3500 then 0.7000::numeric
            else 0.5500::numeric
        end as new_entry_threat_risk_score,
        case when score.metric_coverage_count > 0 then score.capacity_cycle_risk_score else null::numeric end as capacity_cycle_risk_score,
        score.metric_coverage_count,
        score.peer_count,
        to_jsonb(array_remove(array[
            case when score.pricing_power_score >= 0.6500 then '피어 대비 마진 위치가 높아 가격 결정력 proxy가 우호적이다.' end,
            case when score.profitability_score >= 0.6500 then '피어 대비 수익성 지표가 높아 운영 경쟁력이 우호적이다.' end,
            case when score.financial_strength_score >= 0.6500 then '부채와 발생액 proxy가 낮아 재무 방어력이 우호적이다.' end,
            case when score.growth_position_score >= 0.6500 then '피어 대비 성장 위치가 높아 수요/제품 포지션이 우호적이다.' end
        ], null)) as key_strengths_json,
        to_jsonb(array_remove(array[
            case when score.rivalry_risk_score >= 0.7000 then '피어 수가 많아 경쟁 강도가 높을 수 있다.' end,
            case when (1::numeric - score.pricing_power_score) >= 0.6500 then '마진 위치가 낮아 구매자 교섭력 또는 가격 압박을 점검해야 한다.' end,
            case when score.capacity_cycle_risk_score >= 0.6500 then 'CAPEX intensity가 높아 capacity cycle 리스크를 점검해야 한다.' end,
            case when (1::numeric - score.growth_position_score) >= 0.6500 then '성장 위치가 낮아 대체재/수요 둔화 리스크를 점검해야 한다.' end
        ], null)) as key_risks_json,
        jsonb_strip_nulls(jsonb_build_object(
            'peer_group_code', score.group_code,
            'peer_group_name', score.peer_group_name,
            'peer_count', score.peer_count,
            'metric_coverage_count', score.metric_coverage_count,
            'sector_code', score.sector_code,
            'sector_name', score.sector_name,
            'methodology_note', 'Deterministic proxy from peer percentile ranks; not a paid market-share dataset or final analyst judgment.'
        )) as peer_context_json,
        case
            when score.peer_count < 2 then 'Peer group has fewer than two active members; competitive position remains insufficient data.'
            when score.metric_coverage_count < {int(min_metric_coverage)} then 'Peer financial metric coverage is below threshold; competitive position remains insufficient data.'
            else 'Competitive position is a deterministic proxy from pricing power, profitability, growth, financial strength, and capacity-cycle risk.'
        end as rationale
    from scored_inputs score
    cross join lateral (
        select (
            (
                score.pricing_power_score
                + score.profitability_score
                + score.growth_position_score
                + score.financial_strength_score
            ) / 4.0000::numeric
        )::numeric(5,4) as moat_score
    ) moat
),
upserted as (
    insert into research.industry_competitive_position (
        instrument_id,
        peer_group_id,
        sector_node_id,
        as_of_date,
        methodology,
        competitive_position,
        moat_score,
        pricing_power_score,
        profitability_score,
        growth_position_score,
        financial_strength_score,
        rivalry_risk_score,
        buyer_power_risk_score,
        supplier_power_risk_score,
        substitute_threat_risk_score,
        new_entry_threat_risk_score,
        capacity_cycle_risk_score,
        metric_coverage_count,
        peer_count,
        key_strengths_json,
        key_risks_json,
        peer_context_json,
        rationale,
        source_run_id
    )
    select
        instrument_id,
        peer_group_id,
        sector_node_id,
        as_of_date,
        methodology,
        competitive_position,
        moat_score,
        pricing_power_score,
        profitability_score,
        growth_position_score,
        financial_strength_score,
        rivalry_risk_score,
        buyer_power_risk_score,
        supplier_power_risk_score,
        substitute_threat_risk_score,
        new_entry_threat_risk_score,
        capacity_cycle_risk_score,
        metric_coverage_count,
        peer_count,
        key_strengths_json,
        key_risks_json,
        peer_context_json,
        rationale,
        {source_run}
    from candidate_rows
    on conflict (instrument_id, peer_group_id, as_of_date, methodology) do update
    set
        sector_node_id = excluded.sector_node_id,
        competitive_position = excluded.competitive_position,
        moat_score = excluded.moat_score,
        pricing_power_score = excluded.pricing_power_score,
        profitability_score = excluded.profitability_score,
        growth_position_score = excluded.growth_position_score,
        financial_strength_score = excluded.financial_strength_score,
        rivalry_risk_score = excluded.rivalry_risk_score,
        buyer_power_risk_score = excluded.buyer_power_risk_score,
        supplier_power_risk_score = excluded.supplier_power_risk_score,
        substitute_threat_risk_score = excluded.substitute_threat_risk_score,
        new_entry_threat_risk_score = excluded.new_entry_threat_risk_score,
        capacity_cycle_risk_score = excluded.capacity_cycle_risk_score,
        metric_coverage_count = excluded.metric_coverage_count,
        peer_count = excluded.peer_count,
        key_strengths_json = excluded.key_strengths_json,
        key_risks_json = excluded.key_risks_json,
        peer_context_json = excluded.peer_context_json,
        rationale = excluded.rationale,
        source_run_id = excluded.source_run_id,
        updated_at = now()
    returning competitive_position
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'source_run_id', {int(source_run_id)},
    'methodology', {sql_literal(DEFAULT_METHODOLOGY)},
    'position_count', (select count(*)::integer from upserted),
    'competitive_position_counts',
        coalesce(
            (
                select json_object_agg(competitive_position, position_count order by competitive_position)
                from (
                    select competitive_position, count(*)::integer as position_count
                    from upserted
                    group by competitive_position
                ) counts
            ),
            '{{}}'::json
        ),
    'recommendation_scoring_mutated', false
)::text;"""


def load_industry_competitive_positioning_preview(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    min_metric_coverage: int = DEFAULT_MIN_METRIC_COVERAGE,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_industry_competitive_positioning_preview_sql(
                as_of_date=as_of_date,
                min_metric_coverage=min_metric_coverage,
            )
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Industry competitive positioning preview did not return a JSON object.")
    return payload


def run_industry_competitive_positioning(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    min_metric_coverage: int = DEFAULT_MIN_METRIC_COVERAGE,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    preview = load_industry_competitive_positioning_preview(
        config=config,
        as_of_date=as_of_date,
        min_metric_coverage=min_metric_coverage,
        executor=sql_executor,
    )
    report: dict[str, object] = {
        "report_name": "industry_competitive_positioning",
        "status": "planned" if not execute else "running",
        "execute": execute,
        "pipeline_name": DEFAULT_PIPELINE_NAME,
        "as_of_date": as_of_date.isoformat(),
        "model_name": DEFAULT_MODEL_NAME,
        "methodology": DEFAULT_METHODOLOGY,
        "min_metric_coverage": min_metric_coverage,
        "preview": preview,
        "recommendation_scoring_mutated": False,
        "broker_submission_allowed": False,
    }
    if not execute:
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "model_name": DEFAULT_MODEL_NAME,
            "methodology": DEFAULT_METHODOLOGY,
            "min_metric_coverage": min_metric_coverage,
            "recommendation_scoring_mutated": False,
        },
    )
    try:
        upsert_summary = json.loads(
            sql_executor.execute_scalar(
                render_industry_competitive_positioning_upsert_sql(
                    as_of_date=as_of_date,
                    source_run_id=run_id,
                    min_metric_coverage=min_metric_coverage,
                )
            )
        )
        if not isinstance(upsert_summary, dict):
            raise ValueError("Industry competitive positioning upsert did not return a JSON object.")
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return {
        **report,
        "status": "completed",
        "run_id": run_id,
        "upsert": upsert_summary,
    }


def _validate_args(*, min_metric_coverage: int) -> None:
    if min_metric_coverage < 1 or min_metric_coverage > 20:
        raise ValueError("min_metric_coverage must be between 1 and 20.")
