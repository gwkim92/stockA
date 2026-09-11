import json
import os
from pathlib import Path
import unittest
from urllib.parse import urlencode
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.frontend.recommendation_outcomes import API_PATH, resolve_recommendation_outcomes


@unittest.skipUnless(os.getenv('STOCKA_EXPLORER_TEST_ENABLED')=='1','Dedicated disposable PostgreSQL required')
class OutcomeExplorerPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cmd=['/opt/homebrew/opt/postgresql@17/bin/psql','-h','/private/tmp','-p','55489','-U','postgres','-d','stocka_outcome_explorer_test']
        cls.admin=PsqlCommandExecutor(cmd)
        if cls.admin.execute_scalar('select current_database();')!='stocka_outcome_explorer_test':raise RuntimeError('Wrong test database')
        if cls.admin.execute_scalar("select to_regnamespace('performance') is null;")!='t':raise RuntimeError('Refusing existing schema')
        for name in ['0001_bootstrap.sql','0002_priority_1_tables.sql','0003_priority_1_indexes.sql','0005_ai_intelligence.sql','0010_performance_outcome.sql','0035_recommendation_eval_persistence.sql']:
            cls.admin.execute_non_query((Path(__file__).parents[1]/'db/migrations'/name).read_text())
        cls.admin.execute_non_query("""
create role outcome_explorer_reader nologin nosuperuser;
grant usage on schema performance,signal,ref,ai to outcome_explorer_reader;
grant select on all tables in schema performance,signal,ref,ai to outcome_explorer_reader;
insert into ref.market values('US','US','US','USD','UTC',true);
insert into ref.exchange(market_code,mic_code,name,timezone) values('US','TEST','Test','UTC');
insert into ref.issuer(legal_name,display_name,country_code,issuer_type) values('Test','Test','US','company');
insert into ref.instrument(issuer_id,exchange_id,market_code,primary_symbol,instrument_type,currency_code,name) values(1,1,'US','AAA','equity','USD','AAA'),(1,1,'US','BBB','equity','USD','BBB');
insert into signal.recommendation_batch(as_of_date,market_code,strategy_name,horizon_type) values('2026-06-01','US','long_term_core','long_term'),('2026-06-02','US','long_term_core','long_term');
insert into signal.recommendation(batch_id,instrument_id,bucket,action,rank_position,total_score) values(1,1,'test','watch',1,.5),(2,2,'test','watch',2,0);
insert into ai.eval_run(eval_name,dataset_version,provider,model_name,as_of_date,score_json) values('recommendation_quality_calibration','test','fixture','fixture','2026-09-10','{}');
""")
        cls.reader=PsqlCommandExecutor(['env','PGOPTIONS=-c default_transaction_read_only=on -c role=outcome_explorer_reader',*cmd])

    def setUp(self):
        self.admin.execute_non_query('truncate performance.recommendation_outcome restart identity cascade; truncate ai.recommendation_eval_snapshot restart identity;')
        self.admin.execute_non_query("""
insert into performance.recommendation_outcome(recommendation_id,measurement_start_date,measurement_end_date,horizon_days,entry_price,exit_price,absolute_return_pct,benchmark_code,benchmark_return_pct,alpha_pct,outcome_label)
values (1,'2026-06-01','2026-06-29',28,100,110,.1,'SPY',.05,.05,'outperform'),
(2,'2026-06-02','2026-06-29',27,100,100,0,'SPY',0,0,'flat'),
(1,'2026-06-01','2026-08-30',90,100,90,-.1,null,null,null,'unavailable');
insert into ai.recommendation_eval_snapshot(eval_run_id,snapshot_schema_version,source_recommendation_id,source_batch_id,source_outcome_id,primary_symbol,recommendation_action,recommendation_total_score,snapshot_json,snapshot_sha256)
values(1,'test',1,1,1,'AAA','watch',.5,'{}',repeat('a',64));
""")

    def read(self,**query):return resolve_recommendation_outcomes(API_PATH+('?' + urlencode(query) if query else ''),source='live',executor=self.reader)

    def fingerprint(self):return self.admin.execute_scalar("select md5(string_agg(to_jsonb(r)::text,'|' order by outcome_id)) from performance.recommendation_outcome r;")

    def test_all_measurements_without_any_portfolio_or_attribution_and_readonly_preservation(self):
        before=self.fingerprint();report=self.read()
        self.assertEqual(report['summary']['measurement_count'],3);self.assertEqual(report['summary']['recommendation_count'],2)
        self.assertEqual(report['summary']['symbol_count'],2);self.assertEqual(report['summary']['missing_alpha_count'],1)
        self.assertEqual([r['outcome_id'] for r in report['rows']],['3','2','1'])
        self.assertEqual(self.admin.execute_scalar('select count(*) from portfolio.position_snapshot;'),'0')
        self.assertEqual(before,self.fingerprint())
        self.assertEqual(report['rows'][1]['absolute_return_pct'],0);self.assertIsNone(report['rows'][0]['alpha_pct'])
        self.assertIsNone(report['rows'][1]['evaluation_snapshot'])
        self.assertEqual(report['rows'][2]['evaluation_snapshot']['snapshot_id'],'1')

    def test_filters_and_summary_cover_all_matches_not_just_page(self):
        report=self.read(horizon='30',benchmark='SPY',limit=1)
        self.assertEqual(report['summary']['measurement_count'],2);self.assertEqual(len(report['rows']),1)
        self.assertEqual(self.read(symbol='aaa')['summary']['measurement_count'],2)
        self.assertEqual(self.read(from_date='2026-06-02',to_date='2026-06-02')['rows'][0]['symbol'],'BBB')
        self.assertEqual(self.read(alpha='zero')['rows'][0]['alpha_pct'],0)
        self.assertEqual(self.read(benchmark='_missing')['rows'][0]['outcome_id'],'3')
        self.assertEqual(self.read(symbol='NONE')['summary']['measurement_count'],0)
        self.assertEqual(self.read(horizon='180')['rows'],[])

    def test_page_keyset_ties_and_watermark_exclude_new_backfills(self):
        first=self.read(limit=1);self.assertEqual(first['rows'][0]['outcome_id'],'3')
        self.admin.execute_non_query("""insert into performance.recommendation_outcome(recommendation_id,measurement_start_date,measurement_end_date,horizon_days,entry_price,exit_price,absolute_return_pct,benchmark_code,benchmark_return_pct,alpha_pct,outcome_label) values(2,'2026-06-02','2026-07-01',29,100,110,.1,'SPY',.05,.05,'outperform');""")
        second=self.read(limit=1,before=first['pagination']['next_cursor'],through=first['pagination']['through'])
        self.assertEqual(second['rows'][0]['outcome_id'],'2');self.assertEqual(second['summary']['measurement_count'],3)
        third=self.read(limit=1,before=second['pagination']['next_cursor'],through=first['pagination']['through'])
        self.assertEqual(third['rows'][0]['outcome_id'],'1');self.assertFalse(third['pagination']['has_more'])
        self.assertEqual(self.read()['summary']['measurement_count'],4)

    def test_existing_horizon_boundary_and_short_or_same_day_measurements(self):
        self.admin.execute_non_query("""delete from performance.recommendation_outcome; insert into performance.recommendation_outcome(recommendation_id,measurement_start_date,measurement_end_date,horizon_days,entry_price,exit_price,absolute_return_pct,outcome_label)
select 1,'2026-06-01'::date,'2026-06-01'::date+h,h,100,100,0,'flat' from unnest(array[0,1,22,23,37,38,83,97,98]) h;""")
        self.assertEqual(sorted(r['horizon_days'] for r in self.read(horizon='30')['rows']),[23,37])
        self.assertEqual(sorted(r['horizon_days'] for r in self.read(horizon='90')['rows']),[83,97])
        self.assertEqual(sorted(r['horizon_days'] for r in self.read(horizon='other')['rows']),[0,1,22,38,98])


if __name__=='__main__':unittest.main()
