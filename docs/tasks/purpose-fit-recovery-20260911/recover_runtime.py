"""One-time bounded recovery through existing backend services, on the verified host.

Run preflight, outcomes, then research separately. Receipts precede each write;
never replay an interrupted phase without inspecting its journal and DB state.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import date

from stockanalysis.operations.env_file import load_env_file_values
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations.recommendation_outcome_backfill import run_recommendation_outcome_backfill
from stockanalysis.operations.recommendation_outcome_calibration_sample_expansion import run_recommendation_outcome_calibration_sample_expansion
from stockanalysis.operations.recommendation_outcome_due_action_router import run_recommendation_outcome_due_action_router
from stockanalysis.ai.equity_research_reporting import run_equity_research_reporting

BASE = Path('/opt/stockanalysis/runtime/purpose-fit-recovery-20260911')
DAY = date(2026, 9, 10)
PARAMS = dict(market_code='US', strategy_name='long_term_core', horizon_type='long_term', limit=20)
TABLES = {
    'recommendations': ('signal.recommendation', 'recommendation_id::text'),
    'components': ('signal.recommendation_score_component', "recommendation_id::text || ':' || component_name"),
    'positions': ('portfolio.position_snapshot', "portfolio_id::text || ':' || instrument_id::text || ':' || snapshot_date::text"),
    'benchmark': ('ref.benchmark_composition', 'md5(row_to_json(r)::text)'),
    'recommendation_outcomes': ('performance.recommendation_outcome', 'outcome_id::text'),
    'thesis_outcomes': ('performance.thesis_outcome', 'outcome_id::text'),
}

def save(name, value):
    (BASE/name).write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str)+'\n')

def emit(phase, **values):
    print(json.dumps({'phase':phase, **values}, ensure_ascii=False, default=str), flush=True)

def fingerprints(executor):
    result = {}
    for key, (table, identity) in TABLES.items():
        rows = json.loads(executor.execute_scalar(f"select coalesce(json_object_agg({identity}, md5(row_to_json(r)::text)), '{{}}'::json)::text from {table} r;"))
        result[key] = rows
    return result

def preserved(before, after):
    for table, rows in before.items():
        assert all(after[table].get(key) == value for key,value in rows.items()), f'Existing rows changed: {table}'
        if not table.endswith('outcomes'):
            assert len(rows) == len(after[table]), f'Protected table size changed: {table}'

def receipt(name):
    with (BASE/name).open('x') as file:
        file.write(json.dumps({'started_at':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}))

def main():
    os.umask(0o077)
    phase = sys.argv[1]
    activation = json.loads((BASE/'activation.json').read_text())
    assert activation['identity']['accountId'] == '115623963546'
    assert activation['identity']['instanceId'] == 'i-029d51b163fb07b61'
    commit = subprocess.check_output(['git','-C','/opt/stockanalysis/app','rev-parse','HEAD'],text=True).strip()
    assert commit == activation['commit']
    os.environ.update(load_env_file_values('/opt/stockanalysis/runtime/data-operations.env'))
    config = RuntimeConfig.from_env(); executor = PsqlCommandExecutor.from_config(config)
    if phase == 'preflight':
        assert not (BASE/'recovery-before.json').exists()
        before = fingerprints(executor)
        preview = run_recommendation_outcome_backfill(config=config, due_on_date=DAY, execute=False, executor=executor, **PARAMS)
        save('recovery-before.json', before);save('outcome-preview.json',preview)
        emit(phase, commit=commit, table_counts={k:len(v) for k,v in before.items()}, candidate_count=preview['candidate_count'], missing_outcome_count=preview['missing_outcome_count'])
        return
    before = json.loads((BASE/'recovery-before.json').read_text())
    preserved(before, fingerprints(executor))
    receipt(phase+'-started.json')
    if phase == 'outcomes':
        total = 0
        for round_number in range(1, 7):
            preview = run_recommendation_outcome_backfill(config=config, due_on_date=DAY, execute=False, executor=executor, **PARAMS)
            if preview['candidate_count'] == 0: break
            receipt(f'outcomes-{round_number}-started.json')
            result = run_recommendation_outcome_backfill(config=config, due_on_date=DAY, execute=True, executor=executor, **PARAMS)
            save(f'outcomes-{round_number}.json',result)
            assert result['failed_candidate_count'] == 0
            written = result['execution']['recommendation_outcome_count']
            total += written
            emit(phase, round=round_number, run_id=result['run_id'], written=written)
            assert written > 0, 'No progress: inspect price gaps instead of retrying'
            preserved(before, fingerprints(executor))
        preview = run_recommendation_outcome_backfill(config=config, due_on_date=DAY, execute=False, executor=executor, **PARAMS)
        assert preview['candidate_count'] == 0, 'Bounded recovery needs another inspected phase'
        calibration = run_recommendation_outcome_calibration_sample_expansion(config=config, as_of_date=DAY, execute=True, executor=executor, **PARAMS)
        save('calibration.json',calibration)
        router = run_recommendation_outcome_due_action_router(config=config, as_of_date=DAY, execute=True, executor=executor, **PARAMS)
        save('router.json',router)
        emit(phase, new_outcomes=total, remaining_batches=0, calibration_run_id=calibration['run_id'], router=router)
    elif phase == 'research':
        for symbol in ('NVDA','AAPL','ARM'):
            receipt(f'research-{symbol}-started.json')
            result = run_equity_research_reporting(config=config, as_of_date=DAY, symbols=(symbol,), provider='codex_oauth', execute=True, executor=executor)
            save(f'research-{symbol}.json',result)
            emit(phase, symbol=symbol, result=result)
            assert result['failed_artifact_count'] == 0
            assert result['inserted_artifact_count'] == 1
            assert result['fallback_artifact_count'] == 0, 'Primary report failed; fallback is not recovery proof'
    else:
        raise ValueError('Unknown phase')
    after = fingerprints(executor);preserved(before,after)
    save(phase+'-verified.json', {'existing_rows_preserved':True,'table_counts':{key:len(value) for key,value in after.items()}})
    emit(phase, existing_rows_preserved=True, table_counts={key:len(value) for key,value in after.items()})

if __name__ == '__main__':
    main()
