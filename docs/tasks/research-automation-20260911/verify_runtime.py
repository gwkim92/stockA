"""Two-cycle evidence and protected-data fingerprints; no row export."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import sys

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations.env_file import load_env_file_values
from stockanalysis.operations.research_maintenance import render_queue_sql

BASE=Path('/opt/stockanalysis/runtime/research-automation-20260911')


def main():
    os.environ.update(load_env_file_values(BASE.parent/'data-operations.env'))
    db=PsqlCommandExecutor.from_config(RuntimeConfig.from_env())
    day=datetime.now(timezone.utc).date()
    queue=json.loads(db.execute_scalar(render_queue_sql(as_of_date=day)))
    baseline=BASE/'verification-before.json'
    if sys.argv[1]=='before':
        assert not baseline.exists(),'Do not replace an existing baseline'
        selected=[r for r in queue if r['state']=='due'][:6]
        assert len(selected)==6
        data={'as_of_date':day.isoformat(),'targets':selected,
              'before_run_id':int(db.execute_scalar('select max(run_id) from ops.pipeline_run;'))}
    else:
        data=json.loads(baseline.read_text())
        assert data['as_of_date']==day.isoformat()
    ids=','.join(str(r['instrument_id']) for r in data['targets'])
    queries={table:'select * from '+table for table in ('signal.recommendation','signal.recommendation_score_component',
        'portfolio.position_snapshot','ref.benchmark_composition','performance.recommendation_outcome','research.equity_research_artifact')}
    queries['other_periods']=f'select * from market.financial_statement_period where instrument_id not in ({ids})'
    queries['other_metrics']=f'select m.* from market.financial_metric_value m join market.financial_statement_period p using(period_id) where p.instrument_id not in ({ids})'
    queries['older_or_other_normalized']=f"select * from market.financial_metric_normalized where as_of_date < '{day}' or instrument_id not in ({ids})"
    hashes={key:db.execute_scalar("select md5(coalesce(string_agg(h,',' order by h),'')) from (select md5(to_jsonb(r)::text) h from ("+query+") r) hashes;") for key,query in queries.items()}
    if sys.argv[1]=='before':
        data['protected_hashes']=hashes;baseline.write_text(json.dumps(data,indent=2)+'\n')
        print(json.dumps({'baseline_saved':True,'selected_symbols':[r['primary_symbol'] for r in data['targets']]}));return
    assert hashes==data['protected_hashes'],'Protected data changed; inspect before retrying anything'
    rows=json.loads(db.execute_scalar(f"""select coalesce(jsonb_agg(jsonb_build_object('run_id',run_id,'status',status,'symbol',config_json->>'instrument_symbol',
        'fact_count',config_json->'fact_count','period_policy',config_json->>'period_policy','before_image_present',config_json ? 'backup_before') order by run_id),'[]')::text
        from ops.pipeline_run where run_id>{data['before_run_id']} and pipeline_name='research_statement_refresh';"""))
    assert len(rows)==6 and all(r['status']=='succeeded' and r['before_image_present'] for r in rows),rows
    assert len({r['symbol'] for r in rows})==6,'Duplicate collection across consecutive cycles'
    current={r['primary_symbol']:r['state'] for r in queue}
    assert all(current[r['symbol']]=='fresh' for r in rows)
    parents=json.loads(db.execute_scalar(f"select coalesce(jsonb_agg(jsonb_build_object('run_id',run_id,'status',status,'queue_counts',config_json->'queue_counts_after') order by run_id),'[]')::text from ops.pipeline_run where run_id>{data['before_run_id']} and pipeline_name='research_maintenance';"))
    assert len(parents)==2 and all(r['status']=='succeeded' for r in parents)
    report={'verified_at':datetime.now(timezone.utc).isoformat(),'parents':parents,'refreshes':rows,
            'two_cycles_no_duplicate':True,'protected_data_unchanged':True,'before_images_same_database':True,
            'queue_counts':{s:sum(r['state']==s for r in queue) for s in ('due','fresh','retry_wait','reconcile')}}
    (BASE/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))


if __name__=='__main__':main()
