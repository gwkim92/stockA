"""Execute the production health CTE at fixed clocks in a disposable database."""
import json
import unittest
from tests import test_financial_period_integrity_postgres as fixture
from stockanalysis.frontend.live_adapter import render_frontend_data_health_state_sql


class PipelineSchedulePostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.FinancialPeriodPostgresTests.setUpClass.__func__(cls)

    @classmethod
    def sql(cls, sql):
        return fixture.FinancialPeriodPostgresTests.sql.__func__(cls, sql)

    def setUp(self):
        self.sql('''drop schema if exists ops,performance cascade;
create schema ops; create schema performance;
create table performance.thesis_outcome(outcome_id bigint);
create table ops.pipeline_run(run_id bigint,status text,pipeline_name text,
started_at timestamptz,ended_at timestamptz,config_json jsonb default '{}');''')

    def run_record(self, run_id=1, status='succeeded', started='2026-09-11 16:55-04', ended='2026-09-11 16:56-04', market=False, mode='microdata', region='US'):
        pipeline = 'tossinvest_market_data_sync' if market else 'tossinvest_readonly_sync'
        self.sql(f"insert into ops.pipeline_run values ({run_id},'{status}','{pipeline}','{started}',"
                 + (f"'{ended}'" if ended else 'null')
                 + f",'{{\"sync_mode\":\"{mode}\",\"market_code\":\"{region}\"}}');")

    def health(self, clock='2026-09-13 04:00-04', market=False):
        query = render_frontend_data_health_state_sql().split(',\nselected_tossinvest_readonly_sync as (',1)[0]
        query = query.replace('now()', f"timestamptz '{clock}'")
        query += " select json_agg(t) from latest_runs t;"
        rows = json.loads(self.sql(query))
        job = 'toss-priority-microdata-intraday' if market else 'toss-live-account-readonly'
        return next(row for row in rows if row['job_id']==job)

    def test_weekend_wait_and_monday_due_boundary(self):
        self.run_record()
        for clock in ('2026-09-12 10:00-04','2026-09-13 20:00-04','2026-09-14 08:54-04'):
            self.assertEqual(self.health(clock)['health_status'], 'scheduled_wait')
        self.assertEqual(self.health('2026-09-14 08:55-04')['health_status'], 'stale')
        self.assertEqual(self.health('2026-09-11 17:00-04')['health_status'], 'ok')

    def test_missed_last_friday_slot_is_not_weekend_wait(self):
        self.run_record(started='2026-09-11 12:55-04',ended='2026-09-11 12:56-04')
        self.assertEqual(self.health()['health_status'], 'stale')

    def test_failure_running_missing_fallback_are_never_hidden(self):
        self.assertEqual(self.health()['health_status'], 'missing')
        for status, expected in [('failed','failed'),('started','stale_running'),('succeeded_with_fallback','degraded')]:
            self.sql('truncate ops.pipeline_run;')
            self.run_record(status=status)
            self.assertEqual(self.health()['health_status'], expected)
        self.sql('truncate ops.pipeline_run;')
        self.run_record(ended=None)
        self.assertEqual(self.health()['health_status'], 'missing')

    def test_daily_candles_and_other_market_cannot_cover_missing_microdata(self):
        self.run_record(market=True,mode='daily_candles')
        self.run_record(run_id=2,market=True,region='KR')
        self.assertEqual(self.health(market=True)['health_status'], 'missing')
        self.run_record(run_id=3,market=True,started='2026-09-11 15:40-04',ended='2026-09-11 15:41-04')
        row=self.health(market=True)
        self.assertEqual(row['run_id'],3)
        self.assertEqual(row['health_status'],'scheduled_wait')
        self.run_record(run_id=4,market=True,status='failed',started='2026-09-11 16:00-04',ended='2026-09-11 16:01-04')
        self.assertEqual(self.health(market=True)['health_status'],'failed')

    def test_dst_weekends_use_new_york_calendar(self):
        for friday, sunday, monday_due in [
            ('2026-03-06 16:56-05','2026-03-08 16:00-04','2026-03-09 08:55-04'),
            ('2026-10-30 16:56-04','2026-11-01 16:00-05','2026-11-02 08:55-05')]:
            self.sql('truncate ops.pipeline_run;')
            self.run_record(started=friday,ended=friday)
            self.assertEqual(self.health(sunday)['health_status'],'scheduled_wait')
            self.assertEqual(self.health(monday_due)['health_status'],'stale')

    def test_long_previous_slot_does_not_substitute_for_last_scheduled_run(self):
        self.run_record(started='2026-09-11 12:55-04',ended='2026-09-11 17:01-04')
        self.assertEqual(self.health()['health_status'], 'stale')
