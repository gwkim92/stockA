"""Read-only runtime evidence. Execute through SSH; JSON output contains no env values."""
import json
import os
import subprocess
import urllib.request
from datetime import date, datetime, timezone

from stockanalysis.operations.env_file import load_env_file_values
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.ai.equity_research_reporting import load_equity_research_context, _bounded_context_for_prompt

os.environ.update(load_env_file_values('/opt/stockanalysis/runtime/data-operations.env'))
os.environ['PGOPTIONS'] = '-c default_transaction_read_only=on -c statement_timeout=20000'
config = RuntimeConfig.from_env()
db = PsqlCommandExecutor.from_config(config)
values = load_env_file_values('/opt/stockanalysis/runtime/frontend-api.env')

def rows(sql):
    return json.loads(db.execute_scalar("select coalesce(jsonb_agg(t),'[]'::jsonb)::text from (" + sql + ") t;"))

def get(path):
    request = urllib.request.Request('http://127.0.0.1:8787' + path, headers={'Authorization': 'Bearer ' + values['STOCKANALYSIS_FRONTEND_API_READ_TOKEN']})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)

result = {'observed_at': datetime.now(timezone.utc).isoformat(), 'commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd='/opt/stockanalysis/app',text=True).strip(), 'read_only': True, 'model_calls': 0}
result['schema'] = rows("select table_schema,table_name,column_name,data_type from information_schema.columns where table_schema in ('market','ingest','macro','research','ref','ai','ops') order by table_schema,table_name,ordinal_position")
result['health'] = get('/api/data-health')
result['stocks'] = {}
result['contexts'] = {}
for symbol in ('NVDA','AAPL','ARM'):
    result['stocks'][symbol] = get('/api/stocks/' + symbol)
    context = load_equity_research_context(config=config,symbol=symbol,as_of_date=date(2026,9,10))
    result['contexts'][symbol] = {'full': context, 'selected': _bounded_context_for_prompt(context,max_context_chars=16000)}
print(json.dumps(result,ensure_ascii=False,default=str))
