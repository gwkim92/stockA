"""Run on the existing host for read-only input diagnostics; print sizes only."""
import json
import os
from datetime import date
from stockanalysis.operations.env_file import load_env_file_values
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ai.cycle_graph_context import load_cycle_graph_context, load_cycle_graph_context_node_codes
from stockanalysis.ai import cycle_community_ai_summary as cycle
from stockanalysis.ai import equity_research_reporting as equity

os.environ.update(load_env_file_values('/opt/stockanalysis/runtime/data-operations.env'))
config = RuntimeConfig.from_env()
day = date(2026, 9, 10)

def inspect(name, context, select, budget):
    result = {'name':name,'budget':budget,'sizes':{k:len(json.dumps(v,ensure_ascii=False)) for k,v in context.items()}}
    try:
        chosen = select(context, max_context_chars=budget)
        result.update(status='fits',selected_chars=len(json.dumps(chosen,ensure_ascii=False)))
    except Exception as exc:
        result.update(status='failed',error=str(exc) if str(exc)=='input_budget_exceeded' else type(exc).__name__)
    print(json.dumps(result,ensure_ascii=False))

for code in load_cycle_graph_context_node_codes(config=config,as_of_date=day,limit=3):
    inspect(code,load_cycle_graph_context(config=config,node_code=code,as_of_date=day,limit=12),cycle._bounded_context_for_prompt,cycle.DEFAULT_MAX_CONTEXT_CHARS)
for symbol in ('NVDA','AAPL','ARM'):
    inspect(symbol,equity.load_equity_research_context(config=config,symbol=symbol,as_of_date=day),equity._bounded_context_for_prompt,equity.DEFAULT_MAX_CONTEXT_CHARS)
