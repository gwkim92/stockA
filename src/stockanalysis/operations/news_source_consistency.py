"""Preview and quarantine a confirmed RSS identity collision without erasing history.

This is an operator repair, never an automatic inference that news is incorrect.
The original source, events, links and active impacts are archived in pipeline_run.
Only active impact edges are removed; recommendations and stored AI outputs stay.
"""
from __future__ import annotations

import json
import re

from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.psql import PsqlCommandExecutor

QUARANTINED_SOURCE_TYPE = "news_rss_identity_conflict"
PIPELINE = "news-source-identity-quarantine"


def _snapshot_sql(document_id: int) -> str:
    if isinstance(document_id, bool) or not isinstance(document_id, int) or document_id <= 0:
        raise ValueError("A positive document ID is required")
    return f"""with document as (
    select * from ingest.source_document where document_id = {document_id}
), links as (
    select * from event.event_document_link where document_id = {document_id}
), events as (
    select e.* from event.event e where e.event_id in (select event_id from links)
)
select jsonb_build_object(
    'document', (select to_jsonb(d) from document d),
    'source_name', (select s.source_name from ingest.data_source s join document d using (data_source_id)),
    'links', coalesce((select jsonb_agg(to_jsonb(l) order by event_id, link_type) from links l), '[]'::jsonb),
    'events', coalesce((select jsonb_agg(to_jsonb(e) order by event_id) from events e), '[]'::jsonb),
    'other_source_links', (select count(*) from event.event_document_link
        where event_id in (select event_id from events) and document_id <> {document_id} and link_type = 'source'),
    'instrument_impacts', coalesce((select jsonb_agg(to_jsonb(i) order by event_id, instrument_id)
        from event.event_instrument_impact i where event_id in (select event_id from events)), '[]'::jsonb),
    'classification_impacts', coalesce((select jsonb_agg(to_jsonb(c) order by event_id, node_id)
        from event.event_classification_impact c where event_id in (select event_id from events)), '[]'::jsonb)
)"""


def preview_news_source_quarantine(executor: PsqlCommandExecutor, *, document_id: int) -> dict:
    sql = f"select jsonb_build_object('snapshot', snapshot, 'fingerprint', md5(snapshot::text))::text from ({_snapshot_sql(document_id)}) q(snapshot);"
    return json.loads(executor.execute_scalar(sql))


def render_news_source_quarantine_sql(*, document_id: int, expected_fingerprint: str,
                                     expected_external_id: str, expected_source_name: str) -> str:
    if not re.fullmatch(r"[a-f0-9]{32}", expected_fingerprint):
        raise ValueError("A preview fingerprint is required")
    snapshot_sql = _snapshot_sql(document_id)
    return f"""begin;
set local lock_timeout = '5s';
set local statement_timeout = '30s';
-- Short transaction blocks simultaneous ingest/enrichment while snapshotting edges.
lock table ingest.source_document, event.event, event.event_document_link,
    event.event_instrument_impact, event.event_classification_impact in share row exclusive mode;
create temporary table quarantine_receipt (result jsonb) on commit drop;
do $repair$
declare snapshot jsonb; archive_run_id bigint;
begin
    select value into snapshot from ({snapshot_sql}) q(value);
    if snapshot->'document'->>'external_document_id' is distinct from {sql_literal(expected_external_id)}
       or snapshot->>'source_name' is distinct from {sql_literal(expected_source_name)} then
        raise exception 'Source identity changed or document missing; refusing repair';
    end if;
    if snapshot->'document'->>'document_type' = '{QUARANTINED_SOURCE_TYPE}' then
        select run_id into archive_run_id from ops.pipeline_run
        where pipeline_name = '{PIPELINE}' and status = 'succeeded'
          and config_json->'snapshot'->'document'->>'document_id' = '{document_id}'
        order by run_id desc limit 1;
        if archive_run_id is null or jsonb_array_length(snapshot->'instrument_impacts') <> 0
            or jsonb_array_length(snapshot->'classification_impacts') <> 0 then
            raise exception 'Quarantine is incomplete; refusing replay';
        end if;
        insert into quarantine_receipt values (jsonb_build_object('status','already_quarantined','archive_run_id',archive_run_id));
        return;
    end if;
    if md5(snapshot::text) <> '{expected_fingerprint}' then
        raise exception 'Source or impact edges changed after preview; refusing repair';
    end if;
    if snapshot->'document'->>'document_type' <> 'news_rss_item'
       or (snapshot->>'other_source_links')::int <> 0
       or exists (select 1 from jsonb_array_elements(snapshot->'events') e where e->>'event_type' <> 'news_rss_item') then
        raise exception 'Repair requires isolated RSS source events';
    end if;
    insert into ops.pipeline_run (run_kind, pipeline_name, code_version, status, config_json)
    values ('remediation', '{PIPELINE}', 'news-source-consistency-v1', 'running',
        jsonb_build_object('reason','confirmed_shared_rss_guid', 'fingerprint','{expected_fingerprint}', 'snapshot',snapshot))
    returning run_id into archive_run_id;
    delete from event.event_instrument_impact where event_id in
        (select (e->>'event_id')::bigint from jsonb_array_elements(snapshot->'events') e);
    delete from event.event_classification_impact where event_id in
        (select (e->>'event_id')::bigint from jsonb_array_elements(snapshot->'events') e);
    update event.event set event_type = '{QUARANTINED_SOURCE_TYPE}' where event_id in
        (select (e->>'event_id')::bigint from jsonb_array_elements(snapshot->'events') e);
    update ingest.source_document set document_type = '{QUARANTINED_SOURCE_TYPE}' where document_id = {document_id};
    update ops.pipeline_run set status = 'succeeded', ended_at = now() where run_id = archive_run_id;
    insert into quarantine_receipt values (jsonb_build_object('status','quarantined','document_id',{document_id},
        'archive_run_id',archive_run_id, 'removed_instrument_impacts',jsonb_array_length(snapshot->'instrument_impacts'),
        'removed_classification_impacts',jsonb_array_length(snapshot->'classification_impacts')));
end $repair$;
select result::text from quarantine_receipt;
commit;"""


def quarantine_news_source(executor: PsqlCommandExecutor, **kwargs) -> dict:
    return json.loads(executor.execute_scalar(render_news_source_quarantine_sql(**kwargs)))
