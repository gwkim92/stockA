from __future__ import annotations

from datetime import date

from stockanalysis.ingest.macro.sql import sql_date, sql_literal


def render_instrument_evidence_neighborhood_sql(*, primary_symbol: str, as_of_date: date, limit: int = 25) -> str:
    symbol = primary_symbol.strip().upper()
    if not symbol:
        raise ValueError("primary_symbol must not be empty.")
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")

    symbol_literal = sql_literal(symbol)
    target_date_sql = sql_date(as_of_date)
    return f"""-- ai evidence neighborhood lookup
with target_instrument as (
    select
        instrument.instrument_id,
        instrument.primary_symbol,
        instrument.name,
        instrument.market_code
    from ref.instrument instrument
    where upper(instrument.primary_symbol) = upper({symbol_literal})
    limit 1
),
theme_memberships as (
    select
        node.node_id,
        node.taxonomy_family,
        node.node_type,
        node.code,
        node.name,
        membership.membership_type,
        membership.confidence,
        membership.source_document_id
    from target_instrument instrument
    join ref.instrument_classification_membership membership
      on membership.instrument_id = instrument.instrument_id
    join ref.classification_node node
      on node.node_id = membership.node_id
    where membership.valid_from <= {target_date_sql}
      and (membership.valid_to is null or membership.valid_to >= {target_date_sql})
),
theme_edges as (
    select
        edge.edge_id,
        parent_node.code as parent_code,
        child_node.code as child_code,
        edge.relation_type,
        edge.weight
    from theme_memberships theme
    join ref.classification_edge edge
      on edge.parent_node_id = theme.node_id
      or edge.child_node_id = theme.node_id
    join ref.classification_node parent_node
      on parent_node.node_id = edge.parent_node_id
    join ref.classification_node child_node
      on child_node.node_id = edge.child_node_id
    where edge.valid_from <= {target_date_sql}
      and (edge.valid_to is null or edge.valid_to >= {target_date_sql})
),
raw_recent_events as (
    select
        event_row.event_id,
        event_row.title,
        event_row.event_type,
        event_row.event_at,
        instrument_impact.impact_direction as instrument_impact_direction,
        instrument_impact.impact_strength as instrument_impact_strength,
        classification_impact.impact_direction as theme_impact_direction,
        classification_impact.impact_strength as theme_impact_strength,
        theme.code as theme_key,
        document.document_id,
        document.external_document_id,
        document.korean_title,
        document.korean_summary,
        document.translation_confidence,
        document.url as source_url,
        document.checksum as source_checksum
    from target_instrument instrument
    join event.event_instrument_impact instrument_impact
      on instrument_impact.instrument_id = instrument.instrument_id
    join event.event event_row
      on event_row.event_id = instrument_impact.event_id
    left join event.event_classification_impact classification_impact
      on classification_impact.event_id = event_row.event_id
    left join ref.classification_node theme
      on theme.node_id = classification_impact.node_id
    left join event.event_document_link document_link
      on document_link.event_id = event_row.event_id
     and document_link.link_type = 'source'
    left join ingest.source_document document
      on document.document_id = document_link.document_id
    where event_row.event_at < ({target_date_sql} + interval '1 day')
),
recent_events as (
    select *
    from (
        select distinct on (coalesce(nullif(lower(title), ''), source_checksum, 'event:' || event_id::text))
            event_id,
            title,
            event_type,
            event_at,
            instrument_impact_direction,
            instrument_impact_strength,
            theme_impact_direction,
            theme_impact_strength,
            theme_key,
            document_id,
            external_document_id,
            korean_title,
            korean_summary,
            translation_confidence,
            source_url,
            source_checksum
        from raw_recent_events
        order by
            coalesce(nullif(lower(title), ''), source_checksum, 'event:' || event_id::text),
            case when lower(coalesce(source_url, '')) like 'https://news.google.com/%' then 1 else 0 end,
            event_at desc,
            event_id desc
    ) deduped_events
    order by
        case when lower(coalesce(source_url, '')) like 'https://news.google.com/%' then 1 else 0 end,
        event_at desc,
        event_id desc
    limit {limit}
),
event_artifacts as (
    select
        artifact.artifact_id,
        artifact.event_id,
        artifact.document_id,
        artifact.artifact_type,
        artifact.confidence,
        invocation.provider,
        invocation.model_name,
        invocation.status,
        invocation.estimated_cost_usd
    from ai.extraction_artifact artifact
    join ai.model_invocation invocation
      on invocation.invocation_id = artifact.invocation_id
    where artifact.event_id in (select event_id from recent_events)
       or artifact.document_id in (select document_id from recent_events where document_id is not null)
),
evidence_chunks as (
    select
        chunk.chunk_id,
        chunk.document_id,
        chunk.chunk_index,
        chunk.text_preview,
        chunk.token_count,
        chunk.chunk_metadata,
        document.url as source_url,
        embedding.embedding_id,
        embedding.provider as embedding_provider,
        embedding.model_name as embedding_model_name,
        embedding.vector_storage_uri
    from ai.document_chunk chunk
    join recent_events event_row
      on event_row.document_id = chunk.document_id
    left join ingest.source_document document
      on document.document_id = chunk.document_id
    left join ai.embedding_index embedding
      on embedding.chunk_id = chunk.chunk_id
    where chunk.document_id in (select document_id from recent_events where document_id is not null)
    order by
        case when lower(coalesce(document.url, '')) like 'https://news.google.com/%' then 1 else 0 end,
        case when chunk.chunk_metadata ->> 'source_text_kind' = 'raw_html_text' then 0 else 1 end,
        event_row.event_at desc,
        chunk.document_id desc,
        chunk.chunk_index
    limit {limit}
),
active_theses as (
    select
        thesis.thesis_id,
        thesis.title,
        thesis.status,
        thesis.conviction_score,
        thesis.expected_holding_days,
        thesis.invalidation_conditions
    from target_instrument instrument
    join signal.investment_thesis thesis
      on thesis.instrument_id = instrument.instrument_id
    where thesis.created_at < ({target_date_sql} + interval '1 day')
      and (thesis.closed_at is null or thesis.closed_at >= {target_date_sql})
    order by thesis.created_at desc, thesis.thesis_id desc
    limit {limit}
),
latest_recommendations as (
    select
        recommendation.recommendation_id,
        batch.as_of_date,
        recommendation.action,
        recommendation.bucket,
        recommendation.total_score,
        recommendation.recommended_weight,
        recommendation.thesis_id
    from target_instrument instrument
    join signal.recommendation recommendation
      on recommendation.instrument_id = instrument.instrument_id
    join signal.recommendation_batch batch
      on batch.batch_id = recommendation.batch_id
    where batch.as_of_date <= {target_date_sql}
    order by batch.as_of_date desc, recommendation.recommendation_id desc
    limit {limit}
),
position_context as (
    select
        portfolio.portfolio_name,
        position.snapshot_date,
        position.market_value,
        position.weight,
        position.linked_thesis_id
    from target_instrument instrument
    join portfolio.position_snapshot position
      on position.instrument_id = instrument.instrument_id
    join portfolio.portfolio portfolio
      on portfolio.portfolio_id = position.portfolio_id
    where position.snapshot_date <= {target_date_sql}
    order by position.snapshot_date desc, portfolio.portfolio_name
    limit {limit}
)
select json_build_object(
    'query',
    json_build_object(
        'primary_symbol', {symbol_literal},
        'as_of_date', {sql_literal(as_of_date.isoformat())},
        'limit', {limit}
    ),
    'instrument',
    (select row_to_json(target_instrument) from target_instrument),
    'themes',
    coalesce((select json_agg(row_to_json(theme_memberships)) from theme_memberships), '[]'::json),
    'theme_edges',
    coalesce((select json_agg(row_to_json(theme_edges)) from theme_edges), '[]'::json),
    'events',
    coalesce((select json_agg(row_to_json(recent_events)) from recent_events), '[]'::json),
    'ai_artifacts',
    coalesce((select json_agg(row_to_json(event_artifacts)) from event_artifacts), '[]'::json),
    'evidence_chunks',
    coalesce((select json_agg(row_to_json(evidence_chunks)) from evidence_chunks), '[]'::json),
    'theses',
    coalesce((select json_agg(row_to_json(active_theses)) from active_theses), '[]'::json),
    'recommendations',
    coalesce((select json_agg(row_to_json(latest_recommendations)) from latest_recommendations), '[]'::json),
    'positions',
    coalesce((select json_agg(row_to_json(position_context)) from position_context), '[]'::json)
)::text;"""
