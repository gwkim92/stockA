"""Validate stored narrative fields before a display adapter stringifies them.

This is not financial scoring or semantic verification. Keep the established API
string/list shapes, with explicit field-quality metadata for rejected/unavailable
input. Never salvage only the valid elements of a malformed claim/source list.
"""
from __future__ import annotations

from typing import Any

POLICY = 'equity_display_contract_v1'
TEXT_FIELDS = ('title', 'korean_summary')
CLAIM_FIELDS = ('key_points', 'catalysts', 'risks', 'invalidation_conditions')
MAX_DATABASE_ID = 9223372036854775807


def _document_id(value: object) -> bool:
    if type(value) is int:
        return 0 < value <= MAX_DATABASE_ID
    if type(value) is not str:
        return False
    # Stored artifact source inventories contain database IDs. The existing API
    # builder converts them to source-document-N, without going through JS float.
    return (0 < len(value) <= 19 and value.isascii() and value.isdecimal()
            and value[0] != '0' and int(value) <= MAX_DATABASE_ID)


def prepare_equity_display(artifact: dict[str, Any]) -> tuple[dict[str, Any], dict[str, object]]:
    safe = dict(artifact)
    invalid: list[str] = []
    unavailable: list[str] = []
    for field in TEXT_FIELDS:
        value = artifact.get(field)
        if value is None:
            unavailable.append(field)
            safe[field] = ''
        elif type(value) is not str:
            invalid.append(field)
            safe[field] = ''
        else:
            safe[field] = value
    for field in (*CLAIM_FIELDS, 'source_document_ids'):
        value = artifact.get(field)
        if value is None:
            unavailable.append(field)
            safe[field] = []
        elif type(value) is not list or not all(
            _document_id(item) if field == 'source_document_ids' else type(item) is str
            for item in value
        ):
            invalid.append(field)
            safe[field] = []
        else:
            safe[field] = list(value)
    quality: dict[str, object] = {
        'policy': POLICY,
        'status': 'invalid_fields' if invalid else 'partial' if unavailable else 'complete',
        'invalid_fields': invalid,
        'unavailable_fields': unavailable,
    }
    return safe, quality
