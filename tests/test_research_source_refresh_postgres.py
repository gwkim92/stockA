"""Actual reservation races, receipt reconciliation and provenance SQL in disposable PG."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import json
import unittest
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

from stockanalysis.ai.research_source_version import latest_source_sql, freshness_sql, public_freshness
from stockanalysis.ai import equity_research_reporting as equity
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.ingest.sec.financial_periods import PERIOD_POLICY
from stockanalysis.operations import research_report_refresh as refresh
from tests.test_equity_atomic_postgres import original_table
from tests import test_financial_period_integrity_postgres as pg_fixture
from tests.test_equity_batch_isolation import context
from tests.test_equity_research_contract_v3 import response


class SourceRefreshPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pg_fixture.FinancialPeriodPostgresTests.setUpClass.__func__(cls)
        cls.db = PsqlCommandExecutor(cls.command)
        cls.day = date.fromisoformat(cls.db.execute_scalar("select (now() at time zone 'UTC')::date;"))

    @classmethod
    def sql(cls, sql):
        return pg_fixture.FinancialPeriodPostgresTests.sql.__func__(cls, sql)

    def setUp(self):
        self.db.execute_non_query('''drop schema if exists ops,ref,ai,research,market,ingest,signal,portfolio cascade;
create schema ops; create schema ref; create schema ai; create schema research; create schema signal; create schema portfolio;
create table ref.instrument(instrument_id bigint primary key,primary_symbol text,name text default 'Company',
    market_code text default 'US',instrument_type text default 'common_stock',is_active boolean default true);
create table signal.recommendation_batch(batch_id bigint,as_of_date date);
create table signal.recommendation(instrument_id bigint,batch_id bigint,status text);
create table portfolio.position_snapshot(instrument_id bigint,snapshot_date date);
''' + '\n'.join(original_table(f, t) for f, t in (
    ('0002_priority_1_tables.sql', 'ops.pipeline_run'), ('0005_ai_intelligence.sql', 'ai.prompt_template'),
    ('0005_ai_intelligence.sql', 'ai.model_invocation'), ('0021_professional_equity_analysis.sql', 'research.equity_research_artifact')))
        + "insert into ref.instrument(instrument_id,primary_symbol) select n,'TEST'||n from generate_series(1,6) n;"
        + f"insert into signal.recommendation_batch values(1,'{self.day}');"
        + "insert into signal.recommendation select n,1,'active' from generate_series(1,6) n;")
        self.policy = refresh.generation_policy('test-model')

    def source(self, iid=1, sha='a', status='succeeded'):
        cfg = json.dumps({'instrument_id': iid, 'source_sha256': sha*64, 'period_policy': PERIOD_POLICY})
        return int(self.db.execute_scalar(f"insert into ops.pipeline_run(run_kind,pipeline_name,status,config_json,ended_at) values('test','research_statement_refresh','{status}','{cfg}',now()) returning run_id;"))

    def reserve(self):
        return json.loads(self.db.execute_scalar(refresh.render_reservation_sql(as_of_date=self.day, policy=self.policy, model='test-model')))

    def queue(self):
        return json.loads(self.db.execute_scalar(refresh.render_queue_sql(as_of_date=self.day, policy=self.policy)))

    def real_runner(self, calls, *, change_source=False, lose_ack=False):
        owner = self
        class ContextDB:
            def execute_scalar(self, sql):
                if sql.startswith('-- equity research context lookup'):
                    data = context('AAPL')
                    data['instrument'].update(instrument_id=1, primary_symbol='TEST1')
                    data['query'].update(symbol='TEST1', as_of_date=str(owner.day))
                    data['financial_source_version'] = json.loads(owner.db.execute_scalar(
                        f'select to_jsonb(s) from ({latest_source_sql("1")}) s;'))
                    return json.dumps(data)
                return owner.db.execute_scalar(sql)
            def execute_non_query(self, sql): return owner.db.execute_non_query(sql)
        def provider(*_):
            calls.append('TEST1')
            if change_source: owner.source(sha='b')
            return replace(response(), model_name='test-model')
        def runner(**kwargs):
            kwargs['executor'] = ContextDB()
            result = equity.run_equity_research_reporting(**kwargs, provider_runner=provider)
            if lose_ack: raise RuntimeError('simulated lost coordinator response after real COMMIT')
            return result
        return runner

    def worker(self, runner):
        return refresh.run_research_report_refresh(config=SimpleNamespace(), as_of_date=self.day,
            execute=True, executor=self.db, report_runner=runner, model_name='test-model')

    def test_real_result_receipt_suppresses_second_model_call(self):
        self.source(); calls=[]; runner=self.real_runner(calls)
        result=self.worker(runner)
        self.assertEqual(result['status'], 'succeeded', result)
        self.assertEqual(self.worker(runner)['status'], 'no_op')
        self.assertEqual(calls, ['TEST1'])
        self.source()  # Same content, new collection run: still no call.
        self.assertEqual(self.worker(runner)['status'], 'no_op')
        self.assertEqual(next(r for r in self.queue()['queue'] if r['instrument_id']==1)['state'], 'current')
        # A later mutation invalidates the receipt; no optimistic current state.
        self.db.execute_non_query("update research.equity_research_artifact set title='changed after receipt';")
        self.assertEqual(next(r for r in self.queue()['queue'] if r['instrument_id']==1)['state'], 'result_changed')

    def test_lost_ack_is_closed_from_real_receipt_without_replay(self):
        self.source(); calls=[]
        self.assertEqual(self.worker(self.real_runner(calls,lose_ack=True))['status'], 'reconcile')
        recovered=self.worker(self.real_runner(calls))
        self.assertEqual(recovered['status'], 'no_op')
        self.assertEqual(recovered['reconciliation'][0]['status'], 'succeeded')
        self.assertEqual(calls, ['TEST1'])

    def test_existing_manual_result_with_same_version_also_suppresses_auto_call(self):
        self.source(); calls=[]
        self.real_runner(calls)(config=SimpleNamespace(), as_of_date=self.day, symbols=('TEST1',), limit=1,
            provider='codex_oauth', model_name='test-model', reasoning_effort='low', execute=True)
        self.assertEqual(self.worker(self.real_runner(calls))['status'], 'no_op')
        self.assertEqual(calls, ['TEST1'])
        self.assertEqual(self.queue()['daily_used'], 1)

    def test_symbol_filter_cannot_bypass_shared_daily_budget(self):
        for iid in range(1,7): self.source(iid)
        result=json.loads(self.db.execute_scalar(refresh.render_reservation_sql(as_of_date=self.day,
            policy=self.policy, model='test-model', symbol='TEST6')))
        self.assertEqual(result['claim']['request']['symbol'], 'TEST6')
        for _ in range(4): self.reserve()
        result=json.loads(self.db.execute_scalar(refresh.render_reservation_sql(as_of_date=self.day,
            policy=self.policy, model='test-model', symbol='TEST5')))
        self.assertIsNone(result['claim'])

    def test_source_changed_during_real_generation_is_not_current(self):
        self.source(); calls=[]
        result=self.worker(self.real_runner(calls,change_source=True))
        self.assertEqual(result['status'], 'succeeded', result)
        row=next(r for r in self.queue()['queue'] if r['instrument_id']==1)
        self.assertEqual(row['state'], 'due')
        raw=json.loads(self.db.execute_scalar(f'select {freshness_sql()} from research.equity_research_artifact artifact;'))
        self.assertEqual(public_freshness(raw)['status'], 'source_changed')

    def test_failed_collection_does_not_advance_version(self):
        first = self.source(); self.source(sha='b', status='failed')
        row = json.loads(self.db.execute_scalar(f'select to_jsonb(s) from ({latest_source_sql("1")}) s;'))
        self.assertEqual(row['source_run_id'], first)
        self.assertEqual(row['source_sha256'], 'a'*64)

    def test_identical_recollection_is_not_another_generation(self):
        self.source(); first = self.reserve()['claim']; self.source()
        self.db.execute_non_query(f"update ops.pipeline_run set status='succeeded',ended_at=now() where run_id={first['run_id']};")
        self.assertIsNone(self.reserve()['claim'])
        # A coordinator status alone is not proof that a report exists.
        self.assertEqual(next(r for r in self.queue()['queue'] if r['instrument_id']==1)['state'], 'result_changed')

    def test_new_source_is_due_but_unknown_previous_result_blocks_it(self):
        self.source(); claim = self.reserve()['claim']; self.source(sha='b')
        self.assertIsNone(self.reserve()['claim'])
        self.db.execute_non_query(f"update ops.pipeline_run set status='failed',ended_at=now() where run_id={claim['run_id']};")
        second = self.reserve()['claim']
        self.assertEqual(second['request']['source_version']['source_sha256'], 'b'*64)

    def test_concurrent_claims_respect_daily_limit_and_deduplicate(self):
        for iid in range(1,7): self.source(iid)
        with ThreadPoolExecutor(max_workers=8) as pool:
            rows = list(pool.map(lambda _: self.reserve(), range(8)))
        claims = [r['claim'] for r in rows if r['claim']]
        self.assertEqual(len(claims), 5)
        self.assertEqual(len({r['request']['generation_key'] for r in claims}), 5)
        self.assertEqual(self.queue()['daily_used'], 5)

    def test_legacy_budget_is_shared_and_child_is_not_counted_twice(self):
        for iid in range(1,4): self.source(iid)
        cfg = json.dumps({'as_of_date': str(self.day), 'provider':'codex_oauth','symbols':['A','B','C','D']})
        self.db.execute_non_query(f"insert into ops.pipeline_run(run_kind,pipeline_name,status,config_json) values('ai','equity_research_reporting','running','{cfg}');")
        claim = self.reserve()['claim']
        cfg = json.dumps({'as_of_date': str(self.day), 'provider':'codex_oauth','symbols':['TEST1'],'source_refresh_claim_id':claim['run_id']})
        self.db.execute_non_query(f"insert into ops.pipeline_run(run_kind,pipeline_name,status,config_json) values('ai','equity_research_reporting','running','{cfg}');")
        self.assertEqual(self.queue()['daily_used'], 5)
        self.assertIsNone(self.reserve()['claim'])

    def test_malformed_legacy_budget_fails_closed(self):
        self.source()
        cfg = json.dumps({'as_of_date':str(self.day),'provider':'codex_oauth','symbols':{'bad':True}})
        self.db.execute_non_query(f"insert into ops.pipeline_run(run_kind,pipeline_name,status,config_json) values('ai','equity_research_reporting','running','{cfg}');")
        self.assertIsNone(self.reserve()['claim'])

    def test_confirmed_fallback_waits_24_hours_but_unknown_result_never_replays(self):
        self.source(); claim=self.reserve()['claim']; cid=claim['run_id']
        self.db.execute_non_query(f"update ops.pipeline_run set status='failed',ended_at=now(), config_json=config_json || '{{\"result_receipt\":{{\"outcome\":\"fallback\"}}}}'::jsonb where run_id={cid};")
        self.assertEqual(next(r for r in self.queue()['queue'] if r['instrument_id']==1)['state'],'retry_wait')
        self.assertIsNone(self.reserve()['claim'])
        self.db.execute_non_query(f"update ops.pipeline_run set started_at=now()-interval '26 hours',ended_at=now()-interval '25 hours' where run_id={cid};")
        retried=self.reserve()['claim']; self.assertIsNotNone(retried)
        self.source(sha='b')
        self.assertIsNone(self.reserve()['claim'])  # Still-running new attempt blocks newer sources, too.

    def test_historical_execute_cannot_reserve(self):
        self.source()
        result=json.loads(self.db.execute_scalar(refresh.render_reservation_sql(as_of_date=date(2000,1,1),policy=self.policy,model='test')))
        self.assertIsNone(result['claim'])

    def test_current_source_changes_during_generation_remain_visible(self):
        sid = self.source()
        version={'source_run_id':sid,'source_sha256':'a'*64,'period_policy':PERIOD_POLICY}
        cfg=json.dumps({'financial_source_versions':{'TEST1':version}})
        gid=int(self.db.execute_scalar(f"insert into ops.pipeline_run(run_kind,pipeline_name,status,config_json) values('ai','equity_research_reporting','succeeded','{cfg}') returning run_id;"))
        self.db.execute_non_query(f"insert into research.equity_research_artifact(instrument_id,as_of_date,artifact_type,provider,model_name,title,korean_summary,source_run_id) values(1,'{self.day}','full_equity_research','codex_oauth','test','title','summary',{gid});")
        def state():
            return public_freshness(json.loads(self.db.execute_scalar(f'select {freshness_sql()} from research.equity_research_artifact artifact;')))['status']
        self.assertEqual(state(), 'current')
        self.source(sha='b'); self.assertEqual(state(), 'source_changed')
        self.source(sha='c',status='failed'); self.assertEqual(state(), 'source_changed')


if __name__ == '__main__': unittest.main()
