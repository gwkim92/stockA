"""Real SQL tests, restricted to a dedicated disposable PostgreSQL instance."""
from datetime import date
import json
import os
from pathlib import Path
import re
import subprocess
import unittest

from stockanalysis.ingest.sec.companyfacts import normalize_companyfacts_payload
from stockanalysis.ingest.sec.sql import render_sec_companyfacts_upsert_sql
from stockanalysis.operations.professional_equity_analysis import render_financial_metric_normalization_upsert_sql
from tests.test_financial_period_integrity import observed, fact, payload

ROOT = Path(__file__).resolve().parents[1]


class FinancialPeriodPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        socket = os.getenv('STOCKA_FINANCIAL_TEST_SOCKET')
        if not socket:
            raise unittest.SkipTest('Dedicated disposable PostgreSQL socket required')
        cls.root = Path(socket).resolve().parent
        if not re.fullmatch(r'stocka-financial-pg-[a-zA-Z0-9_-]+',cls.root.name) or cls.root.parent != Path('/tmp').resolve():
            raise RuntimeError('Only the task disposable instance is supported')
        if not (cls.root/'disposable-financial-test').is_file():
            raise RuntimeError('Missing disposable instance marker')
        binary = os.getenv('STOCKA_FINANCIAL_TEST_PSQL','psql')
        cls.command=[binary,'-X','-q','-A','-t','-v','ON_ERROR_STOP=1','-h',socket,'-p','55491','-d','stocka_financial_test']
        identity=cls.sql("select json_build_object('db',current_database(),'data',current_setting('data_directory'));")
        actual=json.loads(identity)
        if actual['db']!='stocka_financial_test' or Path(actual['data']).resolve()!=cls.root/'data':
            raise RuntimeError('Not the expected disposable database')

    @classmethod
    def sql(cls, sql):
        return subprocess.run(cls.command,input=sql,text=True,capture_output=True,check=True,timeout=30).stdout.strip()

    def setUp(self):
        schema='''drop schema if exists market,ref,ingest,ops cascade;
create schema market; create schema ref; create schema ingest; create schema ops;
create table ref.instrument(instrument_id bigint primary key,primary_symbol text);
create table ops.pipeline_run(run_id bigint primary key);
create table ingest.data_source(data_source_id bigint primary key,source_name text);
create table ingest.source_document(document_id bigint primary key,data_source_id bigint,external_document_id text);
insert into ref.instrument values (1,'ARM'),(2,'AAPL'),(3,'NVDA'),(4,'CONTROL');
insert into ops.pipeline_run values (1),(2),(3);
insert into ingest.data_source values (1,'sec_edgar');
'''
        for file,table in [('0002_priority_1_tables.sql','financial_statement_period'),
                           ('0002_priority_1_tables.sql','financial_metric_value'),
                           ('0021_professional_equity_analysis.sql','financial_metric_normalized')]:
            source=(ROOT/'db/migrations'/file).read_text()
            start=source.index('create table if not exists market.'+table+' (')
            schema+=source[start:source.index('\n);',start)+3]+'\n'
        self.sql(schema)

    def import_facts(self,p,instrument_id=1):
        sql=render_sec_companyfacts_upsert_sql(normalize_companyfacts_payload(p),instrument_id=instrument_id,source_run_id=1,chunk_size=3)
        self.sql(sql)

    def test_real_arm_growth_and_quarter_cash_flow_exclusion(self):
        for i,symbol in enumerate(('ARM','AAPL','NVDA'),1):
            self.import_facts(observed(symbol),i)
        sql=render_financial_metric_normalization_upsert_sql(as_of_date=date(2026,9,11),source_run_id=2,symbols=('ARM','AAPL','NVDA'))
        self.sql(sql)
        rows=json.loads(self.sql("select json_agg(t) from (select instrument_id,period_end,metric_code,metric_status,metric_value from market.financial_metric_normalized where (instrument_id=1 and period_end in ('2025-03-31','2026-03-31') and metric_code='revenue_growth_yoy') or (instrument_id=2 and period_end='2026-06-27' and metric_code='operating_cash_flow_margin') or (instrument_id=3 and period_end='2026-07-26' and metric_code='operating_cash_flow_margin')) t;"))
        self.assertEqual(len(rows),4)
        for row in rows:
            if row['instrument_id']==1:
                expected=4007/3233-1 if row['period_end']=='2025-03-31' else 4920/4007-1
                self.assertEqual(row['metric_status'],'computed')
                self.assertAlmostEqual(row['metric_value'],expected,places=7)
            else:
                self.assertEqual(row['metric_status'],'unavailable')
                self.assertIsNone(row['metric_value'])

    def test_reimport_removes_stale_ytd_and_keeps_period_id_and_other_symbols(self):
        self.import_facts(payload(Revenues=[fact()],NetIncomeLoss=[fact(val=20)]))
        period_id=self.sql('select period_id from market.financial_statement_period;')
        self.sql(f"insert into market.financial_metric_value values ({period_id},'operating_cash_flow',999,'USD',1),({period_id},'custom_metric',7,'USD',1);")
        self.import_facts(payload(Revenues=[fact()]),4)
        self.import_facts(payload(Revenues=[fact()],NetIncomeLoss=[fact(val=20)]))
        self.assertEqual(self.sql('select count(*) from market.financial_metric_value where metric_code=\'operating_cash_flow\';'),'0')
        self.assertEqual(self.sql('select count(*) from market.financial_metric_value where metric_code=\'custom_metric\';'),'1')
        self.assertEqual(self.sql('select period_id from market.financial_statement_period where instrument_id=1;'),period_id)
        self.assertEqual(self.sql('select count(*) from market.financial_statement_period where instrument_id=4;'),'1')

    def test_failed_reimport_rolls_back_metric_replacement(self):
        self.import_facts(payload(Revenues=[fact()],NetIncomeLoss=[fact(val=20)]))
        before=self.sql('select json_agg(t) from (select * from market.financial_metric_value order by period_id,metric_code) t;')
        sql=render_sec_companyfacts_upsert_sql(normalize_companyfacts_payload(payload(Revenues=[fact(val=120)])),instrument_id=1,source_run_id=2)
        with self.assertRaises(subprocess.CalledProcessError):
            self.sql(sql.replace('commit;','select 1/0; commit;'))
        self.assertEqual(self.sql('select json_agg(t) from (select * from market.financial_metric_value order by period_id,metric_code) t;'),before)

    def test_new_filing_does_not_retain_an_older_document_link(self):
        self.sql("insert into ingest.source_document values (1,1,'filing-2024');")
        self.import_facts(payload(Revenues=[fact()]))
        self.assertEqual(self.sql('select source_document_id from market.financial_statement_period;'),'1')
        self.import_facts(payload(Revenues=[fact(accn='new-filing',filed='2025-03-01')]))
        self.assertEqual(self.sql('select source_document_id is null from market.financial_statement_period;'),'t')

    def test_cutoff_unknown_publication_and_symbol_isolation(self):
        self.import_facts(payload(Revenues=[fact()]),1)
        self.import_facts(payload(Revenues=[fact()]),4)
        self.sql('update market.financial_statement_period set report_date=null where instrument_id=4;')
        for cutoff,expected in [(date(2025,1,31),0),(date(2025,2,1),14)]:
            self.sql(render_financial_metric_normalization_upsert_sql(as_of_date=cutoff,source_run_id=2,symbols=('ARM',)))
            self.assertEqual(int(self.sql(f"select count(*) from market.financial_metric_normalized where as_of_date='{cutoff}';")),expected)
        self.sql(render_financial_metric_normalization_upsert_sql(as_of_date=date(2025,2,2),source_run_id=2))
        self.assertEqual(self.sql('select count(*) from market.financial_metric_normalized where instrument_id=4;'),'0')
