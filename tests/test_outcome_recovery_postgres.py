"""Real SQL regression on the explicitly enabled disposable local test DB."""
import json
import os
from datetime import date
from pathlib import Path
import unittest

from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.performance import outcome


@unittest.skipUnless(os.getenv('STOCKA_OUTCOME_TEST_ENABLED') == '1', 'Disposable local PostgreSQL required')
class OutcomeRecoveryPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        binary = os.getenv('STOCKA_OUTCOME_TEST_PSQL', '/opt/homebrew/opt/postgresql@17/bin/psql')
        cls.command = [binary, '-h', '/private/tmp', '-p', '55487', '-U', 'postgres', '-d', 'stocka_outcome_recovery_test']
        cls.executor = PsqlCommandExecutor(cls.command)
        identity = cls.executor.execute_scalar('select current_database();')
        if identity != 'stocka_outcome_recovery_test':
            raise RuntimeError('Refusing a non-test database')

    def setUp(self):
        self.executor.execute_non_query('''
drop schema if exists performance, signal, market, ref, ops cascade;
create schema performance; create schema signal; create schema market; create schema ref; create schema ops;
create table ops.pipeline_run(run_id bigint primary key);
insert into ops.pipeline_run values(1),(2);
create table ref.instrument(instrument_id bigint primary key, primary_symbol text, is_active boolean);
insert into ref.instrument values(1,'AAA',true),(2,'BBB',true),(3,'SPY',true);
create table signal.recommendation_batch(batch_id bigint primary key, as_of_date date, market_code text, strategy_name text, horizon_type text, universe_version text);
insert into signal.recommendation_batch values(10,'2026-06-05','US','long_term_core','long_term','old-universe'),(20,'2026-09-10','US','long_term_core','long_term','today-universe');
create table signal.investment_thesis(thesis_id bigint primary key, title text, status text, benchmark_code text);
insert into signal.investment_thesis values(1,'AAA business case','active','SPY'),(2,'BBB business case','active','SPY');
create table signal.recommendation(recommendation_id bigint primary key, batch_id bigint, thesis_id bigint, instrument_id bigint, total_score numeric, bucket text, action text, status text);
insert into signal.recommendation values(101,10,1,1,.7,'cycle','watch','active'),(102,10,2,2,.6,'cycle','watch','active'),(201,20,1,1,.7,'cycle','watch','active');
create table market.daily_price_bar(instrument_id bigint, trade_date date, adjusted_close numeric);
insert into market.daily_price_bar values(1,'2026-06-05',100),(1,'2026-07-02',110),(2,'2026-06-05',200),(2,'2026-07-02',240),(3,'2026-06-05',100),(3,'2026-07-02',105);
''')
        self.executor.execute_non_query((Path(__file__).parents[1]/'db/migrations/0010_performance_outcome.sql').read_text())
        self.executor.execute_non_query('''insert into performance.recommendation_outcome
(recommendation_id,measurement_start_date,measurement_end_date,horizon_days,entry_price,exit_price,absolute_return_pct,benchmark_code,benchmark_return_pct,alpha_pct,max_drawdown_pct,outcome_label,source_run_id)
values(101,'2026-06-05','2026-07-02',27,100,110,.1,'SPY',.05,.05,0,'outperform',1);''')

    def schedule(self):
        sql = outcome.render_performance_outcome_schedule_candidate_lookup_sql(due_on_date=date(2026,7,5),horizon_days=(30,),strategy_name='long_term_core')
        return json.loads(self.executor.execute_scalar(sql))

    def candidates(self):
        return outcome.load_performance_outcome_candidates(config=None,as_of_date=date(2026,6,5),measurement_end_date=date(2026,7,5),strategy_name='long_term_core',horizon_type='long_term',universe_version='old-universe',executor=self.executor,preserve_existing=True)

    def test_old_universe_and_holiday_outcome_are_counted_once(self):
        rows = self.schedule()
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['batch_id'],10)
        self.assertEqual(rows[0]['existing_outcome_count'],1)
        self.assertEqual([r.recommendation_id for r in self.candidates()],[102])

    def test_backfill_preserves_recorded_values_and_rerun_has_no_candidates(self):
        before = self.executor.execute_scalar('select row_to_json(r)::text from performance.recommendation_outcome r where recommendation_id=101;')
        recommendations, theses = outcome.build_performance_outcome_rows(self.candidates())
        result = json.loads(self.executor.execute_scalar(outcome.render_performance_outcome_upsert_sql(recommendations,theses,source_run_id=2,preserve_existing=True)))
        self.assertEqual(result['recommendation_outcome_count'],1)
        self.assertEqual(self.schedule(),[])
        after = self.executor.execute_scalar('select row_to_json(r)::text from performance.recommendation_outcome r where recommendation_id=101;')
        self.assertEqual(before,after)
        again = json.loads(self.executor.execute_scalar(outcome.render_performance_outcome_upsert_sql(recommendations,theses,source_run_id=1,preserve_existing=True)))
        self.assertEqual(again['recommendation_outcome_count'],0)
        self.assertEqual(again['thesis_outcome_count'],0)
        self.assertEqual(self.candidates(),())

    def test_short_observation_does_not_satisfy_thirty_day_horizon(self):
        self.executor.execute_non_query("update performance.recommendation_outcome set measurement_end_date='2026-06-10',horizon_days=5;")
        self.assertEqual(self.schedule()[0]['existing_outcome_count'],0)


if __name__ == '__main__': unittest.main()
