"""One bounded production report, then same-symbol dedup; no quota override."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

from stockanalysis.ai.model_settings import inventory
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.operations.env_file import load_env_file_values
from stockanalysis.operations.research_report_refresh import run_research_report_refresh

APP = Path('/opt/stockanalysis/app')
BASE = Path('/opt/stockanalysis/runtime/research-source-refresh-20260911')


def capture(argv):
    deadline = time.monotonic() + 30
    while True:
        output = subprocess.check_output(argv, text=True, timeout=90).strip()
        if (not output or argv[:2] != ['systemctl', 'list-units']
            or '--state=running,activating' not in argv or time.monotonic() >= deadline):
            return output
        time.sleep(0.5)


def save(name, data):
    (BASE/name).write_text(json.dumps(data, indent=2, default=str)+'\n')


def settings():
    current = inventory()
    return {key: current[key] for key in ('revision', 'default_model', 'overrides')}


def hashes(db, symbol):
    # Only the selected report and operational AI logs are allowed to change.
    tables = ('signal.recommendation', 'signal.recommendation_score_component',
        'portfolio.position_snapshot', 'ref.benchmark_composition', 'performance.recommendation_outcome',
        'market.financial_statement_period', 'market.financial_metric_value', 'market.financial_metric_normalized')
    queries = {table: 'select * from '+table for table in tables}
    queries['other_reports'] = ("select a.* from research.equity_research_artifact a join ref.instrument i using(instrument_id) "
                               "where i.primary_symbol <> "+sql_literal(symbol)) if symbol else 'select * from research.equity_research_artifact'
    return {key: db.execute_scalar("select md5(coalesce(string_agg(h,',' order by h),'')) from "
        "(select md5(to_jsonb(r)::text) h from ("+query+") r) hashes;") for key, query in queries.items()}


def env_hashes():
    return {name: hashlib.sha256((BASE.parent/name).read_bytes()).hexdigest()
            for name in ('frontend-api.env', 'web.env', 'data-operations.env')}


def api(path):
    env = load_env_file_values(BASE.parent/'frontend-api.env')
    request = urllib.request.Request('http://127.0.0.1:8787'+path,
        headers={'Authorization': 'Bearer '+env['STOCKANALYSIS_FRONTEND_API_READ_TOKEN']})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)['data']


def main():
    spec = importlib.util.spec_from_file_location('activation', APP/'docs/tasks/research-automation-20260911/activate.py')
    activation = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(activation)
    identity = activation.identity()
    os.umask(0o077)
    BASE.mkdir(exist_ok=True, mode=0o700)
    if '--restore-timers' in sys.argv:
        checkpoint = BASE/'canary-started.json'
        if checkpoint.exists():
            timers = json.loads(checkpoint.read_text())['timers']
            assert len(set(timers))==14 and all(re.fullmatch(r'stockanalysis-operating-data-[a-z-]+\.timer', item) for item in timers)
            subprocess.run(['sudo', '-n', 'systemctl', 'start', *timers], check=True, timeout=90)
        return
    os.environ.update(load_env_file_values(BASE.parent/'data-operations.env'))
    config = RuntimeConfig.from_env()
    db = PsqlCommandExecutor.from_config(config)
    day = datetime.now(timezone.utc).date()
    planned = run_research_report_refresh(config=config, as_of_date=day, executor=db)
    if '--execute' not in sys.argv:
        print(json.dumps({'identity': identity, 'preview': planned}, default=str))
        return
    assert not (BASE/'canary-started.json').exists(), 'Inspect saved checkpoint; never repeat an ambiguous canary'
    timers = [line.split()[0] for line in capture(['systemctl', 'list-units', '--type=timer', '--state=active',
        '--plain', '--no-legend', 'stockanalysis-*']).splitlines()]
    assert len(timers) == 14, 'Timer inventory changed; review first'
    save('canary-started.json', {'timers': timers, 'stage': 'before_model_call', 'as_of_date': str(day)})
    try:
        subprocess.run(['sudo', '-n', 'systemctl', 'stop', *timers], check=True, timeout=90)
        assert not capture(['systemctl', 'list-units', '--type=service', '--state=running,activating',
            '--plain', '--no-legend', 'stockanalysis-operating-data-*']), 'Wait for existing batch'
        planned = run_research_report_refresh(config=config, as_of_date=day, executor=db)
        target = next((row['primary_symbol'] for row in planned['queue'] if row['state']=='due'), None)
        if not target:
            target = next((row['primary_symbol'] for row in planned['queue'] if row['state']=='current'), None)
        assert target, 'No source-backed target for live canary'
        before = {'identity': identity, 'as_of_date': str(day), 'symbol': target,
            'timers': timers, 'preview': planned, 'settings': settings(), 'env_hashes': env_hashes(),
            'protected_hashes': hashes(db, target)}
        save('canary-started.json', before)
        kwargs = dict(config=config, as_of_date=day, executor=db, symbol=target, model_name=planned['model_name'])
        first = run_research_report_refresh(**kwargs, execute=True)
        save('canary-first.json', first)
        claim_count = db.execute_scalar("select count(*) from ops.pipeline_run where pipeline_name='equity_source_refresh';")
        invocation_count = db.execute_scalar('select count(*) from ai.model_invocation;')
        second = run_research_report_refresh(**kwargs, execute=True)
        save('canary-second.json', second)
        assert second.get('provider_attempted') is False, second
        assert claim_count == db.execute_scalar("select count(*) from ops.pipeline_run where pipeline_name='equity_source_refresh';")
        assert invocation_count == db.execute_scalar('select count(*) from ai.model_invocation;')
        after = run_research_report_refresh(**kwargs)
        selected = next(row for row in after['queue'] if row['primary_symbol']==target)
        stock = api('/api/stocks/'+target)
        freshness = (stock.get('equity_research') or {}).get('financial_source_freshness')
        if first['status']=='succeeded':
            assert first['result_receipt']['outcome']=='primary'
            assert selected['state']=='current' and freshness['status']=='current', (selected, freshness)
        assert hashes(db, target)==before['protected_hashes'], 'Protected investment/source data changed'
        assert settings()==before['settings'] and env_hashes()==before['env_hashes'], 'Runtime settings changed'
        result = {'identity': identity, 'verified_at': datetime.now(timezone.utc).isoformat(),
            'commit': capture(['git', '-C', str(APP), 'rev-parse', 'HEAD']), 'symbol': target,
            'first': first, 'second': second, 'queue_state': selected['state'], 'financial_source_freshness': freshness,
            'daily_used_before': planned['daily_used'], 'daily_used_after': after['daily_used'],
            'same_symbol_no_extra_claim_or_invocation': True, 'protected_data_unchanged': True,
            'settings_unchanged': True, 'actual_generation_verified': first['status']=='succeeded'}
        save('canary-verification.json', result)
    finally:
        subprocess.run(['sudo', '-n', 'systemctl', 'start', *timers], check=True, timeout=90)
    active = [line.split()[0] for line in capture(['systemctl', 'list-units', '--type=timer', '--state=active',
        '--plain', '--no-legend', 'stockanalysis-*']).splitlines()]
    assert sorted(active)==sorted(timers)
    result['timers_restored'] = len(active)
    result['routes'] = {}
    for port, path in ((8787, '/__ready'), (3000, '/stocks/'+target), (13000, '/stocks/'+target)):
        with urllib.request.urlopen('http://127.0.0.1:'+str(port)+path, timeout=60) as response:
            assert response.status==200
            result['routes'][str(port)] = response.status
    save('canary-verification.json', result)
    print(json.dumps(result, default=str))


if __name__=='__main__':
    main()
