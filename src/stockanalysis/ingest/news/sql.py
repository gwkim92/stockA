from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import date

from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.news.models import NewsRssItem, NewsRssSyncResult


def render_news_rss_upsert_sql(
    result: NewsRssSyncResult,
    *,
    ingested_by_run_id: int | None = None,
    source_kind: str = "news_rss",
    license_type: str = "free_rss",
    trust_score: float | None = 0.6000,
) -> str:
    if not result.items:
        return """select json_build_object(
    'requested_item_count', 0,
    'source_document_count', 0,
    'event_count', 0,
    'linked_document_count', 0
)::text;"""

    source_name = _source_name(result.feed_name)
    run_literal = "null::bigint" if ingested_by_run_id is None else f"{ingested_by_run_id}::bigint"
    trust_score_literal = "null::numeric" if trust_score is None else f"{trust_score:.4f}::numeric"
    value_rows = ",\n        ".join(_render_item_tuple(item) for item in result.items)
    return f"""with source_row as (
    insert into ingest.data_source (
        source_name,
        source_kind,
        base_url,
        license_type,
        trust_score,
        is_active
    )
    values (
        {sql_literal(source_name)},
        {sql_literal(source_kind)},
        {sql_literal(result.feed_url)},
        {sql_literal(license_type)},
        {trust_score_literal},
        true
    )
    on conflict (source_name) do update
    set
        source_kind = excluded.source_kind,
        base_url = excluded.base_url,
        license_type = excluded.license_type,
        trust_score = excluded.trust_score,
        is_active = excluded.is_active
    returning data_source_id
),
input_rows (
    external_document_id,
    title,
    summary,
    url,
    language,
    published_at,
    checksum
) as (
    values
        {value_rows}
),
upserted_documents as (
    insert into ingest.source_document (
        data_source_id,
        external_document_id,
        document_type,
        title,
        summary,
        url,
        language,
        published_at,
        checksum,
        ingested_by_run_id
    )
    select
        source_row.data_source_id,
        input_rows.external_document_id,
        'news_rss_item',
        input_rows.title,
        input_rows.summary,
        input_rows.url,
        input_rows.language,
        input_rows.published_at,
        input_rows.checksum,
        {run_literal}
    from source_row
    join input_rows on true
    on conflict (data_source_id, external_document_id) where external_document_id is not null do update
    set
        title = excluded.title,
        summary = excluded.summary,
        url = excluded.url,
        language = excluded.language,
        published_at = excluded.published_at,
        checksum = excluded.checksum,
        ingested_at = now(),
        ingested_by_run_id = excluded.ingested_by_run_id
    returning
        document_id,
        external_document_id,
        title,
        summary,
        published_at
),
event_input as (
    select
        document_id,
        external_document_id,
        title,
        coalesce(summary, 'RSS item without publisher summary.') as summary,
        coalesce(published_at, now()) as event_at,
        'news_rss:' || external_document_id as dedupe_key
    from upserted_documents
),
upserted_events as (
    insert into event.event (
        event_type,
        title,
        summary,
        event_at,
        time_horizon,
        impact_polarity,
        significance_score,
        confidence,
        dedupe_key,
        created_by_run_id
    )
    select
        'news_rss_item',
        title,
        summary,
        event_at,
        'medium_term',
        'watch',
        0.3000::numeric,
        0.5000::numeric,
        dedupe_key,
        {run_literal}
    from event_input
    on conflict (dedupe_key) where dedupe_key is not null do update
    set
        title = excluded.title,
        summary = excluded.summary,
        event_at = excluded.event_at,
        time_horizon = excluded.time_horizon,
        impact_polarity = excluded.impact_polarity,
        significance_score = excluded.significance_score,
        confidence = excluded.confidence,
        created_by_run_id = excluded.created_by_run_id
    returning event_id, dedupe_key
),
linked_documents as (
    insert into event.event_document_link (
        event_id,
        document_id,
        link_type
    )
    select
        upserted_events.event_id,
        event_input.document_id,
        'source'
    from upserted_events
    join event_input on event_input.dedupe_key = upserted_events.dedupe_key
    on conflict (event_id, document_id, link_type) do nothing
    returning event_id
)
select json_build_object(
    'requested_item_count', {len(result.items)},
    'source_document_count', (select count(*)::int from upserted_documents),
    'event_count', (select count(*)::int from upserted_events),
    'linked_document_count', (select count(*)::int from linked_documents)
)::text;"""


def _render_item_tuple(item: NewsRssItem) -> str:
    published_at_literal = (
        "null::timestamptz" if item.published_at is None else f"{sql_literal(item.published_at.isoformat())}::timestamptz"
    )
    return (
        f"({sql_literal(item.external_document_id)}, "
        f"{sql_literal(item.title)}, "
        f"{sql_literal(item.summary)}, "
        f"{sql_literal(item.url)}, "
        f"{sql_literal(item.language)}, "
        f"{published_at_literal}, "
        f"{sql_literal(item.checksum)})"
    )


def render_pending_news_rss_event_enrichment_candidates_sql(*, limit: int) -> str:
    if limit <= 0:
        raise ValueError("limit must be greater than 0")
    return f"""select coalesce(
    json_agg(
        json_build_object(
            'event_id', event_id,
            'event_type', event_type,
            'dedupe_key', dedupe_key,
            'title', title,
            'summary', summary,
            'source_name', source_name,
            'external_document_id', external_document_id
        )
        order by event_at desc, event_id desc
    ),
    '[]'::json
)::text
from (
    select
        e.event_id,
        e.event_type,
        e.dedupe_key,
        e.title,
        e.summary,
        e.event_at,
        ds.source_name,
        d.external_document_id
    from event.event e
    left join event.event_document_link l
      on l.event_id = e.event_id
     and l.link_type = 'source'
    left join ingest.source_document d
      on d.document_id = l.document_id
    left join ingest.data_source ds
      on ds.data_source_id = d.data_source_id
    where e.event_type = 'news_rss_item'
      and e.dedupe_key like 'news_rss:%'
      and (
          not exists (
              select 1
              from event.event_classification_impact i
              where i.event_id = e.event_id
          )
          or not exists (
              select 1
              from event.event_instrument_impact i
              where i.event_id = e.event_id
          )
      )
    order by e.event_at desc, e.event_id desc
    limit {limit}
) pending;"""


def render_news_rss_classification_bootstrap_sql() -> str:
    return """begin;

insert into ref.classification_node (
    taxonomy_family,
    node_type,
    code,
    name,
    description,
    status
)
values
    ('internal_theme', 'theme', 'MARKET_NEWS_FLOW', 'Market News Flow', 'Credential-free news flow used as an early warning layer before AI enrichment.', 'active'),
    ('internal_theme', 'subtheme', 'US_MARKET_BREADTH', 'US Market Breadth', 'Broad US equity index, breadth, futures, and risk appetite news.', 'active'),
    ('internal_theme', 'subtheme', 'AI_SEMICONDUCTOR_CYCLE', 'AI Semiconductor Cycle', 'AI accelerator, semiconductor capex, GPU supply, and compute demand news.', 'active'),
    ('internal_theme', 'subtheme', 'MACRO_RATES_FED', 'Macro Rates and Fed', 'Rates, inflation, Treasury market, Fed credibility, and policy path news.', 'active'),
    ('internal_theme', 'subtheme', 'ENERGY_GEOPOLITICS', 'Energy and Geopolitics', 'Oil, energy supply, commodity shock, and geopolitical risk news.', 'active')
on conflict (taxonomy_family, node_type, code) do update
set
    name = excluded.name,
    description = excluded.description,
    status = excluded.status;

with parent_node as (
    select node_id
    from ref.classification_node
    where taxonomy_family = 'internal_theme'
      and node_type = 'theme'
      and code = 'MARKET_NEWS_FLOW'
),
edge_rows(child_code) as (
    values
        ('US_MARKET_BREADTH'),
        ('AI_SEMICONDUCTOR_CYCLE'),
        ('MACRO_RATES_FED'),
        ('ENERGY_GEOPOLITICS')
)
insert into ref.classification_edge (
    parent_node_id,
    child_node_id,
    relation_type,
    weight,
    valid_from,
    valid_to
)
select
    p.node_id,
    c.node_id,
    'hierarchy',
    1.0::numeric,
    '2000-01-01'::date,
    null::date
from parent_node p
join edge_rows e on true
join ref.classification_node c
  on c.taxonomy_family = 'internal_theme'
 and c.node_type = 'subtheme'
 and c.code = e.child_code
on conflict (parent_node_id, child_node_id, relation_type, valid_from) do update
set
    weight = excluded.weight,
    valid_to = excluded.valid_to;

commit;
"""


def render_instrument_lookup_by_symbol_sql(symbol: str) -> str:
    return f"""select json_build_object(
    'instrument_id', i.instrument_id,
    'primary_symbol', i.primary_symbol,
    'instrument_name', i.name
)::text
from ref.instrument i
where i.is_active = true
  and lower(i.primary_symbol) = lower({sql_literal(symbol)})
order by i.instrument_id
limit 1;"""


def render_news_rss_cluster_evidence_event_candidates_sql(*, as_of_date: date, limit: int) -> str:
    if limit <= 0:
        raise ValueError("limit must be greater than 0")
    return f"""select coalesce(
    json_agg(
        json_build_object(
            'event_id', event_id,
            'document_id', document_id,
            'event_type', event_type,
            'title', title,
            'summary', summary,
            'event_at', event_at,
            'source_name', source_name,
            'external_document_id', external_document_id,
            'theme_key', theme_key,
            'theme_name', theme_name,
            'impact_direction', impact_direction,
            'impact_score', impact_score,
            'symbol', symbol
        )
        order by event_at desc, event_id desc
    ),
    '[]'::json
)::text
from (
    select
        e.event_id,
        d.document_id,
        e.event_type,
        e.title,
        e.summary,
        e.event_at,
        ds.source_name,
        d.external_document_id,
        theme.code as theme_key,
        theme.name as theme_name,
        coalesce(instrument_impact.impact_direction, classification_impact.impact_direction, e.impact_polarity, 'watch')
            as impact_direction,
        coalesce(instrument_impact.impact_strength, classification_impact.impact_strength, e.significance_score)
            as impact_score,
        instrument.primary_symbol as symbol
    from event.event e
    join event.event_classification_impact classification_impact
      on classification_impact.event_id = e.event_id
    join ref.classification_node theme
      on theme.node_id = classification_impact.node_id
     and theme.taxonomy_family = 'internal_theme'
    left join event.event_instrument_impact instrument_impact
      on instrument_impact.event_id = e.event_id
    left join ref.instrument instrument
      on instrument.instrument_id = instrument_impact.instrument_id
    left join event.event_document_link document_link
      on document_link.event_id = e.event_id
     and document_link.link_type = 'source'
    left join ingest.source_document d
      on d.document_id = document_link.document_id
    left join ingest.data_source ds
      on ds.data_source_id = d.data_source_id
    where e.event_type = 'news_rss_item'
      and e.dedupe_key like 'news_rss:%'
      and e.event_at < ({sql_literal(as_of_date.isoformat())}::date + interval '1 day')
    order by e.event_at desc, e.event_id desc
    limit {limit}
) candidates;"""


def render_existing_news_rss_cluster_artifact_lookup_sql(*, request_hash: str) -> str:
    return f"""select artifact.artifact_id::text
from ai.extraction_artifact artifact
join ai.model_invocation invocation
  on invocation.invocation_id = artifact.invocation_id
where artifact.artifact_type = 'news_cluster_summary'
  and invocation.request_hash = {sql_literal(request_hash)}
order by artifact.artifact_id desc
limit 1;"""


def render_news_rss_cluster_model_invocation_insert_sql(
    *,
    run_id: int,
    request_hash: str,
    task_name: str = "news_rss_cluster_evidence",
    provider: str = "local_rules",
    model_name: str = "news_cluster_summary_v1",
) -> str:
    return f"""insert into ai.model_invocation (
    run_id,
    task_name,
    provider,
    model_name,
    reasoning_effort,
    input_token_count,
    output_token_count,
    cached_input_token_count,
    estimated_cost_usd,
    latency_ms,
    status,
    request_hash
)
values (
    {run_id},
    {sql_literal(task_name)},
    {sql_literal(provider)},
    {sql_literal(model_name)},
    'none',
    0,
    0,
    0,
    0.000000,
    0,
    'succeeded',
    {sql_literal(request_hash)}
)
returning invocation_id;"""


def render_news_rss_cluster_extraction_artifact_insert_sql(
    *,
    invocation_id: int,
    document_id: int | None,
    event_id: int,
    output_json: str,
    confidence: float,
) -> str:
    document_literal = "null::bigint" if document_id is None else f"{document_id}::bigint"
    return f"""insert into ai.extraction_artifact (
    invocation_id,
    document_id,
    event_id,
    artifact_type,
    output_json,
    confidence
)
values (
    {invocation_id},
    {document_literal},
    {event_id},
    'news_cluster_summary',
    {sql_literal(output_json)}::jsonb,
    {confidence:.4f}
)
returning artifact_id;"""


def render_news_rss_ai_extraction_candidates_sql(
    *,
    as_of_date: date,
    limit: int,
    prompt_template_name: str = "news-rss-ai-extract",
    prompt_template_version: str | None = None,
) -> str:
    if limit <= 0:
        raise ValueError("limit must be greater than 0")
    version_filter = (
        ""
        if prompt_template_version is None
        else f"""
          join ai.prompt_template prompt
            on prompt.template_id = invocation.prompt_template_id
           and prompt.template_name = {sql_literal(prompt_template_name)}
           and prompt.template_version = {sql_literal(prompt_template_version)}"""
    )
    return f"""select coalesce(
    json_agg(
        json_build_object(
            'event_id', event_id,
            'document_id', document_id,
            'title', title,
            'summary', summary,
            'event_at', event_at,
            'source_name', source_name,
            'external_document_id', external_document_id,
            'source_url', source_url,
            'existing_theme_code', existing_theme_code,
            'existing_instrument_symbol', existing_instrument_symbol
        )
        order by rank_bucket, event_at desc, event_id desc
    ),
    '[]'::json
)::text
from (
    select
        e.event_id,
        d.document_id,
        e.title,
        e.summary,
        e.event_at,
        ds.source_name,
        d.external_document_id,
        d.url as source_url,
        theme.code as existing_theme_code,
        instrument.primary_symbol as existing_instrument_symbol,
        case
            when instrument.primary_symbol is not null then 0
            when theme.code is not null then 1
            else 2
        end as rank_bucket
    from event.event e
    join event.event_document_link document_link
      on document_link.event_id = e.event_id
     and document_link.link_type = 'source'
    join ingest.source_document d
      on d.document_id = document_link.document_id
     and d.document_type = 'news_rss_item'
    left join ingest.data_source ds
      on ds.data_source_id = d.data_source_id
    left join event.event_classification_impact classification_impact
      on classification_impact.event_id = e.event_id
    left join ref.classification_node theme
      on theme.node_id = classification_impact.node_id
     and theme.taxonomy_family = 'internal_theme'
    left join event.event_instrument_impact instrument_impact
      on instrument_impact.event_id = e.event_id
    left join ref.instrument instrument
      on instrument.instrument_id = instrument_impact.instrument_id
    where e.event_type = 'news_rss_item'
      and e.dedupe_key like 'news_rss:%'
      and e.event_at < ({sql_literal(as_of_date.isoformat())}::date + interval '1 day')
      and not exists (
          select 1
          from ai.extraction_artifact artifact
          join ai.model_invocation invocation
            on invocation.invocation_id = artifact.invocation_id
{version_filter}
          where artifact.event_id = e.event_id
            and artifact.artifact_type = 'news_event_candidate'
            and invocation.status = 'succeeded'
      )
    order by rank_bucket, e.event_at desc, e.event_id desc
    limit {limit}
) candidates;"""


def render_news_rss_ai_retrieval_context_sql(*, event_id: int, as_of_date: date, limit: int = 8) -> str:
    if limit <= 0:
        raise ValueError("limit must be greater than 0")
    return f"""select json_build_object(
    'as_of_date', {sql_literal(as_of_date.isoformat())},
    'event_id', {event_id},
    'known_themes',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'code', node.code,
                    'node_type', node.node_type,
                    'name', node.name,
                    'description', node.description
                )
                order by node.node_type, node.code
            )
            from ref.classification_node node
            where node.taxonomy_family = 'internal_theme'
              and node.status = 'active'
        ),
        '[]'::json
    ),
    'theme_edges',
    coalesce(
        (
            select json_agg(
                json_build_object(
                    'parent_code', parent_node.code,
                    'child_code', child_node.code,
                    'relation_type', edge.relation_type,
                    'weight', edge.weight
                )
                order by parent_node.code, child_node.code
            )
            from ref.classification_edge edge
            join ref.classification_node parent_node
              on parent_node.node_id = edge.parent_node_id
            join ref.classification_node child_node
              on child_node.node_id = edge.child_node_id
            where edge.valid_from <= {sql_literal(as_of_date.isoformat())}::date
              and (edge.valid_to is null or edge.valid_to >= {sql_literal(as_of_date.isoformat())}::date)
        ),
        '[]'::json
    ),
    'current_event_impacts',
    coalesce(
        (
            select json_agg(row_to_json(current_impacts))
            from (
                select
                    theme.code as theme_code,
                    classification_impact.impact_direction as theme_direction,
                    classification_impact.confidence as theme_confidence,
                    instrument.primary_symbol as symbol,
                    instrument_impact.impact_direction as instrument_direction,
                    instrument_impact.confidence as instrument_confidence
                from event.event current_event
                left join event.event_classification_impact classification_impact
                  on classification_impact.event_id = current_event.event_id
                left join ref.classification_node theme
                  on theme.node_id = classification_impact.node_id
                left join event.event_instrument_impact instrument_impact
                  on instrument_impact.event_id = current_event.event_id
                left join ref.instrument instrument
                  on instrument.instrument_id = instrument_impact.instrument_id
                where current_event.event_id = {event_id}
            ) current_impacts
        ),
        '[]'::json
    ),
    'recent_similar_events',
    coalesce(
        (
            select json_agg(row_to_json(recent_rows))
            from (
                select distinct on (recent.event_id)
                    recent.event_id,
                    recent.title,
                    recent.event_at,
                    theme.code as theme_code,
                    instrument.primary_symbol as symbol,
                    coalesce(instrument_impact.impact_direction, classification_impact.impact_direction, recent.impact_polarity)
                        as impact_direction
                from event.event anchor
                join event.event recent
                  on recent.event_type = 'news_rss_item'
                 and recent.event_id <> anchor.event_id
                 and recent.event_at < ({sql_literal(as_of_date.isoformat())}::date + interval '1 day')
                left join event.event_classification_impact anchor_theme
                  on anchor_theme.event_id = anchor.event_id
                left join event.event_classification_impact classification_impact
                  on classification_impact.event_id = recent.event_id
                 and (
                     anchor_theme.node_id is null
                     or classification_impact.node_id = anchor_theme.node_id
                 )
                left join ref.classification_node theme
                  on theme.node_id = classification_impact.node_id
                left join event.event_instrument_impact instrument_impact
                  on instrument_impact.event_id = recent.event_id
                left join ref.instrument instrument
                  on instrument.instrument_id = instrument_impact.instrument_id
                where anchor.event_id = {event_id}
                order by recent.event_id, recent.event_at desc
                limit {limit}
            ) recent_rows
        ),
        '[]'::json
    )
)::text;"""


def render_classification_node_lookup_by_code_sql(theme_code: str) -> str:
    return f"""select json_build_object(
    'node_id', node.node_id,
    'code', node.code,
    'node_type', node.node_type,
    'name', node.name
)::text
from ref.classification_node node
where node.taxonomy_family = 'internal_theme'
  and upper(node.code) = upper({sql_literal(theme_code)})
  and node.status = 'active'
order by node.node_id
limit 1;"""


def render_existing_news_ai_candidate_artifact_lookup_sql(*, event_id: int, request_hash: str) -> str:
    return f"""select artifact.artifact_id::text
from ai.extraction_artifact artifact
join ai.model_invocation invocation
  on invocation.invocation_id = artifact.invocation_id
where artifact.event_id = {event_id}
  and artifact.artifact_type = 'news_event_candidate'
  and invocation.request_hash = {sql_literal(request_hash)}
  and invocation.status = 'succeeded'
order by artifact.artifact_id desc
limit 1;"""


def render_news_ai_extraction_artifact_insert_sql(
    *,
    invocation_id: int,
    document_id: int,
    event_id: int,
    output_json: dict[str, object],
    confidence: float | None,
) -> str:
    output_text = json.dumps(output_json, ensure_ascii=False, sort_keys=True)
    return f"""insert into ai.extraction_artifact (
    invocation_id,
    document_id,
    event_id,
    artifact_type,
    output_json,
    confidence
)
values (
    {invocation_id},
    {document_id}::bigint,
    {event_id},
    'news_event_candidate',
    {sql_literal(output_text)}::jsonb,
    {sql_literal(confidence)}
)
returning artifact_id;"""


def _source_name(feed_name: str) -> str:
    cleaned = feed_name.strip()
    if not cleaned:
        raise ValueError("feed_name must not be empty")
    return f"rss_news:{cleaned}"


def _chunk(records: tuple[NewsRssItem, ...], size: int) -> Iterable[list[NewsRssItem]]:
    for index in range(0, len(records), size):
        yield list(records[index : index + size])
