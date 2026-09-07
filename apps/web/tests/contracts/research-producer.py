"""Feed the actual Python display producer synthetic records, never a DB/model.

Executed by the TypeScript contract test. stdout is data; no repository writes.
"""
from __future__ import annotations
from contextlib import ExitStack
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
with ExitStack() as guards:
    for target in ('socket.socket.connect', 'socket.create_connection', 'subprocess.Popen'):
        guards.enter_context(patch(target, side_effect=AssertionError('external IO forbidden')))
    from stockanalysis.frontend.live_adapter import _build_stock_equity_research_payload
    from tests.test_research_display_contract import artifact
    raw = artifact()
    malformed = {**raw, 'key_points': ['valid fragment', False, {'bad': 'synthetic-object'}],
                 'source_document_ids': [7001, True]}
    partial = {**raw}; partial.pop('risks')
    empty = {**raw, 'key_points': [], 'source_document_ids': []}
    result = {name: _build_stock_equity_research_payload(value) for name, value in
              [('valid', raw), ('malformed', malformed), ('partial', partial), ('empty', empty)]}
print(json.dumps(result, ensure_ascii=False, allow_nan=False))
