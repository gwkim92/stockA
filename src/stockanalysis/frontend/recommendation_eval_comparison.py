"""Explicit current-state comparison; the original frozen-history reader stays isolated."""
from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any

from stockanalysis.frontend.recommendation_eval_history import (
    API_PATH as HISTORY_PATH, EVAL_NAME, EvaluationHistoryError, HistoryRequest,
    _positive_id, parse_evaluation_history_request, resolve_evaluation_history,
)
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations.recommendation_eval_persistence import canonical_snapshot_json

API_PATH = '/api/recommendation-evaluation-comparisons'


def is_evaluation_comparison_path(path: str) -> bool:
    return path.split('?', 1)[0] == API_PATH or path.startswith(API_PATH + '/')


def parse_comparison_request(path: str) -> HistoryRequest:
    if not path.startswith(API_PATH + '/eval-run-'):
        raise EvaluationHistoryError('Invalid evaluation comparison selector.', code='FrontendPaginationInvalid')
    return parse_evaluation_history_request(HISTORY_PATH + path[len(API_PATH):])


def verify_snapshot(row: dict[str, Any]) -> str:
    raw, expected = row.get('snapshot_json'), row.get('snapshot_sha256')
    if not isinstance(raw, dict) or not isinstance(expected, str) or len(expected) != 64:
        return 'unverifiable'
    try:
        # Match the persisted writer's canonicalization, including Unicode and numeric types.
        encoded = canonical_snapshot_json(raw).encode('utf-8')
        if not hmac.compare_digest(hashlib.sha256(encoded).hexdigest(), expected):
            return 'mismatch'
        recommendation = raw.get('recommendation')
        if not isinstance(recommendation, dict):
            return 'unverifiable'
        # These denormalized values are displayed beside the hashed payload.
        # Never mark the record verified if a copied field contradicts that payload.
        for column, field in (('recommendation_action', 'action'), ('recommendation_total_score', 'total_score')):
            if column in row and row[column] != recommendation.get(field):
                return 'mismatch'
        if recommendation.get('recommendation_id') is not None and str(recommendation['recommendation_id']) != row.get('source_recommendation_id'):
            return 'mismatch'
        instrument = raw.get('instrument')
        if isinstance(instrument, dict) and instrument.get('primary_symbol') != row.get('primary_symbol'):
            return 'mismatch'
        return 'verified'
    except (ValueError, TypeError, OverflowError, UnicodeError):
        return 'unverifiable'


def compare_snapshot(row: dict[str, Any], current: dict[str, Any] | None) -> dict[str, Any]:
    integrity = verify_snapshot(row)
    result = {'integrity': integrity, 'status': 'untrusted_history', 'changes': [], 'current': None, 'later_outcome': None}
    if integrity != 'verified':
        return result
    if current is None or current.get('recommendation') is None:
        return {**result, 'status': 'source_missing'}
    if current.get('primary_symbol') != row.get('primary_symbol'):
        return {**result, 'status': 'source_identity_mismatch'}
    changes = []
    fields = {
        'recommendation': ('action', 'total_score', 'status', 'recommended_weight', 'thesis_id'),
        'thesis': ('title', 'summary', 'status', 'conviction_score', 'invalidation_conditions'),
    }
    for section, names in fields.items():
        old = row['snapshot_json'].get(section) or {}
        new = current.get(section) or {}
        if not isinstance(old, dict) or not isinstance(new, dict):
            return {**result, 'status': 'unavailable'}
        for name in names:
            if old.get(name) != new.get(name):
                changes.append({'field': f'{section}.{name}', 'recorded': old.get(name), 'current': new.get(name)})
    return {**result, 'status': 'changed' if changes else 'unchanged', 'changes': changes,
            'current': current, 'later_outcome': current.get('later_outcome')}


def render_comparison_sql(run_id: int, snapshot_ids: list[str]) -> str:
    _positive_id(str(run_id))
    if not 1 <= len(snapshot_ids) <= 100:
        raise EvaluationHistoryError('Invalid comparison page.', code='FrontendPaginationInvalid')
    identifiers = ','.join(str(_positive_id(x)) for x in snapshot_ids)
    return f"""select coalesce(json_agg(json_build_object(
    'snapshot_id', s.snapshot_id::text,
    'recommendation', to_jsonb(r),
    'thesis', to_jsonb(t),
    'primary_symbol', i.primary_symbol,
    'observed_at', statement_timestamp(),
    'later_outcome', later.payload
) order by s.snapshot_id), '[]'::json)::text
from ai.recommendation_eval_snapshot s
join ai.eval_run e on e.eval_run_id = s.eval_run_id
left join signal.recommendation r on r.recommendation_id = s.source_recommendation_id
left join ref.instrument i on i.instrument_id = r.instrument_id
left join signal.investment_thesis t on t.thesis_id = r.thesis_id
left join lateral (
    select to_jsonb(o) || jsonb_build_object('outcome_id', o.outcome_id::text,
        'recommendation_id', o.recommendation_id::text) as payload
    from performance.recommendation_outcome o
    where o.recommendation_id = r.recommendation_id
      and o.horizon_days = coalesce(
        case when jsonb_typeof(s.snapshot_json->'selected_outcome'->'horizon_days') = 'number'
             then (s.snapshot_json->'selected_outcome'->>'horizon_days')::integer end,
        e.horizon_days)
      and o.measurement_end_date > e.as_of_date
      and o.measurement_end_date <= current_date
    order by o.measurement_end_date desc, o.outcome_id desc limit 1
) later on true
where s.eval_run_id = {run_id} and s.snapshot_id in ({identifiers})
  and e.eval_name = '{EVAL_NAME}';"""


def resolve_evaluation_comparison(path: str, *, source: str, config: RuntimeConfig | None = None,
                                 executor: Any | None = None) -> dict[str, Any]:
    request = parse_comparison_request(path)  # No DB/config access before validation.
    if source not in {'live', 'auto'}:
        raise EvaluationHistoryError('Evaluation history is unavailable.', code='FrontendLiveReadUnavailable')
    if executor is None:
        try:
            executor = PsqlCommandExecutor.from_config(config or RuntimeConfig.from_env())
        except Exception as exc:
            raise EvaluationHistoryError('Evaluation history is unavailable.', code='FrontendLiveReadUnavailable') from exc
    history = resolve_evaluation_history(HISTORY_PATH + path[len(API_PATH):], source=source, config=config, executor=executor)
    rows = history['snapshots']
    current_by_id = {}
    available = True
    if rows:
        try:
            data = json.loads(executor.execute_scalar(render_comparison_sql(request.eval_run_id, [r['snapshot_id'] for r in rows])))
            expected = {r['snapshot_id'] for r in rows}
            if not isinstance(data, list) or len(data) != len(rows):
                raise ValueError('incomplete comparison page')
            current_by_id = {r['snapshot_id']: r for r in data}
            if set(current_by_id) != expected:
                raise ValueError('comparison identity mismatch')
        except Exception:
            # Frozen records and integrity remain readable when current sources are unavailable.
            available = False
    comparisons = []
    for row in rows:
        comparison = compare_snapshot(row, current_by_id.get(row['snapshot_id'])) if available else {
            'status': 'unavailable', 'integrity': verify_snapshot(row), 'changes': [], 'current': None, 'later_outcome': None,
        }
        comparisons.append({'snapshot_id': row['snapshot_id'], **comparison})
    return {'contract_version': 'recommendation-eval-comparison-v1', 'history': history,
            'comparisons': comparisons, 'comparison_status': 'available' if available else 'unavailable',
            'compared_at': datetime.now(timezone.utc).isoformat(), 'read_only': True,
            'later_outcome_basis': 'after_evaluation_as_of_date_same_horizon_not_incremental_return',
            'snapshot_hash_verification': 'returned_page_only', 'order_boundary': 'read_only_no_order'}
