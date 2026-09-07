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
SOURCE_PREFIX = 'source-document-'
_RESERVED_IDS = {'unknown', 'true', 'false', 'none', 'null', 'nan', 'infinity'}


def _positive_decimal(value: str) -> bool:
    return (0 < len(value) <= 19 and value.isascii() and value.isdecimal()
            and value[0] != '0' and int(value) <= MAX_DATABASE_ID)


def _document_id(value: object) -> bool:
    if type(value) is int:
        return 0 < value <= MAX_DATABASE_ID
    if type(value) is not str:
        return False
    # The existing adapter accepts raw named IDs as well as numeric DB IDs.
    # Public prefixed IDs are unwrapped once before its own prefix conversion.
    raw = value[len(SOURCE_PREFIX):] if value.startswith(SOURCE_PREFIX) else value
    if not raw or len(raw) + len(SOURCE_PREFIX) > 240 or raw.startswith(SOURCE_PREFIX):
        return False
    if raw.isdecimal():
        return _positive_decimal(raw)
    return (raw.lower() not in _RESERVED_IDS
            and re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', raw) is not None)


def _adapter_document_id(value: int | str) -> int | str:
    return value[len(SOURCE_PREFIX):] if isinstance(value, str) and value.startswith(SOURCE_PREFIX) else value


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
            safe[field] = [_adapter_document_id(item) for item in value] if field == 'source_document_ids' else list(value)
    quality: dict[str, object] = {
        'policy': POLICY,
        'status': 'invalid_fields' if invalid else 'partial' if unavailable else 'complete',
        'invalid_fields': invalid,
        'unavailable_fields': unavailable,
    }
    return safe, quality
