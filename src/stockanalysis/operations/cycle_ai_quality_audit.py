from __future__ import annotations

import json
from collections.abc import Mapping as MappingABC
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Mapping

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_date, sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations.path_policy import resolve_existing_file
from stockanalysis.signal.universe import (
    _create_pipeline_run,
    _mark_pipeline_run_failed,
    _mark_pipeline_run_succeeded,
)


DEFAULT_PIPELINE_NAME = "cycle_ai_quality_audit"
STALE_DIRECT_IMPACT_CLEANUP_PIPELINE_NAME = "cycle_ai_stale_direct_impact_cleanup"
DUPLICATE_TITLE_CLEANUP_PIPELINE_NAME = "cycle_ai_duplicate_title_cleanup"
CYCLE_AI_QUALITY_AUDIT_REPORT_ENV = "STOCKANALYSIS_CYCLE_AI_QUALITY_AUDIT_REPORT"


def render_cycle_ai_quality_audit_sql(*, as_of_date: date, lookback_days: int = 30) -> str:
    if lookback_days < 1 or lookback_days > 120:
        raise ValueError("lookback_days must be between 1 and 120.")
    target_date = sql_date(as_of_date)
    lookback_interval = f"interval '{lookback_days} days'"
    return f"""-- cycle ai quality audit lookup
with windowed_documents as (
    select
        document.document_id,
        document.title,
        document.summary,
        document.korean_title,
        document.korean_summary,
        document.translation_confidence,
        document.published_at,
        document.ingested_at,
        document.url
    from ingest.source_document document
    where document.document_type = 'news_rss_item'
      and coalesce(document.published_at, document.ingested_at) >= ({target_date} - {lookback_interval})
      and coalesce(document.published_at, document.ingested_at) < ({target_date} + interval '1 day')
),
windowed_events as (
    select event_row.*
    from event.event event_row
    where event_row.event_at >= ({target_date} - {lookback_interval})
      and event_row.event_at < ({target_date} + interval '1 day')
),
event_documents as (
    select distinct
        link.event_id,
        document.document_id,
        document.title,
        document.summary,
        document.korean_title,
        document.korean_summary,
        document.translation_confidence,
        document.url
    from windowed_events event_row
    join event.event_document_link link on link.event_id = event_row.event_id
    join ingest.source_document document on document.document_id = link.document_id
    where link.link_type = 'source'
),
classification_impacts as (
    select
        impact.event_id,
        node.node_id,
        node.code as node_code,
        node.node_type,
        impact.impact_direction,
        impact.impact_strength,
        impact.confidence,
        left(coalesce(document.korean_title, document.title, event_row.title, ''), 220) as event_title,
        upper(
            coalesce(document.title, event_row.title, '') || ' ' ||
            coalesce(document.summary, event_row.summary, '')
        ) as source_text_upper
    from event.event_classification_impact impact
    join windowed_events event_row on event_row.event_id = impact.event_id
    join ref.classification_node node on node.node_id = impact.node_id
    left join event_documents document on document.event_id = impact.event_id
),
source_aliases(primary_symbol, alias_text) as (
    values
        ('SPY', 's&p 500'),
        ('SPY', 's&p500'),
        ('SPY', 'spx'),
        ('QQQ', 'nasdaq 100'),
        ('QQQ', 'nasdaq futures'),
        ('QQQ', 'nasdaq'),
        ('XLE', 'energy sector')
),
direct_impacts as (
    select
        impact.event_id,
        impact.instrument_id,
        instrument.primary_symbol,
        instrument.name as instrument_name,
        impact.impact_direction,
        impact.impact_strength,
        impact.confidence,
        left(coalesce(document.korean_title, document.title, event_row.title, ''), 220) as event_title,
        source_text.source_text_upper,
        case
            when position(' ' || lower(instrument.primary_symbol) || ' ' in source_text.source_text_normalized) > 0 then true
            when exists (
                select 1
                from source_aliases alias
                where alias.primary_symbol = upper(instrument.primary_symbol)
                  and position(
                      ' ' || btrim(regexp_replace(lower(alias.alias_text), '[^a-z0-9]+', ' ', 'g')) || ' '
                      in source_text.source_text_normalized
                  ) > 0
            ) then true
            when exists (
                select 1
                from regexp_split_to_table(instrument.name, '[^A-Za-z0-9]+') as token(value)
                where length(lower(token.value)) >= 4
                  and lower(token.value) not in (
                      'class',
                      'company',
                      'corp',
                      'corporation',
                      'group',
                      'holding',
                      'holdings',
                      'inc',
                      'ltd',
                      'plc',
                      'shares',
                      'stock',
                      'trust'
                  )
                  and position(' ' || lower(token.value) || ' ' in source_text.source_text_normalized) > 0
            ) then true
            else false
        end as is_grounded
    from event.event_instrument_impact impact
    join windowed_events event_row on event_row.event_id = impact.event_id
    join ref.instrument instrument on instrument.instrument_id = impact.instrument_id
    left join event_documents document on document.event_id = impact.event_id
    cross join lateral (
        select
            upper(
                coalesce(document.title, event_row.title, '') || ' ' ||
                coalesce(document.summary, event_row.summary, '')
            ) as source_text_upper,
            ' ' || btrim(regexp_replace(
                lower(
                    coalesce(document.title, event_row.title, '') || ' ' ||
                    coalesce(document.summary, event_row.summary, '')
                ),
                '[^a-z0-9]+',
                ' ',
                'g'
            )) || ' ' as source_text_normalized
    ) source_text
),
duplicate_titles as (
    select
        lower(regexp_replace(title, '\\s+', ' ', 'g')) as normalized_title,
        count(*)::integer as repeated_count,
        array_agg(document_id order by coalesce(published_at, ingested_at) desc, document_id desc) as document_ids
    from windowed_documents
    where title is not null and btrim(title) <> ''
    group by lower(regexp_replace(title, '\\s+', ' ', 'g'))
    having count(*) > 1
),
ungrounded_direct_tickers as (
    select
        event_id,
        instrument_id,
        primary_symbol,
        instrument_name,
        max(event_title) as event_title
    from direct_impacts
    where is_grounded = false
    group by event_id, instrument_id, primary_symbol, instrument_name
),
macro_false_tickers as (
    select
        direct_impacts.event_id,
        direct_impacts.instrument_id,
        direct_impacts.primary_symbol,
        direct_impacts.instrument_name,
        max(direct_impacts.event_title) as event_title,
        array_agg(distinct classification_impacts.node_code order by classification_impacts.node_code) as node_codes,
        max(classification_impacts.impact_direction) as impact_direction
    from direct_impacts
    join classification_impacts on classification_impacts.event_id = direct_impacts.event_id
    where direct_impacts.is_grounded = false
      and (
          classification_impacts.node_code like 'MACRO_%'
          or classification_impacts.node_code in ('MACRO_RATES_FED', 'MACRO_INFLATION', 'MACRO_LIQUIDITY', 'MACRO_GROWTH')
      )
    group by direct_impacts.event_id, direct_impacts.instrument_id, direct_impacts.primary_symbol, direct_impacts.instrument_name
),
quantum_energy_mislinks as (
    select distinct classification_impacts.event_id, classification_impacts.node_code
    from classification_impacts
    where classification_impacts.source_text_upper ~ '(QUANTUM|QUBIT)'
      and classification_impacts.node_code in ('ENERGY_GEOPOLITICS', 'ENERGY_DOMAIN', 'ENERGY_CYCLE', 'XLE_ENERGY')
    union
    select distinct direct_impacts.event_id, direct_impacts.primary_symbol as node_code
    from direct_impacts
    where direct_impacts.source_text_upper ~ '(QUANTUM|QUBIT)'
      and direct_impacts.primary_symbol in ('XLE', 'XOM')
),
normal_macro_flows as (
    select
        classification_impacts.event_id,
        max(classification_impacts.event_title) as event_title,
        array_agg(distinct classification_impacts.node_code order by classification_impacts.node_code) as node_codes,
        array_agg(distinct classification_impacts.impact_direction order by classification_impacts.impact_direction) as impact_directions
    from classification_impacts
    left join direct_impacts on direct_impacts.event_id = classification_impacts.event_id
    where direct_impacts.event_id is null
      and (
          classification_impacts.node_code like 'MACRO_%'
          or classification_impacts.node_type in ('macro', 'domain', 'theme')
      )
    group by classification_impacts.event_id
),
artifact_counts as (
    select
        count(*) filter (where artifact.artifact_type = 'news_event_candidate')::integer as accepted_artifact_count,
        count(*) filter (where artifact.artifact_type = 'news_event_candidate_rejected')::integer as rejected_artifact_count,
        count(*) filter (where artifact.artifact_type = 'news_cluster_summary')::integer as cluster_artifact_count
    from ai.extraction_artifact artifact
    where artifact.created_at >= ({target_date} - {lookback_interval})
      and artifact.created_at < ({target_date} + interval '1 day')
),
invocation_counts as (
    select
        count(*) filter (where invocation.provider = 'codex_oauth')::integer as codex_invocation_count,
        count(*) filter (where invocation.provider = 'codex_oauth' and invocation.status = 'succeeded')::integer as codex_succeeded_count,
        count(*) filter (where invocation.provider = 'codex_oauth' and invocation.status <> 'succeeded')::integer as codex_failed_count
    from ai.model_invocation invocation
    where invocation.created_at >= ({target_date} - {lookback_interval})
      and invocation.created_at < ({target_date} + interval '1 day')
),
hierarchical_counts as (
    select count(*)::integer as hierarchical_impact_count
    from signal.hierarchical_propagated_instrument_impact propagated
    join windowed_events event_row on event_row.event_id = propagated.event_id
),
cycle_counts as (
    select count(*)::integer as cycle_snapshot_count
    from signal.cycle_hierarchy_state_snapshot snapshot
    where snapshot.as_of_date = {target_date}
),
recommendation_counts as (
    select count(*)::integer as recommendation_cycle_component_count
    from signal.recommendation_score_component component
    join signal.recommendation recommendation on recommendation.recommendation_id = component.recommendation_id
    join signal.recommendation_batch batch on batch.batch_id = recommendation.batch_id
    where batch.as_of_date <= {target_date}
      and component.component_name in (
          'macro_regime_score',
          'domain_cycle_score',
          'theme_cycle_score',
          'instrument_cycle_score',
          'macro_flow_score',
          'cycle_conflict_penalty'
      )
),
paper_counts as (
    select
        count(*)::integer as paper_validation_count,
        count(*) filter (where status = 'passed')::integer as paper_validation_passed_count
    from trading.paper_validation_run validation
    where validation.validation_date <= {target_date}
),
metrics as (
    select
        (select count(*)::integer from windowed_documents) as rss_document_count,
        (select count(*)::integer from windowed_documents where korean_title is not null and korean_summary is not null) as translated_document_count,
        coalesce((select accepted_artifact_count from artifact_counts), 0) as accepted_artifact_count,
        coalesce((select rejected_artifact_count from artifact_counts), 0) as rejected_artifact_count,
        coalesce((select cluster_artifact_count from artifact_counts), 0) as cluster_artifact_count,
        coalesce((select codex_invocation_count from invocation_counts), 0) as codex_invocation_count,
        coalesce((select codex_succeeded_count from invocation_counts), 0) as codex_succeeded_count,
        coalesce((select codex_failed_count from invocation_counts), 0) as codex_failed_count,
        coalesce((select hierarchical_impact_count from hierarchical_counts), 0) as hierarchical_impact_count,
        coalesce((select cycle_snapshot_count from cycle_counts), 0) as cycle_snapshot_count,
        coalesce((select recommendation_cycle_component_count from recommendation_counts), 0) as recommendation_cycle_component_count,
        coalesce((select paper_validation_count from paper_counts), 0) as paper_validation_count,
        coalesce((select paper_validation_passed_count from paper_counts), 0) as paper_validation_passed_count
),
checks as (
    select
        coalesce((select sum(repeated_count - 1)::integer from duplicate_titles), 0) as duplicate_title_count,
        (select count(*)::integer from ungrounded_direct_tickers) as ungrounded_direct_ticker_count,
        (select count(*)::integer from macro_false_tickers) as macro_false_ticker_count,
        (select count(*)::integer from quantum_energy_mislinks) as quantum_energy_mislink_count,
        (select count(*)::integer from normal_macro_flows) as normal_macro_flow_count
),
score_input as (
    select
        checks.*,
        metrics.*,
        (
            checks.ungrounded_direct_ticker_count
            + checks.macro_false_ticker_count
            + checks.quantum_energy_mislink_count
            + least(checks.duplicate_title_count, 5)
        )::integer as issue_count,
        (
            case when metrics.rss_document_count = 0 then 1 else 0 end
            + case when metrics.translated_document_count = 0 then 1 else 0 end
            + case when metrics.accepted_artifact_count = 0 and metrics.rejected_artifact_count = 0 then 1 else 0 end
            + case when metrics.hierarchical_impact_count = 0 then 1 else 0 end
            + case when metrics.cycle_snapshot_count = 0 then 1 else 0 end
        )::integer as readiness_gap_count
    from checks
    cross join metrics
)
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'lookback_days', {lookback_days},
    'audit_status',
    case
        when rss_document_count = 0 then 'not_ready'
        when issue_count > 0 then 'attention_required'
        when readiness_gap_count > 0 then 'degraded'
        else 'ok'
    end,
    'audit_score', greatest(0, 100 - issue_count * 15 - readiness_gap_count * 8),
    'issue_count', issue_count,
    'readiness_gap_count', readiness_gap_count,
    'readiness_gaps',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'gap_key', gap.gap_key,
                    'label', gap.label,
                    'metric_key', gap.metric_key,
                    'current_value', gap.current_value,
                    'next_action', gap.next_action
                )
                order by gap.sort_order
            )
            from (
                values
                    (
                        1,
                        'rss_documents_missing',
                        'RSS 뉴스 수집 결과 없음',
                        'rss_document_count',
                        rss_document_count,
                        'run news-intraday before quality audit'
                    ),
                    (
                        2,
                        'korean_translation_missing',
                        '한국어 번역 결과 없음',
                        'translated_document_count',
                        translated_document_count,
                        'run Korean translation batch before user-facing review'
                    ),
                    (
                        3,
                        'ai_extraction_artifact_missing',
                        'AI 후보 분석 결과 없음',
                        'accepted_or_rejected_artifact_count',
                        accepted_artifact_count + rejected_artifact_count,
                        'run news-rss-ai-extract-run before recommendation review'
                    ),
                    (
                        4,
                        'hierarchical_impact_missing',
                        '상위 흐름 전파 결과 없음',
                        'hierarchical_impact_count',
                        hierarchical_impact_count,
                        'run hierarchical-impact-propagation after AI extraction'
                    ),
                    (
                        5,
                        'cycle_snapshot_missing',
                        '사이클 스냅샷 결과 없음',
                        'cycle_snapshot_count',
                        cycle_snapshot_count,
                        'run decision-daily or cycle-hierarchy-snapshot-v2-run'
                    )
            ) as gap(sort_order, gap_key, label, metric_key, current_value, next_action)
            where gap.current_value = 0
        ),
        '[]'::json
    ),
    'metrics', json_build_object(
        'rss_document_count', rss_document_count,
        'translated_document_count', translated_document_count,
        'accepted_artifact_count', accepted_artifact_count,
        'rejected_artifact_count', rejected_artifact_count,
        'cluster_artifact_count', cluster_artifact_count,
        'codex_invocation_count', codex_invocation_count,
        'codex_succeeded_count', codex_succeeded_count,
        'codex_failed_count', codex_failed_count,
        'hierarchical_impact_count', hierarchical_impact_count,
        'cycle_snapshot_count', cycle_snapshot_count,
        'recommendation_cycle_component_count', recommendation_cycle_component_count,
        'paper_validation_count', paper_validation_count,
        'paper_validation_passed_count', paper_validation_passed_count
    ),
    'checks', json_build_object(
        'duplicate_title_count', duplicate_title_count,
        'ungrounded_direct_ticker_count', ungrounded_direct_ticker_count,
        'macro_false_ticker_count', macro_false_ticker_count,
        'quantum_energy_mislink_count', quantum_energy_mislink_count,
        'normal_macro_flow_count', normal_macro_flow_count
    ),
    'samples', json_build_object(
        'duplicate_titles',
        coalesce(
            (
                select json_agg(json_build_object('title', normalized_title, 'repeated_count', repeated_count))
                from (select * from duplicate_titles order by repeated_count desc, normalized_title limit 5) sample
            ),
            '[]'::json
        ),
        'ungrounded_direct_tickers',
        coalesce(
            (
                select json_agg(
                    json_build_object(
                        'event_id', event_id,
                        'symbol', primary_symbol,
                        'instrument_name', instrument_name,
                        'event_title', event_title
                    )
                )
                from (select * from ungrounded_direct_tickers order by event_id, primary_symbol limit 5) sample
            ),
            '[]'::json
        ),
        'macro_false_tickers',
        coalesce(
            (
                select json_agg(
                    json_build_object(
                        'event_id', event_id,
                        'symbol', primary_symbol,
                        'instrument_name', instrument_name,
                        'event_title', event_title,
                        'node_codes', node_codes,
                        'impact_direction', impact_direction
                    )
                )
                from (select * from macro_false_tickers order by event_id, primary_symbol limit 5) sample
            ),
            '[]'::json
        ),
        'quantum_energy_mislinks',
        coalesce(
            (
                select json_agg(json_build_object('event_id', event_id, 'node_code', node_code))
                from (select * from quantum_energy_mislinks order by event_id, node_code limit 5) sample
            ),
            '[]'::json
        ),
        'normal_macro_flows',
        coalesce(
            (
                select json_agg(
                    json_build_object(
                        'event_id', event_id,
                        'event_title', event_title,
                        'node_codes', node_codes,
                        'impact_directions', impact_directions
                    )
                )
                from (select * from normal_macro_flows order by event_id limit 5) sample
            ),
            '[]'::json
        )
    )
)
from score_input;"""


def render_stale_direct_impact_cleanup_sql(
    *,
    as_of_date: date,
    lookback_days: int = 30,
    execute: bool = False,
    limit: int = 200,
) -> str:
    if lookback_days < 1 or lookback_days > 120:
        raise ValueError("lookback_days must be between 1 and 120.")
    if limit < 1 or limit > 1000:
        raise ValueError("limit must be between 1 and 1000.")
    target_date = sql_date(as_of_date)
    lookback_interval = f"interval '{lookback_days} days'"
    deletion_cte = (
        """deleted_impacts as (
    delete from event.event_instrument_impact impact
    using stale_direct_impacts stale
    where impact.event_id = stale.event_id
      and impact.instrument_id = stale.instrument_id
    returning impact.event_id, impact.instrument_id
)"""
        if execute
        else """deleted_impacts as (
    select null::bigint as event_id, null::bigint as instrument_id
    where false
)"""
    )
    return f"""-- cycle ai stale direct impact cleanup
with windowed_events as (
    select event_row.*
    from event.event event_row
    where event_row.event_type = 'news_rss_item'
      and event_row.event_at >= ({target_date} - {lookback_interval})
      and event_row.event_at < ({target_date} + interval '1 day')
),
source_text_by_event as (
    select
        event_row.event_id,
        string_agg(
            coalesce(document.title, '') || ' ' || coalesce(document.summary, ''),
            ' '
            order by document.document_id
        ) as source_text
    from windowed_events event_row
    left join event.event_document_link link
      on link.event_id = event_row.event_id
     and link.link_type = 'source'
    left join ingest.source_document document
      on document.document_id = link.document_id
    group by event_row.event_id
),
source_aliases(primary_symbol, alias_text) as (
    values
        ('SPY', 's&p 500'),
        ('SPY', 's&p500'),
        ('SPY', 'spx'),
        ('QQQ', 'nasdaq 100'),
        ('QQQ', 'nasdaq futures'),
        ('QQQ', 'nasdaq'),
        ('XLE', 'energy sector')
),
direct_impacts as (
    select
        impact.event_id,
        impact.instrument_id,
        instrument.primary_symbol,
        instrument.name as instrument_name,
        impact.impact_direction,
        impact.impact_strength,
        impact.confidence,
        left(coalesce(event_row.title, ''), 180) as event_title,
        source_text.source_text_normalized,
        case
            when position(' ' || lower(instrument.primary_symbol) || ' ' in source_text.source_text_normalized) > 0 then true
            when exists (
                select 1
                from source_aliases alias
                where alias.primary_symbol = upper(instrument.primary_symbol)
                  and position(
                      ' ' || btrim(regexp_replace(lower(alias.alias_text), '[^a-z0-9]+', ' ', 'g')) || ' '
                      in source_text.source_text_normalized
                  ) > 0
            ) then true
            when exists (
                select 1
                from regexp_split_to_table(instrument.name, '[^A-Za-z0-9]+') as token(value)
                where length(lower(token.value)) >= 4
                  and lower(token.value) not in (
                      'class',
                      'company',
                      'corp',
                      'corporation',
                      'group',
                      'holding',
                      'holdings',
                      'inc',
                      'ltd',
                      'plc',
                      'shares',
                      'stock',
                      'trust'
                  )
                  and position(' ' || lower(token.value) || ' ' in source_text.source_text_normalized) > 0
            ) then true
            else false
        end as is_grounded
    from event.event_instrument_impact impact
    join windowed_events event_row on event_row.event_id = impact.event_id
    join ref.instrument instrument on instrument.instrument_id = impact.instrument_id
    join source_text_by_event source_event on source_event.event_id = impact.event_id
    cross join lateral (
        select ' ' || btrim(regexp_replace(lower(coalesce(source_event.source_text, '')), '[^a-z0-9]+', ' ', 'g')) || ' ' as source_text_normalized
    ) source_text
),
stale_direct_impacts as (
    select
        event_id,
        instrument_id,
        primary_symbol,
        instrument_name,
        impact_direction,
        impact_strength,
        confidence,
        event_title
    from direct_impacts
    where is_grounded = false
    order by event_id, primary_symbol
    limit {limit}
),
{deletion_cte}
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'lookback_days', {lookback_days},
    'execute', {str(execute).lower()},
    'candidate_count', (select count(*)::integer from stale_direct_impacts),
    'removed_count', (select count(*)::integer from deleted_impacts),
    'samples',
        coalesce(
            (
                select json_agg(
                    json_build_object(
                        'event_id', event_id,
                        'symbol', primary_symbol,
                        'instrument_name', instrument_name,
                        'impact_direction', impact_direction,
                        'confidence', confidence,
                        'event_title', event_title
                    )
                    order by event_id, primary_symbol
                )
                from (select * from stale_direct_impacts order by event_id, primary_symbol limit 10) sample
            ),
            '[]'::json
        )
)::text;"""


def render_duplicate_title_cleanup_sql(
    *,
    as_of_date: date,
    lookback_days: int = 30,
    execute: bool = False,
    limit: int = 200,
) -> str:
    if lookback_days < 1 or lookback_days > 120:
        raise ValueError("lookback_days must be between 1 and 120.")
    if limit < 1 or limit > 1000:
        raise ValueError("limit must be between 1 and 1000.")
    target_date = sql_date(as_of_date)
    lookback_interval = f"interval '{lookback_days} days'"
    write_ctes = (
        """deleted_conflicting_classification as (
    delete from event.event_classification_impact impact
    using cleanup_candidates candidate
    where impact.event_id = candidate.event_id
      and exists (
          select 1
          from event.event_classification_impact keeper
          where keeper.event_id = candidate.keeper_event_id
            and keeper.node_id = impact.node_id
      )
    returning impact.event_id, impact.node_id
),
merged_classification as (
    update event.event_classification_impact impact
    set event_id = candidate.keeper_event_id
    from cleanup_candidates candidate
    where impact.event_id = candidate.event_id
      and not exists (
          select 1
          from event.event_classification_impact keeper
          where keeper.event_id = candidate.keeper_event_id
            and keeper.node_id = impact.node_id
      )
    returning impact.event_id, impact.node_id
),
deleted_conflicting_instrument as (
    delete from event.event_instrument_impact impact
    using cleanup_candidates candidate
    where impact.event_id = candidate.event_id
      and exists (
          select 1
          from event.event_instrument_impact keeper
          where keeper.event_id = candidate.keeper_event_id
            and keeper.instrument_id = impact.instrument_id
      )
    returning impact.event_id, impact.instrument_id
),
merged_instrument as (
    update event.event_instrument_impact impact
    set event_id = candidate.keeper_event_id
    from cleanup_candidates candidate
    where impact.event_id = candidate.event_id
      and not exists (
          select 1
          from event.event_instrument_impact keeper
          where keeper.event_id = candidate.keeper_event_id
            and keeper.instrument_id = impact.instrument_id
      )
    returning impact.event_id, impact.instrument_id
),
deleted_conflicting_propagated as (
    delete from signal.propagated_instrument_impact impact
    using cleanup_candidates candidate
    where impact.event_id = candidate.event_id
      and exists (
          select 1
          from signal.propagated_instrument_impact keeper
          where keeper.event_id = candidate.keeper_event_id
            and keeper.node_id = impact.node_id
            and keeper.instrument_id = impact.instrument_id
            and keeper.propagation_kind = impact.propagation_kind
      )
    returning impact.event_id, impact.node_id, impact.instrument_id
),
merged_propagated as (
    update signal.propagated_instrument_impact impact
    set event_id = candidate.keeper_event_id
    from cleanup_candidates candidate
    where impact.event_id = candidate.event_id
      and not exists (
          select 1
          from signal.propagated_instrument_impact keeper
          where keeper.event_id = candidate.keeper_event_id
            and keeper.node_id = impact.node_id
            and keeper.instrument_id = impact.instrument_id
            and keeper.propagation_kind = impact.propagation_kind
      )
    returning impact.event_id, impact.node_id, impact.instrument_id
),
deleted_conflicting_hierarchical as (
    delete from signal.hierarchical_propagated_instrument_impact impact
    using cleanup_candidates candidate
    where impact.event_id = candidate.event_id
      and exists (
          select 1
          from signal.hierarchical_propagated_instrument_impact keeper
          where keeper.event_id = candidate.keeper_event_id
            and keeper.source_node_id = impact.source_node_id
            and keeper.propagated_node_id = impact.propagated_node_id
            and keeper.instrument_id = impact.instrument_id
            and keeper.propagation_kind = impact.propagation_kind
            and keeper.path_hash = impact.path_hash
      )
    returning impact.event_id, impact.source_node_id, impact.propagated_node_id, impact.instrument_id, impact.path_hash
),
merged_hierarchical as (
    update signal.hierarchical_propagated_instrument_impact impact
    set event_id = candidate.keeper_event_id
    from cleanup_candidates candidate
    where impact.event_id = candidate.event_id
      and not exists (
          select 1
          from signal.hierarchical_propagated_instrument_impact keeper
          where keeper.event_id = candidate.keeper_event_id
            and keeper.source_node_id = impact.source_node_id
            and keeper.propagated_node_id = impact.propagated_node_id
            and keeper.instrument_id = impact.instrument_id
            and keeper.propagation_kind = impact.propagation_kind
            and keeper.path_hash = impact.path_hash
      )
    returning impact.event_id, impact.source_node_id, impact.propagated_node_id, impact.instrument_id, impact.path_hash
),
deleted_conflicting_chunks as (
    delete from ai.document_chunk chunk
    using cleanup_candidates candidate
    where chunk.document_id = candidate.document_id
      and exists (
          select 1
          from ai.document_chunk keeper
          where keeper.document_id = candidate.keeper_document_id
            and keeper.chunk_index = chunk.chunk_index
            and keeper.content_hash = chunk.content_hash
      )
    returning chunk.chunk_id
),
merged_chunks as (
    update ai.document_chunk chunk
    set document_id = candidate.keeper_document_id
    from cleanup_candidates candidate
    where chunk.document_id = candidate.document_id
      and not exists (
          select 1
          from ai.document_chunk keeper
          where keeper.document_id = candidate.keeper_document_id
            and keeper.chunk_index = chunk.chunk_index
      )
    returning chunk.chunk_id
),
merged_artifacts as (
    update ai.extraction_artifact artifact
    set
        document_id = candidate.keeper_document_id,
        event_id = candidate.keeper_event_id
    from cleanup_candidates candidate
    where artifact.document_id = candidate.document_id
       or artifact.event_id = candidate.event_id
    returning artifact.artifact_id
),
deleted_events as (
    delete from event.event event_row
    using cleanup_candidates candidate
    where event_row.event_id = candidate.event_id
    returning event_row.event_id
),
deleted_documents as (
    delete from ingest.source_document document
    using cleanup_candidates candidate
    where document.document_id = candidate.document_id
    returning document.document_id
)"""
        if execute
        else """deleted_conflicting_classification as (
    select null::bigint as event_id, null::bigint as node_id
    where false
),
merged_classification as (
    select null::bigint as event_id, null::bigint as node_id
    where false
),
deleted_conflicting_instrument as (
    select null::bigint as event_id, null::bigint as instrument_id
    where false
),
merged_instrument as (
    select null::bigint as event_id, null::bigint as instrument_id
    where false
),
deleted_conflicting_propagated as (
    select null::bigint as event_id, null::bigint as node_id, null::bigint as instrument_id
    where false
),
merged_propagated as (
    select null::bigint as event_id, null::bigint as node_id, null::bigint as instrument_id
    where false
),
deleted_conflicting_hierarchical as (
    select null::bigint as event_id, null::bigint as source_node_id, null::bigint as propagated_node_id, null::bigint as instrument_id, null::text as path_hash
    where false
),
merged_hierarchical as (
    select null::bigint as event_id, null::bigint as source_node_id, null::bigint as propagated_node_id, null::bigint as instrument_id, null::text as path_hash
    where false
),
deleted_conflicting_chunks as (
    select null::bigint as chunk_id
    where false
),
merged_chunks as (
    select null::bigint as chunk_id
    where false
),
merged_artifacts as (
    select null::bigint as artifact_id
    where false
),
deleted_events as (
    select null::bigint as event_id
    where false
),
deleted_documents as (
    select null::bigint as document_id
    where false
)"""
    )
    return f"""-- cycle ai duplicate title cleanup
with windowed_documents as (
    select
        document.document_id,
        document.data_source_id,
        lower(regexp_replace(document.title, '\\s+', ' ', 'g')) as normalized_title,
        document.title,
        document.url,
        document.published_at,
        document.ingested_at,
        coalesce(document.published_at, document.ingested_at) as observed_at
    from ingest.source_document document
    where document.document_type = 'news_rss_item'
      and coalesce(document.published_at, document.ingested_at) >= ({target_date} - {lookback_interval})
      and coalesce(document.published_at, document.ingested_at) < ({target_date} + interval '1 day')
      and document.title is not null
      and btrim(document.title) <> ''
),
document_events as (
    select
        document.document_id,
        event_row.event_id,
        event_row.title as event_title
    from windowed_documents document
    left join event.event_document_link link
      on link.document_id = document.document_id
     and link.link_type = 'source'
    left join event.event event_row
      on event_row.event_id = link.event_id
     and event_row.event_type = 'news_rss_item'
),
quality as (
    select
        document.document_id,
        coalesce(bool_or(event_row.event_id is not null), false) as has_event,
        coalesce(bool_or(classification.event_id is not null), false) as has_classification_impact,
        coalesce(bool_or(instrument.event_id is not null), false) as has_instrument_impact,
        coalesce(bool_or(propagated.event_id is not null), false) as has_propagated_impact,
        coalesce(bool_or(hierarchical.event_id is not null), false) as has_hierarchical_impact,
        coalesce(bool_or(artifact.artifact_id is not null), false) as has_ai_artifact
    from windowed_documents document
    left join document_events event_row on event_row.document_id = document.document_id
    left join event.event_classification_impact classification on classification.event_id = event_row.event_id
    left join event.event_instrument_impact instrument on instrument.event_id = event_row.event_id
    left join signal.propagated_instrument_impact propagated on propagated.event_id = event_row.event_id
    left join signal.hierarchical_propagated_instrument_impact hierarchical on hierarchical.event_id = event_row.event_id
    left join ai.extraction_artifact artifact
      on artifact.document_id = document.document_id
      or artifact.event_id = event_row.event_id
    group by document.document_id
),
ranked_documents as (
    select
        document.*,
        event_row.event_id,
        coalesce(event_row.event_title, document.title) as event_title,
        first_value(document.document_id) over (
            partition by document.normalized_title, document.observed_at
            order by
                case when event_row.event_id is null then 1 else 0 end,
                case
                    when lower(coalesce(document.url, '')) like '%finance.yahoo.com/%' then 2
                    when lower(coalesce(document.url, '')) like '%finance.yahoo.com%' then 2
                    else 0
                end,
                quality.has_ai_artifact desc,
                quality.has_classification_impact desc,
                quality.has_instrument_impact desc,
                quality.has_propagated_impact desc,
                quality.has_hierarchical_impact desc,
                document.ingested_at,
                document.document_id
        ) as keeper_document_id,
        first_value(event_row.event_id) over (
            partition by document.normalized_title, document.observed_at
            order by
                case when event_row.event_id is null then 1 else 0 end,
                case
                    when lower(coalesce(document.url, '')) like '%finance.yahoo.com/%' then 2
                    when lower(coalesce(document.url, '')) like '%finance.yahoo.com%' then 2
                    else 0
                end,
                quality.has_ai_artifact desc,
                quality.has_classification_impact desc,
                quality.has_instrument_impact desc,
                quality.has_propagated_impact desc,
                quality.has_hierarchical_impact desc,
                document.ingested_at,
                document.document_id
        ) as keeper_event_id,
        quality.has_classification_impact,
        quality.has_instrument_impact,
        quality.has_propagated_impact,
        quality.has_hierarchical_impact,
        quality.has_ai_artifact,
        count(*) over (
            partition by document.normalized_title, document.observed_at
        ) as duplicate_group_count,
        row_number() over (
            partition by document.normalized_title, document.observed_at
            order by
                case when event_row.event_id is null then 1 else 0 end,
                case
                    when lower(coalesce(document.url, '')) like '%finance.yahoo.com/%' then 2
                    when lower(coalesce(document.url, '')) like '%finance.yahoo.com%' then 2
                    else 0
                end,
                quality.has_ai_artifact desc,
                quality.has_classification_impact desc,
                quality.has_instrument_impact desc,
                quality.has_propagated_impact desc,
                quality.has_hierarchical_impact desc,
                document.ingested_at,
                document.document_id
        ) as duplicate_rank
    from windowed_documents document
    left join document_events event_row on event_row.document_id = document.document_id
    join quality on quality.document_id = document.document_id
),
cleanup_candidates as (
    select
        document_id,
        event_id,
        keeper_document_id,
        keeper_event_id,
        normalized_title,
        title,
        event_title,
        url,
        published_at,
        duplicate_group_count,
        duplicate_rank
    from ranked_documents
    where duplicate_group_count > 1
      and duplicate_rank > 1
      and event_id is not null
      and keeper_event_id is not null
      and event_id <> keeper_event_id
      and not exists (
          select 1
          from ai.document_chunk duplicate_chunk
          join ai.document_chunk keeper_chunk
            on keeper_chunk.document_id = ranked_documents.keeper_document_id
           and keeper_chunk.chunk_index = duplicate_chunk.chunk_index
           and keeper_chunk.content_hash <> duplicate_chunk.content_hash
          where duplicate_chunk.document_id = ranked_documents.document_id
      )
    order by duplicate_group_count desc, normalized_title, duplicate_rank
    limit {limit}
),
{write_ctes}
select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'lookback_days', {lookback_days},
    'execute', {str(execute).lower()},
    'candidate_count', (select count(*)::integer from cleanup_candidates),
    'merged_classification_count', (select count(*)::integer from merged_classification),
    'deleted_conflicting_classification_count', (select count(*)::integer from deleted_conflicting_classification),
    'merged_instrument_count', (select count(*)::integer from merged_instrument),
    'deleted_conflicting_instrument_count', (select count(*)::integer from deleted_conflicting_instrument),
    'merged_propagated_count', (select count(*)::integer from merged_propagated),
    'deleted_conflicting_propagated_count', (select count(*)::integer from deleted_conflicting_propagated),
    'merged_hierarchical_count', (select count(*)::integer from merged_hierarchical),
    'deleted_conflicting_hierarchical_count', (select count(*)::integer from deleted_conflicting_hierarchical),
    'merged_chunk_count', (select count(*)::integer from merged_chunks),
    'deleted_conflicting_chunk_count', (select count(*)::integer from deleted_conflicting_chunks),
    'merged_artifact_count', (select count(*)::integer from merged_artifacts),
    'deleted_event_count', (select count(*)::integer from deleted_events),
    'deleted_document_count', (select count(*)::integer from deleted_documents),
    'samples',
        coalesce(
            (
                select json_agg(
                    json_build_object(
                        'event_id', event_id,
                        'document_id', document_id,
                        'keeper_event_id', keeper_event_id,
                        'keeper_document_id', keeper_document_id,
                        'title', title,
                        'url', url,
                        'published_at', published_at,
                        'duplicate_group_count', duplicate_group_count,
                        'duplicate_rank', duplicate_rank
                    )
                    order by normalized_title, duplicate_rank
                )
                from (select * from cleanup_candidates order by normalized_title, duplicate_rank limit 10) sample
            ),
            '[]'::json
        )
)::text;"""


def load_cycle_ai_quality_audit_state(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    lookback_days: int = 30,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_cycle_ai_quality_audit_sql(as_of_date=as_of_date, lookback_days=lookback_days)
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Cycle AI quality audit lookup did not return a JSON object.")
    return payload


def load_stale_direct_impact_cleanup_state(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    lookback_days: int = 30,
    execute: bool = False,
    limit: int = 200,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_stale_direct_impact_cleanup_sql(
                as_of_date=as_of_date,
                lookback_days=lookback_days,
                execute=execute,
                limit=limit,
            )
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Stale direct impact cleanup lookup did not return a JSON object.")
    return payload


def load_duplicate_title_cleanup_state(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    lookback_days: int = 30,
    execute: bool = False,
    limit: int = 200,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    payload = json.loads(
        sql_executor.execute_scalar(
            render_duplicate_title_cleanup_sql(
                as_of_date=as_of_date,
                lookback_days=lookback_days,
                execute=execute,
                limit=limit,
            )
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Duplicate title cleanup lookup did not return a JSON object.")
    return payload


def run_cycle_ai_quality_audit(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    lookback_days: int = 30,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    state = load_cycle_ai_quality_audit_state(
        config=config,
        as_of_date=as_of_date,
        lookback_days=lookback_days,
        executor=sql_executor,
    )
    report: dict[str, object] = {
        "report_name": DEFAULT_PIPELINE_NAME,
        "generated_at": _format_timestamp(generated_at or datetime.now(timezone.utc)),
        "status": "planned" if not execute else "running",
        "execute": execute,
        "as_of_date": str(state.get("as_of_date") or as_of_date.isoformat()),
        "lookback_days": int(state.get("lookback_days") or lookback_days),
        "audit_status": str(state.get("audit_status") or "unknown"),
        "audit_score": int(state.get("audit_score") or 0),
        "issue_count": int(state.get("issue_count") or 0),
        "readiness_gap_count": int(state.get("readiness_gap_count") or 0),
        "readiness_gaps": _as_scalar_or_mapping_list(state.get("readiness_gaps")),
        "metrics": _as_mapping(state.get("metrics")),
        "checks": _as_mapping(state.get("checks")),
        "samples": _as_mapping(state.get("samples")),
        "next_actions": _next_actions(state),
    }
    if not execute:
        _assert_secret_free_payload(report)
        return report

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_PIPELINE_NAME,
        config_json={
            "as_of_date": as_of_date.isoformat(),
            "lookback_days": lookback_days,
            "audit_status": report["audit_status"],
            "audit_score": report["audit_score"],
            "issue_count": report["issue_count"],
        },
    )
    try:
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise
    report["status"] = "completed"
    report["run_id"] = run_id
    _assert_secret_free_payload(report)
    return report


def run_stale_direct_impact_cleanup(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    lookback_days: int = 30,
    execute: bool = False,
    limit: int = 200,
    executor: PsqlCommandExecutor | None = None,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id: int | None = None
    if execute:
        run_id = _create_pipeline_run(
            sql_executor,
            pipeline_name=STALE_DIRECT_IMPACT_CLEANUP_PIPELINE_NAME,
            config_json={
                "as_of_date": as_of_date.isoformat(),
                "lookback_days": lookback_days,
                "limit": limit,
            },
        )
    try:
        state = load_stale_direct_impact_cleanup_state(
            config=config,
            as_of_date=as_of_date,
            lookback_days=lookback_days,
            execute=execute,
            limit=limit,
            executor=sql_executor,
        )
        if run_id is not None:
            _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        if run_id is not None:
            _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    report: dict[str, object] = {
        "report_name": STALE_DIRECT_IMPACT_CLEANUP_PIPELINE_NAME,
        "generated_at": _format_timestamp(generated_at or datetime.now(timezone.utc)),
        "status": "completed" if execute else "planned",
        "execute": execute,
        "as_of_date": str(state.get("as_of_date") or as_of_date.isoformat()),
        "lookback_days": int(state.get("lookback_days") or lookback_days),
        "candidate_count": int(state.get("candidate_count") or 0),
        "removed_count": int(state.get("removed_count") or 0),
        "samples": _as_scalar_or_mapping_list(state.get("samples")),
        "order_boundary": "read_only_no_order",
        "recommendation_scoring_mutated": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
    }
    if run_id is not None:
        report["run_id"] = run_id
    _assert_secret_free_payload(report)
    return report


def run_duplicate_title_cleanup(
    *,
    config: RuntimeConfig,
    as_of_date: date,
    lookback_days: int = 30,
    execute: bool = False,
    limit: int = 200,
    executor: PsqlCommandExecutor | None = None,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id: int | None = None
    if execute:
        run_id = _create_pipeline_run(
            sql_executor,
            pipeline_name=DUPLICATE_TITLE_CLEANUP_PIPELINE_NAME,
            config_json={
                "as_of_date": as_of_date.isoformat(),
                "lookback_days": lookback_days,
                "limit": limit,
            },
        )
    try:
        state = load_duplicate_title_cleanup_state(
            config=config,
            as_of_date=as_of_date,
            lookback_days=lookback_days,
            execute=execute,
            limit=limit,
            executor=sql_executor,
        )
        if run_id is not None:
            _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        if run_id is not None:
            _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    report: dict[str, object] = {
        "report_name": DUPLICATE_TITLE_CLEANUP_PIPELINE_NAME,
        "generated_at": _format_timestamp(generated_at or datetime.now(timezone.utc)),
        "status": "completed" if execute else "planned",
        "execute": execute,
        "as_of_date": str(state.get("as_of_date") or as_of_date.isoformat()),
        "lookback_days": int(state.get("lookback_days") or lookback_days),
        "candidate_count": int(state.get("candidate_count") or 0),
        "merged_classification_count": int(state.get("merged_classification_count") or 0),
        "deleted_conflicting_classification_count": int(
            state.get("deleted_conflicting_classification_count") or 0
        ),
        "merged_instrument_count": int(state.get("merged_instrument_count") or 0),
        "deleted_conflicting_instrument_count": int(state.get("deleted_conflicting_instrument_count") or 0),
        "merged_propagated_count": int(state.get("merged_propagated_count") or 0),
        "deleted_conflicting_propagated_count": int(
            state.get("deleted_conflicting_propagated_count") or 0
        ),
        "merged_hierarchical_count": int(state.get("merged_hierarchical_count") or 0),
        "deleted_conflicting_hierarchical_count": int(
            state.get("deleted_conflicting_hierarchical_count") or 0
        ),
        "merged_chunk_count": int(state.get("merged_chunk_count") or 0),
        "deleted_conflicting_chunk_count": int(state.get("deleted_conflicting_chunk_count") or 0),
        "merged_artifact_count": int(state.get("merged_artifact_count") or 0),
        "deleted_event_count": int(state.get("deleted_event_count") or 0),
        "deleted_document_count": int(state.get("deleted_document_count") or 0),
        "samples": _as_scalar_or_mapping_list(state.get("samples")),
        "order_boundary": "read_only_no_order",
        "recommendation_scoring_mutated": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
    }
    if run_id is not None:
        report["run_id"] = run_id
    _assert_secret_free_payload(report)
    return report


def load_cycle_ai_quality_audit_visibility_report(
    *,
    report_path: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    repo_root: str | Path | None = None,
) -> dict[str, object]:
    selected_report_path = str(
        report_path
        if report_path is not None
        else (env if env is not None else {}).get(CYCLE_AI_QUALITY_AUDIT_REPORT_ENV, "")
    ).strip()
    base = {
        "status": "not_configured",
        "execute": False,
        "generated_at": "",
        "as_of_date": "",
        "lookback_days": 0,
        "audit_score": 0,
        "issue_count": 0,
        "readiness_gap_count": 0,
        "readiness_gaps": [],
        "metrics": {},
        "checks": {},
        "samples": {},
        "next_actions": ["run cycle-ai-quality-audit-run --execute --output outside the repository"],
        "source": "not_configured",
    }
    if not selected_report_path:
        return base

    candidate = Path(selected_report_path).expanduser()
    if not candidate.is_file():
        return {
            **base,
            "status": "missing_report",
            "source": "missing_report",
            "next_actions": ["regenerate cycle AI quality audit report"],
        }

    try:
        resolved_report_path = resolve_existing_file(
            candidate,
            label="cycle AI quality audit report",
            repo_root=repo_root,
            require_repo_outside=True,
        )
        payload = json.loads(resolved_report_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {
            **base,
            "status": "invalid_report",
            "source": "invalid_report",
            "next_actions": ["regenerate cycle AI quality audit report"],
        }

    if not isinstance(payload, dict) or payload.get("report_name") != DEFAULT_PIPELINE_NAME:
        return {
            **base,
            "status": "invalid_report",
            "source": "invalid_report",
            "next_actions": ["regenerate cycle AI quality audit report"],
        }

    visibility = {
        "status": str(payload.get("audit_status") or payload.get("status") or "unknown"),
        "execute": payload.get("execute") is True,
        "generated_at": str(payload.get("generated_at") or ""),
        "as_of_date": str(payload.get("as_of_date") or ""),
        "lookback_days": int(payload.get("lookback_days") or 0),
        "audit_score": int(payload.get("audit_score") or 0),
        "issue_count": int(payload.get("issue_count") or 0),
        "readiness_gap_count": int(payload.get("readiness_gap_count") or 0),
        "readiness_gaps": _as_scalar_or_mapping_list(payload.get("readiness_gaps")),
        "metrics": _as_mapping(payload.get("metrics")),
        "checks": _as_mapping(payload.get("checks")),
        "samples": _as_mapping(payload.get("samples")),
        "next_actions": [str(item) for item in _as_scalar_list(payload.get("next_actions"))],
        "source": "cycle_ai_quality_audit_report",
    }
    _assert_secret_free_payload(visibility)
    return visibility


def _next_actions(state: Mapping[str, object]) -> list[str]:
    status = str(state.get("audit_status") or "unknown")
    checks = _as_mapping(state.get("checks"))
    metrics = _as_mapping(state.get("metrics"))
    actions: list[str] = []
    if status == "not_ready":
        actions.append("run news-intraday and decision-daily before trusting recommendations")
    if int(checks.get("quantum_energy_mislink_count") or 0) > 0:
        actions.append("inspect quantum news theme grounding and remove energy mislinks")
    if int(checks.get("ungrounded_direct_ticker_count") or 0) > 0:
        actions.append("review direct ticker impacts without source-text grounding")
    if int(checks.get("macro_false_ticker_count") or 0) > 0:
        actions.append("keep macro-only news at macro/theme level until propagation adds instrument impact")
    if int(checks.get("duplicate_title_count") or 0) > 0:
        actions.append("deduplicate repeated RSS titles before cluster evidence")
    if int(metrics.get("translated_document_count") or 0) == 0:
        actions.append("run Korean translation batch before user-facing review")
    if int(metrics.get("accepted_artifact_count") or 0) == 0 and int(metrics.get("rejected_artifact_count") or 0) == 0:
        actions.append("run news-rss-ai-extract-run before recommendation review")
    if int(metrics.get("hierarchical_impact_count") or 0) == 0:
        actions.append("run hierarchical-impact-propagation after AI extraction")
    if int(metrics.get("cycle_snapshot_count") or 0) == 0:
        actions.append("run decision-daily or cycle-hierarchy-snapshot-v2-run")
    if not actions:
        actions.append("continue scheduled news, propagation, cycle snapshot, and paper validation runs")
    return actions


def _as_mapping(value: object) -> dict[str, object]:
    if not isinstance(value, MappingABC):
        return {}
    return {str(key): item for key, item in value.items()}


def _as_scalar_list(value: object) -> list[object]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str | int | float | bool)]


def _as_scalar_or_mapping_list(value: object) -> list[object]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str | int | float | bool | dict)]


def _assert_secret_free_payload(payload: Mapping[str, object]) -> None:
    text = json.dumps(payload, sort_keys=True)
    forbidden_markers = (
        "postgresql://",
        "postgres://",
        "hidden-",
        "token-",
        "api-key-",
        "runtime_pass",
    )
    for marker in forbidden_markers:
        if marker in text:
            raise ValueError("Cycle AI quality audit report contains a secret-like value.")


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
