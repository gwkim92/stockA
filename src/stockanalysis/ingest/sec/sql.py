from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone

from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.sec.models import (
    SecCompanyFactsSyncResult,
    SecCompanyFactsValueRecord,
    SecExtractedEventCandidate,
    SecFilingRecord,
    SecFilingsSyncResult,
)


def render_sec_filings_upsert_sql(
    result: SecFilingsSyncResult,
    *,
    ingested_by_run_id: int | None = None,
    chunk_size: int = 200,
) -> str:
    lines = ["begin;"]
    for chunk in _chunk(result.filings, chunk_size):
        lines.extend(
            [
                "",
                _render_document_upsert(chunk, ingested_by_run_id=ingested_by_run_id),
            ]
        )
    lines.extend(["", "commit;"])
    return "\n".join(lines) + "\n"


def render_sec_source_document_lookup_sql(external_document_id: str) -> str:
    return f"""select json_build_object(
    'document_id', d.document_id,
    'external_document_id', d.external_document_id,
    'title', d.title,
    'url', d.url,
    'raw_storage_uri', d.raw_storage_uri,
    'checksum', d.checksum
)::text
from ingest.source_document d
join ingest.data_source s on s.data_source_id = d.data_source_id
where s.source_name = 'sec_edgar'
  and d.external_document_id = {sql_literal(external_document_id)}
order by d.document_id desc
limit 1;"""


def render_sec_source_document_raw_update_sql(
    *,
    document_id: int,
    raw_storage_uri: str,
    checksum: str,
) -> str:
    return f"""update ingest.source_document
set
    raw_storage_uri = {sql_literal(raw_storage_uri)},
    checksum = {sql_literal(checksum)}
where document_id = {document_id};"""


def render_sec_event_source_document_lookup_sql(external_document_id: str) -> str:
    return f"""select json_build_object(
    'document_id', d.document_id,
    'external_document_id', d.external_document_id,
    'title', d.title,
    'summary', d.summary,
    'published_at', d.published_at,
    'raw_storage_uri', d.raw_storage_uri,
    'checksum', d.checksum
)::text
from ingest.source_document d
join ingest.data_source s on s.data_source_id = d.data_source_id
where s.source_name = 'sec_edgar'
  and d.external_document_id = {sql_literal(external_document_id)}
order by d.document_id desc
limit 1;"""


def render_sec_event_extract_sql(
    candidate: SecExtractedEventCandidate,
    *,
    created_by_run_id: int | None = None,
) -> str:
    run_literal = "null::bigint" if created_by_run_id is None else f"{created_by_run_id}::bigint"
    significance_literal = sql_literal(candidate.significance_score)
    confidence_literal = sql_literal(candidate.confidence)
    return f"""begin;

with upserted_event as (
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
    values (
        {sql_literal(candidate.event_type)},
        {sql_literal(candidate.title)},
        {sql_literal(candidate.summary)},
        {sql_literal(candidate.event_at.isoformat())}::timestamptz,
        {sql_literal(candidate.time_horizon)},
        {sql_literal(candidate.impact_polarity)},
        {significance_literal},
        {confidence_literal},
        {sql_literal(candidate.dedupe_key)},
        {run_literal}
    )
    on conflict (dedupe_key) where dedupe_key is not null do update
    set
        event_type = excluded.event_type,
        title = excluded.title,
        summary = excluded.summary,
        event_at = excluded.event_at,
        time_horizon = excluded.time_horizon,
        impact_polarity = excluded.impact_polarity,
        significance_score = excluded.significance_score,
        confidence = excluded.confidence,
        created_by_run_id = excluded.created_by_run_id
    returning event_id
)
insert into event.event_document_link (
    event_id,
    document_id,
    link_type
)
select
    u.event_id,
    {candidate.document_id},
    {sql_literal(candidate.link_type)}
from upserted_event u
on conflict (event_id, document_id, link_type) do nothing;

commit;
"""


def render_sec_pending_event_document_ids_sql(*, limit: int) -> str:
    if limit <= 0:
        raise ValueError("limit must be greater than 0")
    return f"""select coalesce(json_agg(external_document_id order by published_at, document_id), '[]'::json)::text
from (
    select
        d.external_document_id,
        d.published_at,
        d.document_id
    from ingest.source_document d
    join ingest.data_source s on s.data_source_id = d.data_source_id
    where s.source_name = 'sec_edgar'
      and d.raw_storage_uri is not null
      and d.external_document_id is not null
      and not exists (
          select 1
          from event.event_document_link l
          where l.document_id = d.document_id
            and l.link_type = 'source'
      )
    order by d.published_at nulls last, d.document_id
    limit {limit}
) pending;"""


def render_pending_sec_event_impact_candidates_sql(*, limit: int) -> str:
    if limit <= 0:
        raise ValueError("limit must be greater than 0")
    return f"""select coalesce(
    json_agg(
        json_build_object(
            'event_id', event_id,
            'event_type', event_type,
            'dedupe_key', dedupe_key,
            'title', title
        )
        order by event_at, event_id
    ),
    '[]'::json
)::text
from (
    select
        e.event_id,
        e.event_type,
        e.dedupe_key,
        e.title,
        e.event_at
    from event.event e
    where e.dedupe_key like 'sec_edgar:%'
      and not exists (
          select 1
          from event.event_classification_impact i
          where i.event_id = e.event_id
      )
    order by e.event_at nulls last, e.event_id
    limit {limit}
) pending;"""


def render_reporting_classification_bootstrap_sql() -> str:
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
    ('internal_theme', 'theme', 'PUBLIC_COMPANY_REPORTING', 'Public Company Reporting', 'Cross-cutting reporting theme for public company disclosures.', 'active'),
    ('internal_theme', 'subtheme', 'ANNUAL_REPORTING', 'Annual Reporting', 'Annual reporting cadence driven by Form 10-K filings.', 'active'),
    ('internal_theme', 'subtheme', 'QUARTERLY_REPORTING', 'Quarterly Reporting', 'Quarterly reporting cadence driven by Form 10-Q filings.', 'active'),
    ('internal_theme', 'subtheme', 'CURRENT_REPORTING', 'Current Reporting', 'Current reporting cadence driven by Form 8-K filings.', 'active'),
    ('internal_theme', 'subtheme', 'CORPORATE_GOVERNANCE', 'Corporate Governance', 'Governance and proxy-related reporting themes.', 'active')
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
      and code = 'PUBLIC_COMPANY_REPORTING'
),
edge_rows(child_code) as (
    values
        ('ANNUAL_REPORTING'),
        ('QUARTERLY_REPORTING'),
        ('CURRENT_REPORTING'),
        ('CORPORATE_GOVERNANCE')
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


def render_event_classification_impact_upsert_sql(
    *,
    event_id: int,
    node_code: str,
    node_type: str,
    impact_direction: str,
    impact_strength: float | None,
    confidence: float | None,
    rationale: str,
) -> str:
    return f"""insert into event.event_classification_impact (
    event_id,
    node_id,
    impact_direction,
    impact_strength,
    confidence,
    rationale
)
select
    {event_id},
    n.node_id,
    {sql_literal(impact_direction)},
    {sql_literal(impact_strength)},
    {sql_literal(confidence)},
    {sql_literal(rationale)}
from ref.classification_node n
where n.taxonomy_family = 'internal_theme'
  and n.node_type = {sql_literal(node_type)}
  and n.code = {sql_literal(node_code)}
on conflict (event_id, node_id) do update
set
    impact_direction = excluded.impact_direction,
    impact_strength = excluded.impact_strength,
    confidence = excluded.confidence,
    rationale = excluded.rationale;"""


def render_pending_sec_event_instrument_candidates_sql(*, limit: int) -> str:
    if limit <= 0:
        raise ValueError("limit must be greater than 0")
    return f"""select coalesce(
    json_agg(
        json_build_object(
            'event_id', event_id,
            'event_type', event_type,
            'dedupe_key', dedupe_key,
            'title', title,
            'summary', summary
        )
        order by event_at, event_id
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
        e.event_at
    from event.event e
    where e.dedupe_key like 'sec_edgar:%'
      and not exists (
          select 1
          from event.event_instrument_impact i
          where i.event_id = e.event_id
      )
    order by e.event_at nulls last, e.event_id
    limit {limit}
) pending;"""


def render_instrument_lookup_by_company_name_sql(company_name: str) -> str:
    return f"""select json_build_object(
    'instrument_id', i.instrument_id,
    'primary_symbol', i.primary_symbol,
    'instrument_name', i.name,
    'issuer_display_name', iss.display_name,
    'issuer_legal_name', iss.legal_name
)::text
from ref.instrument i
join ref.issuer iss on iss.issuer_id = i.issuer_id
where i.is_active = true
  and (
      lower(iss.display_name) = lower({sql_literal(company_name)})
      or lower(iss.legal_name) = lower({sql_literal(company_name)})
      or lower(i.name) = lower({sql_literal(company_name)})
  )
order by i.instrument_id
limit 1;"""


def render_event_instrument_impact_upsert_sql(
    *,
    event_id: int,
    instrument_id: int,
    impact_direction: str,
    impact_strength: float | None,
    confidence: float | None,
    rationale: str,
) -> str:
    return f"""insert into event.event_instrument_impact (
    event_id,
    instrument_id,
    impact_direction,
    impact_strength,
    confidence,
    rationale
)
values (
    {event_id},
    {instrument_id},
    {sql_literal(impact_direction)},
    {sql_literal(impact_strength)},
    {sql_literal(confidence)},
    {sql_literal(rationale)}
)
on conflict (event_id, instrument_id) do update
set
    impact_direction = excluded.impact_direction,
    impact_strength = excluded.impact_strength,
    confidence = excluded.confidence,
    rationale = excluded.rationale;"""


def render_sec_companyfacts_upsert_sql(
    result: SecCompanyFactsSyncResult,
    *,
    instrument_id: int,
    source_run_id: int | None = None,
    chunk_size: int = 200,
) -> str:
    lines = ["begin;"]
    for chunk in _chunk_companyfacts(result.values, chunk_size):
        lines.extend(
            [
                "",
                _render_companyfacts_upsert_chunk(
                    chunk,
                    instrument_id=instrument_id,
                    source_run_id=source_run_id,
                ),
            ]
        )
    lines.extend(["", "commit;"])
    return "\n".join(lines) + "\n"


def _render_document_upsert(records: list[SecFilingRecord], *, ingested_by_run_id: int | None) -> str:
    value_rows = ",\n        ".join(
        _render_document_value_tuple(record, ingested_by_run_id=ingested_by_run_id) for record in records
    )
    return f"""with sec_source as (
    select data_source_id
    from ingest.data_source
    where source_name = 'sec_edgar'
),
input_rows(
    external_document_id,
    document_type,
    title,
    summary,
    url,
    language,
    published_at,
    checksum,
    ingested_by_run_id
) as (
    values
        {value_rows}
)
insert into ingest.source_document (
    data_source_id,
    external_document_id,
    document_type,
    title,
    summary,
    url,
    language,
    published_at,
    raw_storage_uri,
    checksum,
    ingested_by_run_id
)
select
    s.data_source_id,
    i.external_document_id,
    i.document_type,
    i.title,
    i.summary,
    i.url,
    i.language,
    i.published_at,
    null::text,
    i.checksum,
    i.ingested_by_run_id
from sec_source s
join input_rows i on true
on conflict (data_source_id, external_document_id) where external_document_id is not null do update
set
    document_type = excluded.document_type,
    title = excluded.title,
    summary = excluded.summary,
    url = excluded.url,
    language = excluded.language,
    published_at = excluded.published_at,
    checksum = excluded.checksum,
    ingested_by_run_id = excluded.ingested_by_run_id;"""


def _render_companyfacts_upsert_chunk(
    records: list[SecCompanyFactsValueRecord],
    *,
    instrument_id: int,
    source_run_id: int | None,
) -> str:
    run_literal = "null::bigint" if source_run_id is None else f"{source_run_id}::bigint"
    value_rows = ",\n        ".join(_render_companyfacts_value_tuple(record) for record in records)
    return f"""with sec_source as (
    select data_source_id
    from ingest.data_source
    where source_name = 'sec_edgar'
),
input_rows(
    statement_scope,
    fiscal_year,
    fiscal_quarter,
    period_start,
    period_end,
    report_date,
    currency_code,
    is_audited,
    accession_number,
    metric_code,
    metric_value,
    unit
) as (
    values
        {value_rows}
),
resolved_input as (
    select
        {instrument_id}::bigint as instrument_id,
        i.statement_scope,
        i.fiscal_year,
        i.fiscal_quarter,
        i.period_start,
        i.period_end,
        i.report_date,
        i.currency_code,
        i.is_audited,
        d.document_id as source_document_id,
        i.metric_code,
        i.metric_value,
        i.unit
    from input_rows i
    left join sec_source s on true
    left join ingest.source_document d
      on d.data_source_id = s.data_source_id
     and d.external_document_id = i.accession_number
),
source_periods as (
    select
        r.instrument_id,
        r.statement_scope,
        max(r.fiscal_year)::integer as fiscal_year,
        max(r.fiscal_quarter)::smallint as fiscal_quarter,
        min(r.period_start)::date as period_start,
        r.period_end,
        max(r.report_date)::date as report_date,
        max(r.currency_code) as currency_code,
        bool_or(r.is_audited) as is_audited,
        max(r.source_document_id) as source_document_id
    from resolved_input r
    group by
        r.instrument_id,
        r.statement_scope,
        r.period_end
),
upsert_periods as (
    insert into market.financial_statement_period (
        instrument_id,
        statement_scope,
        fiscal_year,
        fiscal_quarter,
        period_start,
        period_end,
        report_date,
        currency_code,
        is_audited,
        source_document_id,
        source_run_id
    )
    select
        p.instrument_id,
        p.statement_scope,
        p.fiscal_year,
        p.fiscal_quarter,
        p.period_start,
        p.period_end,
        p.report_date,
        p.currency_code,
        p.is_audited,
        p.source_document_id,
        {run_literal}
    from source_periods p
    on conflict (instrument_id, statement_scope, period_end) do update
    set
        fiscal_year = excluded.fiscal_year,
        fiscal_quarter = excluded.fiscal_quarter,
        period_start = excluded.period_start,
        report_date = excluded.report_date,
        currency_code = excluded.currency_code,
        is_audited = excluded.is_audited,
        source_document_id = coalesce(excluded.source_document_id, market.financial_statement_period.source_document_id),
        source_run_id = excluded.source_run_id
    returning period_id, instrument_id, statement_scope, period_end
)
insert into market.financial_metric_value (
    period_id,
    metric_code,
    metric_value,
    unit,
    source_run_id
)
select
    p.period_id,
    r.metric_code,
    r.metric_value,
    r.unit,
    {run_literal}
from resolved_input r
join upsert_periods p
  on p.instrument_id = r.instrument_id
 and p.statement_scope = r.statement_scope
 and p.period_end = r.period_end
on conflict (period_id, metric_code) do update
set
    metric_value = excluded.metric_value,
    unit = excluded.unit,
    source_run_id = excluded.source_run_id;"""


def _render_companyfacts_value_tuple(record: SecCompanyFactsValueRecord) -> str:
    fiscal_quarter = "null::smallint" if record.fiscal_quarter is None else f"{record.fiscal_quarter}::smallint"
    report_date = "null::date" if record.report_date is None else f"{sql_literal(record.report_date.isoformat())}::date"
    return (
        f"({sql_literal(record.statement_scope)}, "
        f"{record.fiscal_year}, "
        f"{fiscal_quarter}, "
        f"{sql_literal(record.period_start.isoformat())}::date, "
        f"{sql_literal(record.period_end.isoformat())}::date, "
        f"{report_date}, "
        f"{sql_literal(record.currency_code)}, "
        f"{sql_literal(record.is_audited)}, "
        f"{sql_literal(record.accession_number)}, "
        f"{sql_literal(record.metric_code)}, "
        f"{record.metric_value}::numeric, "
        f"{sql_literal(record.unit)})"
    )


def _render_document_value_tuple(record: SecFilingRecord, *, ingested_by_run_id: int | None) -> str:
    published_at = datetime.combine(record.filing_date, datetime.min.time(), tzinfo=timezone.utc)
    title_suffix = record.primary_doc_description or record.company_name
    title = f"{record.form_type} - {title_suffix}"
    summary = _build_summary(record)
    run_literal = "null::bigint" if ingested_by_run_id is None else f"{ingested_by_run_id}::bigint"
    return (
        f"({sql_literal(record.accession_number)}, "
        f"{sql_literal('filing')}, "
        f"{sql_literal(title)}, "
        f"{sql_literal(summary)}, "
        f"{sql_literal(record.filing_url)}, "
        f"{sql_literal('en')}, "
        f"{sql_literal(published_at.isoformat())}::timestamptz, "
        f"{sql_literal(None)}, "
        f"{run_literal})"
    )


def _build_summary(record: SecFilingRecord) -> str:
    parts = [f"SEC {record.form_type} filing for {record.company_name}"]
    if record.primary_doc_description:
        parts.append(record.primary_doc_description)
    if record.items:
        parts.append(f"items: {record.items}")
    if record.file_number:
        parts.append(f"file number: {record.file_number}")
    return " | ".join(parts)


def _chunk(records: tuple[SecFilingRecord, ...], size: int) -> Iterable[list[SecFilingRecord]]:
    for index in range(0, len(records), size):
        yield list(records[index : index + size])


def _chunk_companyfacts(
    records: tuple[SecCompanyFactsValueRecord, ...],
    size: int,
) -> Iterable[list[SecCompanyFactsValueRecord]]:
    for index in range(0, len(records), size):
        yield list(records[index : index + size])
