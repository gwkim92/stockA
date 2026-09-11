"""Read-only projection of the exact automatic research worker queue."""
from collections import Counter
from datetime import datetime, timedelta, timezone
import re
from typing import Any

from stockanalysis.operations.research_report_refresh import run_research_report_refresh

STATES = frozenset({'current', 'due', 'waiting_for_source', 'retry_wait',
                    'reconcile', 'attempt_recorded', 'result_changed'})
ATTENTION = frozenset({'reconcile', 'attempt_recorded', 'result_changed', 'unknown'})


def _timestamp(value: Any) -> str | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc).isoformat()
    except (ValueError, TypeError):
        return None


def _run_id(value: Any) -> int | None:
    return value if type(value) is int and value > 0 else None


def load_research_refresh_status(*, config: Any, executor: Any, now: datetime | None = None) -> dict[str, Any]:
    observed = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    base = {'observed_at': observed.isoformat(), 'as_of_date': observed.date().isoformat(),
            'scope': 'financial_source_only', 'read_only': True, 'maximum_calls_per_run': 1,
            'budget_resets_at': (observed.replace(hour=0, minute=0, second=0, microsecond=0)
                                 + timedelta(days=1)).isoformat()}
    try:
        # execute=False never reconciles claims, reserves calls, or invokes AI.
        planned = run_research_report_refresh(config=config, executor=executor,
            as_of_date=observed.date(), execute=False)
        used, limit = planned['daily_used'], planned['daily_limit']
        if type(used) is not int or used < 0 or type(limit) is not int or limit <= 0:
            raise ValueError('invalid_budget')
        rows = []
        for row in planned['queue']:
            symbol = row.get('primary_symbol')
            if not isinstance(symbol, str) or not re.fullmatch(r'[A-Z0-9][A-Z0-9.-]{0,19}', symbol):
                raise ValueError('invalid_symbol')
            state = row.get('state') if row.get('state') in STATES else 'unknown'
            rows.append({'symbol': symbol, 'state': state,
                'source_run_id': _run_id(row.get('source_run_id')),
                'source_collected_at': _timestamp(row.get('ended_at')),
                'claim_id': _run_id(row.get('previous_claim_id')),
                'retry_after': _timestamp(row.get('retry_after')),
                'failure_code': 'report_not_completed' if row.get('failure_code') == 'report_not_completed' else None})
        counts = dict(Counter(row['state'] for row in rows))
        attention = sum(counts.get(state, 0) for state in ATTENTION)
        return {**base, 'status': 'attention_required' if attention else 'loaded',
                'model_name': planned['model_name'], 'daily_used': used, 'daily_limit': limit,
                'daily_remaining': max(0, limit-used), 'counts': counts, 'attention_count': attention,
                'total_count': len(rows), 'rows': rows}
    except Exception:
        # An unavailable read is never presented as an empty healthy queue.
        # Do not expose database errors, source hashes, paths, or model session data.
        return {**base, 'status': 'unavailable', 'model_name': None, 'daily_used': None,
                'daily_limit': None, 'daily_remaining': None, 'counts': {}, 'attention_count': None,
                'total_count': None, 'rows': []}
