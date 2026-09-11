"""Bounded repair for the verified Yahoo GUID collision, after runtime activation.

Usage on the target host: PYTHONPATH=/opt/stockanalysis/app/src <venv-python> repair_runtime.py
Requires a saved quarantine-preview.json. No model invocation or financial writes.
"""
import json
import os
from pathlib import Path
import subprocess

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations.env_file import load_env_file_values
from stockanalysis.operations.news_source_consistency import preview_news_source_quarantine, quarantine_news_source
from activate_runtime import identity

BASE = Path('/opt/stockanalysis/runtime/news-source-consistency-20260911')
TABLES = {
    'recommendations': ('signal.recommendation', 'recommendation_id::text'),
    'components': ('signal.recommendation_score_component', "recommendation_id::text || ':' || component_name"),
    'positions': ('portfolio.position_snapshot', "portfolio_id::text || ':' || instrument_id::text || ':' || snapshot_date::text"),
    'benchmark': ('ref.benchmark_composition', 'md5(row_to_json(r)::text)'),
    'recommendation_outcomes': ('performance.recommendation_outcome', 'outcome_id::text'),
    'thesis_outcomes': ('performance.thesis_outcome', 'outcome_id::text'),
    'research': ('research.equity_research_artifact', 'artifact_id::text'),
}


def save(name, value):
    with (BASE/name).open('x') as file:
        json.dump(value, file, ensure_ascii=False, indent=2)


def protected(executor):
    result = {}
    for key, (table, key_sql) in TABLES.items():
        result[key] = json.loads(executor.execute_scalar(f"select coalesce(jsonb_object_agg({key_sql},md5(to_jsonb(r)::text)), '{{}}'::jsonb)::text from {table} r;"))
    for key, table, id_column in [('chunks','ai.document_chunk','chunk_id'),('extractions','ai.extraction_artifact','artifact_id')]:
        result[key] = json.loads(executor.execute_scalar(f"select coalesce(jsonb_object_agg({id_column}::text,md5(to_jsonb(r)::text)), '{{}}'::jsonb)::text from {table} r where document_id=22;"))
    return result


def main():
    os.umask(0o077)
    ident = identity()
    activation = json.loads((BASE/'activation.json').read_text())
    commit = subprocess.check_output(['git','-C','/opt/stockanalysis/app','rev-parse','HEAD'],text=True).strip()
    assert commit == activation['commit']
    assert not (BASE/'repair-started.json').exists(), 'Already attempted; inspect receipts instead of replaying'
    expected = json.loads((BASE/'quarantine-preview.json').read_text())
    os.environ.update(load_env_file_values('/opt/stockanalysis/runtime/data-operations.env'))
    executor = PsqlCommandExecutor.from_config(RuntimeConfig.from_env())
    preview = preview_news_source_quarantine(executor, document_id=22)
    assert preview == expected, 'Preview changed; inspect before attempting repair'
    assert [e['event_id'] for e in preview['snapshot']['events']] == [19]
    before = protected(executor)
    save('protected-before.json', before)
    save('repair-started.json', {'identity':ident,'commit':commit,'fingerprint':preview['fingerprint']})
    result = quarantine_news_source(executor, document_id=22, expected_fingerprint=preview['fingerprint'],
        expected_external_id='rss:yahoo-finance-news:a9942e6ecc582301998de621', expected_source_name='rss_news:yahoo-finance-news')
    save('repair-receipt.json', result)
    after = preview_news_source_quarantine(executor, document_id=22)
    save('quarantine-after.json', after)
    archived = json.loads(executor.execute_scalar(f"select (config_json->'snapshot')::text from ops.pipeline_run where run_id={int(result['archive_run_id'])};"))
    assert archived == preview['snapshot'], 'Archive mismatch'
    assert after['snapshot']['document']['document_type'] == 'news_rss_identity_conflict'
    assert not after['snapshot']['instrument_impacts'] and not after['snapshot']['classification_impacts']
    current = protected(executor)
    for table, rows in before.items():
        assert all(current[table].get(key) == value for key,value in rows.items()), f'Existing rows changed: {table}'
    report = {'result':result,'archive_matches_preview':True,'protected_rows_unchanged':{key:len(rows) for key,rows in before.items()},
              'ai_calls':0,'financial_writes':False,'schema_changes':False}
    save('repair-verified.json',report)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__': main()
