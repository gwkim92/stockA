"""Read-only production verification. No models, scheduler actions or data mutations."""
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations.env_file import load_env_file_values
from activate_runtime import identity

BASE=Path('/opt/stockanalysis/runtime/recommendation-outcome-explorer-20260911')
API='http://127.0.0.1:8787/api/recommendation-outcomes'

def main():
    ident=identity()
    values=load_env_file_values('/opt/stockanalysis/runtime/frontend-api.env')
    os.environ.update(load_env_file_values('/opt/stockanalysis/runtime/data-operations.env'))
    os.environ['PGOPTIONS']='-c default_transaction_read_only=on -c statement_timeout=10000'
    executor=PsqlCommandExecutor.from_config(RuntimeConfig.from_env())
    def get(path,authenticated=True):
        request=urllib.request.Request(path,headers={'Authorization':'Bearer '+values['STOCKANALYSIS_FRONTEND_API_READ_TOKEN']} if authenticated else {})
        with urllib.request.urlopen(request,timeout=20) as response:
            assert response.headers['cache-control']=='no-store'
            return json.load(response)
    def fingerprint():
        result={}
        for table in ['signal.recommendation','signal.recommendation_score_component','portfolio.position_snapshot','ref.benchmark_composition','performance.recommendation_outcome']:
            result[table]=json.loads(executor.execute_scalar("select json_build_object('count',count(*),'hash',md5(coalesce(string_agg(row_hash,',' order by row_hash),'')))::text from (select md5(to_jsonb(r)::text) row_hash from "+table+" r) hashes;"))
        return result
    before=fingerprint()
    first=get(API+'?limit=100');through=first['pagination']['through']
    assert through.isdigit()
    expected=json.loads(executor.execute_scalar(f"select json_agg(outcome_id::text order by measurement_end_date desc,outcome_id desc)::text from performance.recommendation_outcome where outcome_id<={int(through)};")) or []
    ids=[];page=first;pages=0
    while True:
        pages+=1;assert pages<=100,'Unexpected pagination size'
        assert page['read_only'] and page['source']=='live'
        assert page['summary']==first['summary']
        ids.extend(row['outcome_id'] for row in page['rows'])
        if not page['pagination']['has_more']:break
        page=get(API+'?'+urllib.parse.urlencode({'limit':100,'before':page['pagination']['next_cursor'],'through':through}))
    assert ids==expected,'API rows differ from stored outcomes'
    scopes=[]
    for query,condition in [
        ({'symbol':'AAPL'},"i.primary_symbol='AAPL'"),
        ({'horizon':'30'},'o.horizon_days between 23 and 37'),
        ({'horizon':'90'},'o.horizon_days between 83 and 97'),
        ({'horizon':'other'},'not (o.horizon_days between 23 and 37 or o.horizon_days between 83 and 97 or o.horizon_days between 173 and 187 or o.horizon_days between 358 and 372)'),
        ({'benchmark':'_missing'},'o.benchmark_code is null'),
        ({'alpha':'zero'},'o.alpha_pct=0'),
        ({'alpha':'missing'},'o.alpha_pct is null'),
        ({'alpha':'positive'},'o.alpha_pct>0'),
        ({'alpha':'negative'},'o.alpha_pct<0'),
        ({'from_date':'2026-08-11','to_date':'2026-08-11'},"b.as_of_date='2026-08-11'"),
        ({'symbol':'NOSUCHSYMBOL'},"i.primary_symbol='NOSUCHSYMBOL'"),
    ]:
        report=get(API+'?'+urllib.parse.urlencode(query|{'through':through}))
        count=int(executor.execute_scalar(f"select count(*) from performance.recommendation_outcome o join signal.recommendation r using(recommendation_id) join signal.recommendation_batch b using(batch_id) join ref.instrument i using(instrument_id) where o.outcome_id<={int(through)} and {condition};"))
        assert report['summary']['measurement_count']==count,query
        scopes.append({'query':query,'count':count})
    snapshot_row=next((row for row in first['rows'] if row['evaluation_snapshot']),None)
    snapshot_check=None
    if snapshot_row:
        saved=snapshot_row['evaluation_snapshot']
        path='http://127.0.0.1:8787/api/recommendation-evaluation-comparisons/eval-run-'+saved['eval_run_id']+'?after='+str(int(saved['snapshot_id'])-1)+'&limit=1'
        comparison=get(path);snapshot=comparison['history']['snapshots'][0]
        assert snapshot['snapshot_id']==saved['snapshot_id']
        assert snapshot['source_recommendation_id']==snapshot_row['recommendation_id']
        assert snapshot['source_outcome_id']==snapshot_row['outcome_id']
        snapshot_check={'snapshot_id':snapshot['snapshot_id'],'recommendation_id':snapshot['source_recommendation_id'],'outcome_id':snapshot['source_outcome_id'],'integrity':comparison['comparisons'][0]['integrity']}
    errors=[]
    for path,auth,expected_status in [(API,False,401),(API+'?horizon=31',True,400),(API+'?symbol=AAPL&symbol=SPY',True,400)]:
        try:get(path,auth);raise AssertionError('Expected rejection')
        except urllib.error.HTTPError as error:
            assert error.code==expected_status
            errors.append(expected_status)
    after=fingerprint();assert before==after,'Protected data changed during read verification'
    result={'identity':ident,'summary':first['summary'],'rows_match_database':len(ids),'unique_outcome_ids':len(set(ids)),'page_count':pages,'through':through,'scopes':scopes,'snapshot':snapshot_check,'error_statuses':errors,'protected_tables_unchanged':after,'database_writes':False,'model_calls':0}
    (BASE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
