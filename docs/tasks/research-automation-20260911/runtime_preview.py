"""Read-only runtime checks; only aggregate results leave the host."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import urllib.request

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations.env_file import load_env_file_values
from stockanalysis.operations.research_maintenance import run_research_maintenance
from stockanalysis.ai.equity_research_reporting import run_equity_research_reporting
from stockanalysis.frontend.live_adapter import render_frontend_data_health_state_sql


def identity():
    req=urllib.request.Request('http://169.254.169.254/latest/api/token',method='PUT',headers={'X-aws-ec2-metadata-token-ttl-seconds':'60'})
    with urllib.request.urlopen(req,timeout=3) as response: token=response.read().decode()
    req=urllib.request.Request('http://169.254.169.254/latest/dynamic/instance-identity/document',headers={'X-aws-ec2-metadata-token':token})
    with urllib.request.urlopen(req,timeout=3) as response: actual=json.load(response)
    assert (actual['accountId'],actual['instanceId'],actual['region'])==('115623963546','i-029d51b163fb07b61','us-east-1')
    return {k:actual[k] for k in ('accountId','instanceId','region')}


if __name__=='__main__':
    ident=identity()
    os.environ.update(load_env_file_values('/opt/stockanalysis/runtime/data-operations.env'))
    os.environ['PGOPTIONS']='-c default_transaction_read_only=on -c statement_timeout=60000'
    config=RuntimeConfig.from_env()
    db=PsqlCommandExecutor.from_config(config)
    day=datetime.now(timezone.utc).date()
    report=run_research_maintenance(config=config,as_of_date=day,artifact_root=Path('/opt/stockanalysis/runtime/research-automation-artifacts'),executor=db)
    ai=run_equity_research_reporting(config=config,as_of_date=day,provider='codex_oauth',executor=db,execute=False)
    health=json.loads(db.execute_scalar(render_frontend_data_health_state_sql()))
    print(json.dumps({'identity':ident,'queue':report['queue'],
        'research_preview':{k:ai.get(k) for k in ('status','symbol_count','symbol_preview','prepared_symbol_count','input_error_count','preview_error_count')},
        'data_health_sql_valid':True,'maintenance_job_in_health':any(r['job_id']=='research-maintenance' for r in health['pipeline_runs']),
        'database_writes':False,'model_calls':0},default=str))
