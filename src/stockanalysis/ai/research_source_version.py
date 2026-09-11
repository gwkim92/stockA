"""Financial input provenance; this is not a claim of complete research freshness."""
from __future__ import annotations

import re
import hashlib
import json
from typing import Any

from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.sec.financial_periods import PERIOD_POLICY

VERSION_KEY = "financial_source_versions"


def generation_policy(*, model: str, template: str, reasoning: str | None, context_limit: int) -> str:
    return hashlib.sha256(json.dumps({'policy': 'financial-source-report-refresh-v1', 'template': template,
        'model': model, 'reasoning': reasoning, 'context_limit': context_limit}, sort_keys=True).encode()).hexdigest()


def latest_source_sql(instrument_sql: str, *, cutoff_sql: str | None = None) -> str:
    # instrument_sql/cutoff_sql are internal SQL expressions, never request text.
    cutoff = f"and r.ended_at < {cutoff_sql}" if cutoff_sql else ""
    return f"""select r.run_id as source_run_id,
        r.config_json->>'source_sha256' as source_sha256,
        r.config_json->>'period_policy' as period_policy, r.ended_at
    from ops.pipeline_run r
    where r.pipeline_name='research_statement_refresh' and r.status='succeeded'
      and r.config_json->>'instrument_id'=({instrument_sql})::text
      and r.config_json->>'source_sha256' ~ '^[0-9a-f]{{64}}$'
      and r.config_json->>'period_policy'={sql_literal(PERIOD_POLICY)}
      and r.ended_at is not null {cutoff}
    order by r.ended_at desc, r.run_id desc limit 1"""


def validated_version(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if (not isinstance(value, dict) or type(value.get('source_run_id')) is not int
        or not 0 < value['source_run_id'] <= 9223372036854775807
        or not isinstance(value.get('source_sha256'), str)
        or not re.fullmatch('[0-9a-f]{64}', value['source_sha256'])
        or value.get('period_policy') != PERIOD_POLICY):
        raise ValueError('invalid_financial_source_version')
    return {key: value[key] for key in ('source_run_id', 'source_sha256', 'period_policy')}


def same_version(left: Any, right: Any) -> bool:
    a, b = validated_version(left), validated_version(right)
    return bool(a and b and all(a[key] == b[key] for key in ('source_sha256', 'period_policy')))


def freshness_sql(artifact_alias: str = 'artifact') -> str:
    return f"""(select jsonb_build_object(
        'input_version', g.config_json->'{VERSION_KEY}'->i.primary_symbol,
        'current_version', (select to_jsonb(s) from ({latest_source_sql('i.instrument_id')}) s)
    ) from ref.instrument i
    left join ops.pipeline_run g on g.run_id={artifact_alias}.source_run_id
    where i.instrument_id={artifact_alias}.instrument_id)"""


def public_freshness(value: Any) -> dict[str, Any]:
    raw = value if isinstance(value, dict) else {}
    try:
        used, current = validated_version(raw.get('input_version')), validated_version(raw.get('current_version'))
        status = ('source_unavailable' if not current else 'not_recorded' if not used
                  else 'current' if same_version(used, current) else 'source_changed')
    except ValueError:
        used, current, status = None, None, 'invalid_version'
    return {'status': status, 'scope': 'financial_source_only',
            'input_source_run_id': used['source_run_id'] if used else None,
            'current_source_run_id': current['source_run_id'] if current else None,
            'all_research_inputs_verified': False}
