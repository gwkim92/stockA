"""Three free public SEC reads using the existing registered User-Agent; no DB writes."""
import json
import os
import time
from datetime import datetime, timezone
from stockanalysis.operations.env_file import load_env_file_values
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.sec.companyfacts import _load_companyfacts_payload

os.environ.update(load_env_file_values('/opt/stockanalysis/runtime/data-operations.env'))
config=RuntimeConfig.from_env()
result={'observed_at':datetime.now(timezone.utc).isoformat(),'provider':'SEC companyfacts','database_writes':False,'samples':{}}
for symbol,cik in [('NVDA','0001045810'),('AAPL','0000320193'),('ARM','0001973239')]:
    try:
        payload=_load_companyfacts_payload(cik,config=config,json_path=None)
        facts=payload.get('facts',{}).get('us-gaap',{})
        wanted=['Revenues','RevenueFromContractWithCustomerExcludingAssessedTax','NetIncomeLoss','GrossProfit','OperatingIncomeLoss','NetCashProvidedByUsedInOperatingActivities','PaymentsToAcquirePropertyPlantAndEquipment','PaymentsToAcquireProductiveAssets']
        chosen={}
        for name in wanted:
            values=[x for x in facts.get(name,{}).get('units',{}).get('USD',[]) if str(x.get('end',''))>='2024-01-01' and str(x.get('filed',''))<='2026-09-10']
            if values: chosen[name]=values
        result['samples'][symbol]={'status':'received','url':f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json','entity':payload.get('entityName'),'facts':chosen,'concept_count':len(facts)}
    except Exception as exc:
        result['samples'][symbol]={'status':'unavailable','error_type':type(exc).__name__}
    time.sleep(1)
print(json.dumps(result,ensure_ascii=False))
