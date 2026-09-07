"""Validate stored narrative fields before a display adapter stringifies them.

This is not financial scoring or semantic verification. Keep established API
shapes and explicit metadata; never salvage part of a malformed claim list.
"""
from __future__ import annotations

import re
from typing import Any

POLICY = 'equity_display_contract_v1'
TEXT_FIELDS = ('title', 'korean_summary')
CLAIM_FIELDS = ('key_points', 'catalysts', 'risks', 'invalidation_conditions')
MAX_DATABASE_ID = 9223372036854775807


def _positive_decimal(value: str) -> bool:
    return (0 < len(value) <= 19 and value.isascii() and value.isdecimal()
            and value[0] != '0' and int(value) <= MAX_DATABASE_ID)


def _document_id(value: object) -> bool:
    if type(value) is int:
        return 0 < value <= MAX_DATABASE_ID
    if type(value) is not str:
        return False
    if _positive_decimal(value):
        return True
    # Existing display contracts also carry prefixed source aliases, not only
    # numeric database IDs. Preserve them exactly; never guess an alias or URL.
    prefix = 'source-document-'
    if not value.startswith(prefix) or len(value) > 240:
        return False
    suffix = value[len(prefix):]
    if suffix.isdecimal():
        return _positive_decimal(suffix)
    return (suffix.lower() not in {'unknown', 'true', 'false', 'none', 'null', 'nan', 'infinity'}
            and re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', suffix) is not None)


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
