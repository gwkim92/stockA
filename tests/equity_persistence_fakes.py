"""Synthetic acknowledgements for fake executors; no SQL execution claim."""
from __future__ import annotations
import json
import re


def fake_atomic_ack(sql: str, *, invocation_id: int = 8801, artifact_id: int = 9901) -> str:
    run_id = int(re.search(r'where p.run_id = (\d+)', sql)[1])
    request_hash = re.search(r"'request_hash', '([0-9a-f]{64})'", sql)[1]
    fallback = "'outcome', 'fallback'" in sql
    failed = int(re.search(r'where invocation_id = (\d+)', sql)[1]) if fallback else None
    artifact = sql.split('insert into research.equity_research_artifact', 1)[1]
    match = re.search(r"values \(\s*(\d+),\s*(?:date )?'(\d{4}-\d{2}-\d{2})'(?:\:\:date)?,\s*'full_equity_research',\s*'((?:[^']|'')*)',\s*'((?:[^']|'')*)'", artifact)
    if match is None:
        raise AssertionError('Fake executor cannot identify atomic artifact fields')
    instrument, day, provider, model = match.groups()
    receipt = {
        'policy': 'equity_atomic_result_v1', 'run_id': run_id, 'request_hash': request_hash,
        'outcome': 'fallback' if fallback else 'primary', 'artifact_id': artifact_id,
        'invocation_id': None if fallback else invocation_id, 'failed_invocation_id': failed,
        'instrument_id': int(instrument), 'as_of_date': day,
        'provider': provider.replace("''", "'"), 'model_name': model.replace("''", "'"),
        'invocation_fingerprint': 'a' * 64, 'result_fingerprint': 'b' * 64,
    }
    return json.dumps({'acknowledged': 1, 'receipt': receipt})
