"""One-statement result persistence and read-only receipt reconciliation.

No schema change, automatic retry, model call or exactly-once delivery claim.
The failed primary attempt remains an independent audit record on fallback paths.
"""
from __future__ import annotations

from datetime import date
import re
from typing import Any

from stockanalysis.ai_agents.prompt_contract import PromptContractError, strict_json_object
from stockanalysis.ingest.macro.sql import sql_literal

POLICY = 'equity_atomic_result_v1'
RECEIPTS_KEY = 'equity_result_receipts_v1'


def _positive_id(value: object) -> bool:
    return type(value) is int and 0 < value <= 9223372036854775807


def _identity(run_id: int, request_hash: str) -> None:
    if not _positive_id(run_id) or not isinstance(request_hash, str) or not re.fullmatch('[0-9a-f]{64}', request_hash):
        raise PromptContractError('invalid_persistence_identity')


def _returning_all(sql: str, column: str) -> str:
    # Adapt only the known static RETURNING tail; never split SQL on semicolons
    # (a legitimate source string can contain them). Refuse a changed builder.
    tail = f'returning {column};'
    if not sql.endswith(tail):
        raise PromptContractError('persistence_builder_changed')
    return sql[:-len(tail)] + 'returning *'


def _fingerprint(alias: str) -> str:
    # JSONB canonical text comes from the same server on write and reconciliation.
    # The timestamp is not report content and its rendering depends on time zone.
    return f"encode(sha256(convert_to((to_jsonb({alias}) - 'created_at')::text, 'UTF8')), 'hex')"


def render_atomic_result_sql(*, context: dict[str, Any], response: Any, as_of_date: date,
                             run_id: int, prompt_template_id: int, request_hash: str,
                             failed_invocation_id: int | None = None) -> str:
    from stockanalysis.ai import equity_research_reporting as equity
    _identity(run_id, request_hash)
    if type(as_of_date) is not date or not _positive_id(prompt_template_id):
        raise PromptContractError('invalid_persistence_identity')
    if failed_invocation_id is not None and not _positive_id(failed_invocation_id):
        raise PromptContractError('invalid_failed_invocation_identity')
    instrument = context.get('instrument', {})
    if not _positive_id(instrument.get('instrument_id')):
        raise PromptContractError('invalid_persistence_instrument')
    artifact_sql = _returning_all(equity.render_equity_research_artifact_upsert_sql(
        context=context, response=response, as_of_date=as_of_date, source_run_id=run_id,
    ), 'artifact_id')
    if failed_invocation_id is None:
        invocation_sql = _returning_all(equity.render_equity_research_model_invocation_insert_sql(
            run_id=run_id, provider=response.provider, model_name=response.model_name,
            reasoning_effort=response.reasoning_effort, prompt_template_id=prompt_template_id,
            input_token_count=response.input_token_count, output_token_count=response.output_token_count,
            cached_input_token_count=response.cached_input_token_count,
            estimated_cost_usd=response.estimated_cost_usd, latency_ms=response.latency_ms,
            status='succeeded', error_summary=None, request_hash=request_hash,
        ), 'invocation_id')
    else:
        # A fallback is not another successful model generation. Its original
        # failed invocation must exist in this run with this exact request hash.
        if response.provider != equity.FIXTURE_PROVIDER:
            raise PromptContractError('fallback_provider_mismatch')
        invocation_sql = f"""select * from ai.model_invocation
where invocation_id = {failed_invocation_id} and run_id = {run_id}
  and task_name = {sql_literal(equity.DEFAULT_TASK_NAME)} and status = 'failed'
  and request_hash = {sql_literal(request_hash)} and prompt_template_id = {prompt_template_id}"""
    outcome = 'fallback' if failed_invocation_id is not None else 'primary'
    return f"""-- equity atomic result v1
with recorded_invocation as (
{invocation_sql}
), stored_artifact as (
{artifact_sql}
), assembled_receipt as (
    select jsonb_build_object(
        'policy', '{POLICY}', 'run_id', {run_id}, 'request_hash', {sql_literal(request_hash)},
        'outcome', '{outcome}',
        'invocation_id', {'null' if failed_invocation_id is not None else 'i.invocation_id'},
        'failed_invocation_id', {'i.invocation_id' if failed_invocation_id is not None else 'null'},
        'artifact_id', a.artifact_id, 'instrument_id', a.instrument_id,
        'as_of_date', a.as_of_date, 'provider', a.provider, 'model_name', a.model_name,
        'invocation_fingerprint', {_fingerprint('i')},
        'result_fingerprint', {_fingerprint('a')}
    ) as receipt
    from recorded_invocation i cross join stored_artifact a
), stored_receipt as (
    update ops.pipeline_run p
    set config_json = jsonb_set(coalesce(p.config_json, '{{}}'::jsonb), '{{{RECEIPTS_KEY}}}',
        coalesce(p.config_json->'{RECEIPTS_KEY}', '{{}}'::jsonb)
        || jsonb_build_object({sql_literal(request_hash)}, r.receipt), true)
    from assembled_receipt r
    where p.run_id = {run_id} and p.pipeline_name = {sql_literal(equity.DEFAULT_PIPELINE_NAME)}
      and p.status = 'running'
      and jsonb_typeof(coalesce(p.config_json, '{{}}'::jsonb)) = 'object'
      and (p.config_json->'{RECEIPTS_KEY}' is null
           or jsonb_typeof(p.config_json->'{RECEIPTS_KEY}') = 'object')
      and not (coalesce(p.config_json->'{RECEIPTS_KEY}', '{{}}'::jsonb) ? {sql_literal(request_hash)})
    returning p.run_id
)
-- A missing/closed/wrong run, invalid receipt container, duplicate request, or
-- missing failed attempt must roll back the *whole statement*, not commit an
-- orphan artifact and merely return no rows. The scalar aggregate always runs.
select jsonb_build_object(
    'acknowledged', 1 / (select count(*) from stored_receipt),
    'receipt', (select receipt from assembled_receipt)
)::text;"""


_RECEIPT_KEYS = frozenset({
    'policy', 'run_id', 'request_hash', 'outcome', 'invocation_id', 'failed_invocation_id',
    'artifact_id', 'instrument_id', 'as_of_date', 'provider', 'model_name',
    'invocation_fingerprint', 'result_fingerprint',
})


def validate_receipt(value: object, *, run_id: int, request_hash: str) -> dict[str, Any]:
    data = strict_json_object(value)
    if set(data) != _RECEIPT_KEYS or data.get('policy') != POLICY:
        raise PromptContractError('invalid_result_receipt')
    if type(data['run_id']) is not int or data['run_id'] != run_id or data['request_hash'] != request_hash:
        raise PromptContractError('receipt_identity_mismatch')
    if data['outcome'] not in ('primary', 'fallback'):
        raise PromptContractError('invalid_receipt_outcome')
    primary = data['outcome'] == 'primary'
    present, absent = ('invocation_id', 'failed_invocation_id') if primary else ('failed_invocation_id', 'invocation_id')
    if not all(_positive_id(data[k]) for k in (present, 'artifact_id', 'instrument_id')) or data[absent] is not None:
        raise PromptContractError('invalid_receipt_identifiers')
    if any(not isinstance(data[k], str) or not re.fullmatch('[0-9a-f]{64}', data[k])
           for k in ('invocation_fingerprint', 'result_fingerprint')):
        raise PromptContractError('invalid_receipt_fingerprint')
    try:
        if date.fromisoformat(data['as_of_date']).isoformat() != data['as_of_date']:
            raise ValueError
    except (TypeError, ValueError):
        raise PromptContractError('invalid_receipt_date') from None
    if any(type(data[k]) is not str or not data[k].strip() for k in ('provider', 'model_name')):
        raise PromptContractError('invalid_receipt_provider')
    return data


def parse_acknowledgement(raw: object, *, run_id: int, request_hash: str) -> dict[str, Any]:
    data = strict_json_object(raw)
    if set(data) != {'acknowledged', 'receipt'} or type(data['acknowledged']) is not int or data['acknowledged'] != 1:
        raise PromptContractError('invalid_result_acknowledgement')
    return validate_receipt(data['receipt'], run_id=run_id, request_hash=request_hash)


def render_reconciliation_sql(*, run_id: int, request_hash: str) -> str:
    from stockanalysis.ai import equity_research_reporting as equity
    _identity(run_id, request_hash)
    return f"""-- equity result reconciliation v1 (read only; no automatic retry)
with expected as (
    select (select p.config_json->'{RECEIPTS_KEY}'->{sql_literal(request_hash)}
            from ops.pipeline_run p where p.run_id = {run_id}
            and p.pipeline_name = {sql_literal(equity.DEFAULT_PIPELINE_NAME)}) as receipt
), observed as (
    select e.receipt, i.invocation_id, a.artifact_id,
        coalesce(
            e.receipt->>'policy' = '{POLICY}'
            and e.receipt->>'run_id' = '{run_id}'
            and e.receipt->>'request_hash' = {sql_literal(request_hash)}
            and i.run_id = {run_id} and i.task_name = {sql_literal(equity.DEFAULT_TASK_NAME)}
            and i.request_hash = {sql_literal(request_hash)}
            and ((e.receipt->>'outcome' = 'primary' and i.status = 'succeeded'
                  and e.receipt->'failed_invocation_id' = 'null'::jsonb
                  and a.provider = i.provider and a.model_name = i.model_name)
                 or (e.receipt->>'outcome' = 'fallback' and i.status = 'failed'
                     and e.receipt->'invocation_id' = 'null'::jsonb and a.provider = '{equity.FIXTURE_PROVIDER}'))
            and a.source_run_id = {run_id} and a.artifact_type = {sql_literal(equity.ARTIFACT_TYPE)}
            and a.instrument_id::text = e.receipt->>'instrument_id'
            and to_jsonb(a.as_of_date) = e.receipt->'as_of_date'
            and a.provider = e.receipt->>'provider' and a.model_name = e.receipt->>'model_name'
            and {_fingerprint('i')} = e.receipt->>'invocation_fingerprint'
            and {_fingerprint('a')} = e.receipt->>'result_fingerprint', false
        ) as matches
    from expected e
    left join ai.model_invocation i on i.invocation_id::text =
        coalesce(e.receipt->>'invocation_id', e.receipt->>'failed_invocation_id')
    left join research.equity_research_artifact a on a.artifact_id::text = e.receipt->>'artifact_id'
)
select jsonb_build_object(
    'status', case when receipt is null then 'not_observed' when matches then 'matching' else 'conflicting' end,
    'receipt', receipt
)::text from observed;"""


def reconcile_result(executor: Any, *, run_id: int, request_hash: str) -> dict[str, Any]:
    # Deliberately callable but not invoked automatically during a DB outage.
    # A snapshot read cannot authorize a retry while another transaction is live.
    raw = executor.execute_scalar(render_reconciliation_sql(run_id=run_id, request_hash=request_hash))
    payload = strict_json_object(raw)
    if set(payload) != {'status', 'receipt'} or payload['status'] not in ('not_observed', 'matching', 'conflicting'):
        raise PromptContractError('invalid_reconciliation_response')
    receipt = None
    if payload['receipt'] is not None:
        receipt = validate_receipt(payload['receipt'], run_id=run_id, request_hash=request_hash)
    if (payload['status'] == 'not_observed') != (receipt is None):
        raise PromptContractError('inconsistent_reconciliation_response')
    return {**payload, 'receipt': receipt, 'automatic_retry_allowed': False,
            'observation_scope': 'current_database_snapshot_not_a_retry_authorization'}
