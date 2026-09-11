"""Assert deployed API behavior; emit a compact verification report only."""
from datetime import date, datetime, timezone
import json
import os
import urllib.request

from stockanalysis.ai.equity_research_reporting import load_equity_research_context
from stockanalysis.frontend.research_content_review import report_fingerprint
from stockanalysis.frontend.research_review_records import REVIEW_RECORDS
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.env_file import load_env_file_values
from runtime_pilot import BASE, SERVICES, capture, identity, persist


def main():
    ident=identity()
    settings=load_env_file_values('/opt/stockanalysis/runtime/frontend-api.env')
    os.environ.update(load_env_file_values('/opt/stockanalysis/runtime/data-operations.env'))
    os.environ['PGOPTIONS']='-c default_transaction_read_only=on -c statement_timeout=20000'
    config=RuntimeConfig.from_env()
    results=[]
    for symbol,expected_period,artifact in [('ARM','2026-03-31','494'),('AAPL','2025-09-27','493'),('NVDA','2026-01-25','492')]:
        request=urllib.request.Request('http://127.0.0.1:8787/api/stocks/'+symbol,
            headers={'Authorization':'Bearer '+settings['STOCKANALYSIS_FRONTEND_API_READ_TOKEN']})
        with urllib.request.urlopen(request,timeout=30) as response:
            data=json.load(response)['data']
        model=data['financial_statement_model']
        assert model['latest_period_end']==expected_period
        assert model['latest_as_of_date']=='2026-09-11'
        growth=next(m for section in model['sections'] for m in section['metrics'] if m['metric_code']=='revenue_growth_yoy')
        assert growth['metric_status']=='computed' and growth['metric_value'] is not None
        report=data['equity_research']
        assert report['artifact_id']=='equity-research-artifact-'+artifact
        assert report['content_review']['status']=='needs_source_correction'
        assert report_fingerprint(report) in REVIEW_RECORDS
        context=load_equity_research_context(config=config,symbol=symbol,as_of_date=date(2026,9,11))
        assert {r['period_end'] for r in context['financial_metrics']}=={expected_period}
        results.append({'symbol':symbol,'financial_period':expected_period,'fiscal_year':model['latest_fiscal_year'],
                        'normalized_as_of_date':model['latest_as_of_date'],'computed_metric_count':model['computed_metric_count'],
                        'growth_computed':True,'report_preserved':True,'report_review_required':True,'ai_input_period_verified':True})
    services={unit:capture(['systemctl','is-active',unit]) for unit in SERVICES}
    assert all(status=='active' for status in services.values())
    pilot=json.loads((BASE/'completed.json').read_text())
    original_timers=json.loads((BASE/'started.json').read_text())['active_timers']
    assert all(capture(['systemctl','is-active',unit])=='active' for unit in original_timers)
    result={'observed_at':datetime.now(timezone.utc).isoformat(),'identity':ident,'symbols':results,'services':services,
            'restored_timer_count':len(original_timers),'protected_tables_unchanged':pilot['protected_tables_unchanged'],
            'settings_unchanged':pilot['settings_unchanged'],'manual_model_calls':0,'database_writes':False}
    persist('verification.json',result)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    main()
