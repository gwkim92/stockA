-- Source: develop d7ad05c; equity blob 634348bea83db09e56dc1eb60d23129d69cb7585
-- equity research context lookup
with target as (
    select
        instrument.instrument_id,
        instrument.primary_symbol,
        instrument.name,
        instrument.market_code,
        instrument.currency_code
    from ref.instrument instrument
    where upper(instrument.primary_symbol) = 'AAPL'
      and instrument.is_active = true
    order by instrument.instrument_id desc
    limit 1
),
latest_financial_metrics as (
    select distinct on (normalized.metric_code)
        normalized.metric_code,
        normalized.metric_value,
        normalized.metric_unit,
        normalized.metric_status,
        normalized.rationale,
        normalized.statement_scope,
        normalized.period_end,
        normalized.source_run_id
    from market.financial_metric_normalized normalized
    join target on target.instrument_id = normalized.instrument_id
    where normalized.as_of_date <= '2026-09-05'::date
      and normalized.statement_scope = 'annual'
    order by normalized.metric_code, normalized.as_of_date desc, normalized.period_end desc
),
financial_metric_status_counts as (
    select
        metric_status,
        count(*)::integer as metric_count
    from latest_financial_metrics
    group by metric_status
),
latest_peer_rows as (
    select distinct on (snapshot.metric_code)
        peer_group.group_code as peer_group_code,
        peer_group.name as peer_group_name,
        snapshot.metric_code,
        snapshot.instrument_value as metric_value,
        snapshot.percentile_rank,
        snapshot.relative_signal,
        snapshot.as_of_date,
        snapshot.source_run_id
    from market.peer_relative_snapshot snapshot
    join target on target.instrument_id = snapshot.instrument_id
    join ref.peer_group peer_group on peer_group.peer_group_id = snapshot.peer_group_id
    where snapshot.as_of_date <= '2026-09-05'::date
    order by snapshot.metric_code, snapshot.as_of_date desc, snapshot.peer_snapshot_id desc
),
latest_valuation_rows as (
    select distinct on (valuation.method)
        valuation.method,
        valuation.base_price,
        valuation.fair_value_low,
        valuation.fair_value_base,
        valuation.fair_value_high,
        valuation.margin_of_safety,
        valuation.assumptions_json,
        valuation.confidence,
        valuation.as_of_date,
        valuation.source_run_id
    from market.valuation_snapshot valuation
    join target on target.instrument_id = valuation.instrument_id
    where valuation.as_of_date <= '2026-09-05'::date
    order by valuation.method, valuation.as_of_date desc, valuation.valuation_snapshot_id desc
),
latest_recommendation as (
    select
        recommendation.recommendation_id,
        batch.as_of_date,
        batch.strategy_name,
        batch.horizon_type,
        recommendation.action,
        recommendation.bucket,
        recommendation.rank_position,
        recommendation.total_score,
        recommendation.recommended_weight,
        recommendation.status,
        recommendation.thesis_id,
        batch.source_run_id
    from signal.recommendation recommendation
    join signal.recommendation_batch batch on batch.batch_id = recommendation.batch_id
    join target on target.instrument_id = recommendation.instrument_id
    where batch.as_of_date <= '2026-09-05'::date
    order by batch.as_of_date desc, recommendation.recommendation_id desc
    limit 1
),
fundamental_components as (
    select
        component.component_name,
        component.component_score,
        component.component_weight,
        component.explanation
    from signal.recommendation_score_component component
    join latest_recommendation recommendation on recommendation.recommendation_id = component.recommendation_id
    where component.component_name in (
        'fundamental_quality_score',
        'valuation_margin_score',
        'peer_relative_score',
        'balance_sheet_risk_penalty',
        'thesis_consistency_score'
    )
    order by component.component_name
),
latest_thesis as (
    select
        thesis.thesis_id,
        thesis.title,
        thesis.summary,
        thesis.status,
        thesis.conviction_score,
        thesis.expected_holding_days,
        thesis.benchmark_code,
        thesis.entry_conditions,
        thesis.invalidation_conditions,
        thesis.exit_conditions,
        thesis.created_by_run_id
    from signal.investment_thesis thesis
    join target on target.instrument_id = thesis.instrument_id
    order by
        case when thesis.thesis_id = (select thesis_id from latest_recommendation) then 0 else 1 end,
        case when thesis.status = 'active' then 0 else 1 end,
        thesis.created_at desc,
        thesis.thesis_id desc
    limit 1
),
recent_events as (
    select
        event_row.event_id,
        event_row.title,
        event_row.summary,
        event_row.event_at,
        impact.impact_direction,
        impact.impact_strength,
        coalesce(impact.confidence, event_row.confidence) as confidence,
        impact.rationale,
        source_document.document_id,
        source_document.korean_title,
        source_document.korean_summary,
        source_document.translation_confidence,
        source_document.url
    from target
    join event.event_instrument_impact impact on impact.instrument_id = target.instrument_id
    join event.event event_row on event_row.event_id = impact.event_id
    left join event.event_document_link document_link
      on document_link.event_id = event_row.event_id
     and document_link.link_type = 'source'
    left join ingest.source_document source_document on source_document.document_id = document_link.document_id
    where event_row.event_at <= ('2026-09-05'::date::date + interval '1 day')
    order by event_row.event_at desc, event_row.event_id desc
    limit 50
),
cycle_summaries as (
    select
        node.code as node_code,
        node.name as node_name,
        summary.summary_type,
        summary.summary_json,
        summary.as_of_date,
        summary.source_run_id
    from target
    join ref.instrument_classification_membership membership on membership.instrument_id = target.instrument_id
    join ref.classification_node node on node.node_id = membership.node_id
    left join lateral (
        select summary.*
        from ai.cycle_community_summary summary
        where summary.node_id = node.node_id
          and summary.as_of_date <= '2026-09-05'::date
        order by summary.as_of_date desc, summary.updated_at desc
        limit 1
    ) summary on true
    where membership.valid_from <= '2026-09-05'::date
      and (membership.valid_to is null or membership.valid_to >= '2026-09-05'::date)
    order by coalesce(membership.confidence, 0) desc, node.code
    limit 50
)
select json_build_object(
    'query', json_build_object('symbol', 'AAPL', 'as_of_date', '2026-09-05', 'limit', 50),
    'instrument', (select row_to_json(target) from target),
    'financial_metrics', coalesce((select json_agg(row_to_json(latest_financial_metrics) order by metric_code) from latest_financial_metrics), '[]'::json),
    'financial_metric_status_counts', coalesce((select json_agg(row_to_json(financial_metric_status_counts) order by metric_status) from financial_metric_status_counts), '[]'::json),
    'peer_relative', coalesce((select json_agg(row_to_json(latest_peer_rows) order by metric_code) from latest_peer_rows), '[]'::json),
    'valuations', coalesce((select json_agg(row_to_json(latest_valuation_rows) order by method) from latest_valuation_rows), '[]'::json),
    'recommendation', (select row_to_json(latest_recommendation) from latest_recommendation),
    'fundamental_components', coalesce((select json_agg(row_to_json(fundamental_components) order by component_name) from fundamental_components), '[]'::json),
    'thesis', (select row_to_json(latest_thesis) from latest_thesis),
    'recent_events', coalesce((select json_agg(row_to_json(recent_events) order by event_at desc, event_id desc) from recent_events), '[]'::json),
    'cycle_summaries', coalesce((select json_agg(row_to_json(cycle_summaries) order by node_code) from cycle_summaries), '[]'::json)
)::text;
