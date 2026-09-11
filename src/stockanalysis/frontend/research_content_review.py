"""Source-audit records bound to exact stored report content, never inferred approval."""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from stockanalysis.frontend.research_review_records import REVIEW_RECORDS

_FIELDS = (
    'artifact_id', 'as_of_date', 'provider', 'model_name', 'title', 'korean_summary',
    'key_points', 'catalysts', 'risks', 'invalidation_conditions',
    'valuation_sensitivity', 'source_document_ids', 'created_at',
)


def report_fingerprint(report: dict[str, Any]) -> str:
    payload = {key: report.get(key) for key in _FIELDS}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def content_review_for(report: dict[str, Any]) -> dict[str, Any]:
    record = REVIEW_RECORDS.get(report_fingerprint(report))
    if record is None:
        return {'status': 'not_recorded', 'scope': 'exact_report_content', 'human_approved': False}
    return copy.deepcopy(record)
