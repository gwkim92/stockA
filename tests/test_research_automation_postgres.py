from datetime import date
import json
from pathlib import Path
import subprocess
import unittest

from tests import test_financial_period_integrity_postgres as fixture
from tests.test_financial_period_integrity import observed
from stockanalysis.ingest.sec.companyfacts import normalize_companyfacts_payload
from stockanalysis.ingest.sec.models import SecFilingsSyncResult
from stockanalysis.operations.research_maintenance import render_apply_sql, render_reconcile_sql, render_queue_sql
from stockanalysis.ai.equity_research_reporting import render_equity_research_symbol_lookup_sql


class ResearchAutomationPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.FinancialPeriodPostgresTests.setUpClass.__func__(cls)

    @classmethod
    def sql(cls, sql):
        return fixture.FinancialPeriodPostgresTests.sql.__func__(cls,sql)

    def setUp(self):
        fixture.FinancialPeriodPostgresTests.setUp(self)
        self.sql('''drop schema if exists signal,portfolio,research cascade;
create schema signal; create schema portfolio; create schema research;
alter table ref.instrument add column is_active boolean default true,
 add column market_code text default 'US', add column instrument_type text default 'common_stock', add column name text default 'Company';
alter table ops.pipeline_run add column pipeline_name text, add column status text default 'running',
 add column started_at timestamptz default now(), add column ended_at timestamptz,
 add column config_json jsonb default '{}', add column error_summary text;
create table signal.recommendation_batch(batch_id bigint,as_of_date date);
create table signal.recommendation(instrument_id bigint,batch_id bigint,status text,rank_position int);
create table portfolio.position_snapshot(instrument_id bigint,snapshot_date date);
create table research.equity_research_artifact(instrument_id bigint,as_of_date date,artifact_type text,provider text);
insert into signal.recommendation_batch values(1,'2026-09-11');
insert into signal.recommendation values(1,1,'active',1),(2,1,'active',2),(3,1,'active',3),(4,1,'active',4);
''')

    def apply_sql(self, run_id=1):
        result=normalize_companyfacts_payload(observed('ARM'))
        return render_apply_sql(result=result, filings=SecFilingsSyncResult(cik=result.cik,company_name='ARM',filings=()),
            instrument_id=1,symbol='ARM',as_of_date=date(2026,9,11),run_id=run_id)

    def fingerprint(self):
        return self.sql("select coalesce(jsonb_agg(to_jsonb(m) order by period_id,metric_code),'[]') from market.financial_metric_value m;")

    def test_atomic_commit_backup_and_reconciliation_no_replay(self):
        self.sql(self.apply_sql())
        self.assertEqual(self.sql('select status from ops.pipeline_run where run_id=1;'),'succeeded')
        self.assertEqual(json.loads(self.sql("select config_json->'backup_before' from ops.pipeline_run where run_id=1;")),
                         {'periods':[], 'metrics':[], 'normalized_today':[]})
        self.assertGreater(int(self.sql('select count(*) from market.financial_metric_normalized;')),0)
        self.assertEqual(self.sql(render_reconcile_sql(1)),'1\nsucceeded')
        before=self.fingerprint()
        with self.assertRaises(subprocess.CalledProcessError): self.sql(self.apply_sql())
        self.assertEqual(self.fingerprint(),before)

    def test_failure_after_raw_upsert_rolls_back_raw_normalized_and_receipt(self):
        self.sql(self.apply_sql())
        before=self.fingerprint()
        sql=self.apply_sql(2).replace("do $$ begin\n if not exists(select 1 from market.financial_metric_normalized", "select 1/0;\ndo $$ begin\n if not exists(select 1 from market.financial_metric_normalized")
        with self.assertRaises(subprocess.CalledProcessError): self.sql(sql)
        self.assertEqual(self.fingerprint(),before)
        self.assertEqual(self.sql('select count(*) from market.financial_metric_normalized where source_run_id=2;'),'0')
        self.sql("update ops.pipeline_run set pipeline_name='research_statement_refresh' where run_id=2;")
        self.assertEqual(self.sql(render_reconcile_sql(2)),'2\nfailed')

    def test_live_transaction_is_not_reconciled_as_rolled_back(self):
        self.sql("update ops.pipeline_run set pipeline_name='research_statement_refresh' where run_id=1;")
        process=subprocess.Popen(self.command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            process.stdin.write('begin; select run_id from ops.pipeline_run where run_id=1 for update;\n'); process.stdin.flush()
            self.assertEqual(process.stdout.readline().strip(),'1')
            with self.assertRaises(subprocess.CalledProcessError): self.sql(render_reconcile_sql(1))
            self.assertEqual(self.sql('select status from ops.pipeline_run where run_id=1;'),'running')
            process.stdin.write('rollback;\n');process.stdin.close();process.wait(timeout=5)
            self.assertEqual(self.sql(render_reconcile_sql(1)),'1\nfailed')
        finally:
            if process.poll() is None: process.kill();process.wait(timeout=5)
            process.stdout.close();process.stderr.close()

    def test_queue_policy_age_cooldown_and_fund_exclusion(self):
        self.sql('''update ops.pipeline_run set pipeline_name='research_statement_refresh',status='succeeded',ended_at=now(),
 config_json='{"instrument_id":1,"period_policy":"sec-statement-duration-v2"}' where run_id=1;
update ops.pipeline_run set pipeline_name='research_statement_refresh',status='failed',config_json='{"instrument_id":2}' where run_id=2;
update ops.pipeline_run set pipeline_name='sec_companyfacts_upsert',status='succeeded',ended_at=now(),
 config_json='{"instrument_id":3,"period_policy":"old-policy"}' where run_id=3;
update ref.instrument set instrument_type='etf' where instrument_id=4;''')
        rows=json.loads(self.sql(render_queue_sql(as_of_date=date(2026,9,11))))
        self.assertEqual({r['primary_symbol']:r['state'] for r in rows},{'ARM':'fresh','AAPL':'retry_wait','NVDA':'due'})
        self.sql("update ops.pipeline_run set started_at=now()-interval '25 hours' where run_id=2; update ops.pipeline_run set ended_at=now()-interval '8 days' where run_id=1;")
        self.assertTrue(all(r['state']=='due' for r in json.loads(self.sql(render_queue_sql(as_of_date=date(2026,9,11))))))

    def test_reporting_rotation_same_day_skip_and_budget_reservation(self):
        self.sql("insert into research.equity_research_artifact values(1,'2026-09-11','full_equity_research','codex_oauth'),(2,'2026-09-10','full_equity_research','codex_oauth'),(3,'2026-09-09','full_equity_research','codex_oauth');")
        query=render_equity_research_symbol_lookup_sql(as_of_date=date(2026,9,11))
        self.assertEqual(json.loads(self.sql(query)),['CONTROL','NVDA','AAPL'])
        self.sql('''update ops.pipeline_run set pipeline_name='equity_research_reporting',config_json='{"provider":"codex_oauth","as_of_date":"2026-09-11","symbols":["ONE","TWO","THREE","FOUR"]}' where run_id=1;''')
        self.assertEqual(json.loads(self.sql(query)),['CONTROL'])
        self.sql('''update ops.pipeline_run set config_json=jsonb_set(config_json,'{symbols}','["1","2","3","4","5"]') where run_id=1;''')
        self.assertEqual(json.loads(self.sql(query)),[])
        explicit=render_equity_research_symbol_lookup_sql(as_of_date=date(2026,9,11),symbols=('ARM','AAPL','NVDA'),limit=1)
        self.assertEqual(json.loads(self.sql(explicit)),['AAPL'])


if __name__=='__main__': unittest.main()
