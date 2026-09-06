"""Committed-write/fault tests on one explicitly isolated CI PostgreSQL service.

Unlike the cutoff suite these tests observe COMMIT and rollback across separate
connections. Tables are recreated per case, only in stocka_atomic_test.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
from datetime import date
import json
import os
from pathlib import Path
import re
from threading import Barrier
from types import SimpleNamespace
import unittest

from stockanalysis.ai import equity_research_reporting as equity
from stockanalysis.ai.equity_research_batch import EquityResearchBatchError
from stockanalysis.ai.equity_research_persistence import (
    render_atomic_result_sql, parse_acknowledgement, reconcile_result, RECEIPTS_KEY,
)
from stockanalysis.ai_agents.prompt_contract import PromptContractError
from stockanalysis.ingest.psql import PsqlCommandExecutor, PsqlExecutionError
from tests.test_equity_atomic_persistence import arguments, HASH, DAY
from tests.test_equity_batch_isolation import context
from tests.test_equity_research_contract_v3 import response

ROOT = Path(__file__).resolve().parents[1]
SQL_EXECUTIONS = 0
POSTGRES_VERSION = None


def original_table(filename, table):
    text = (ROOT / 'db/migrations' / filename).read_text()
    pattern = rf'create table if not exists {re.escape(table)} \(.*?^\);'
    result = re.search(pattern, text, re.S | re.M)
    if result is None: raise AssertionError(f'Original table missing: {table}')
    return result.group()


def schema():
    return '\n'.join([
        'create schema ops; create schema ref; create schema ai; create schema research;',
        'create table ref.instrument (instrument_id bigint primary key);',
        original_table('0002_priority_1_tables.sql', 'ops.pipeline_run'),
        original_table('0005_ai_intelligence.sql', 'ai.prompt_template'),
        original_table('0005_ai_intelligence.sql', 'ai.model_invocation'),
        original_table('0021_professional_equity_analysis.sql', 'research.equity_research_artifact'),
        "insert into ref.instrument values (101), (102), (103);",
        """insert into ops.pipeline_run(run_id,run_kind,pipeline_name,status,config_json)
            overriding system value values
            (901,'test','equity_research_reporting','running','{"keep":"unchanged"}'),
            (902,'test','equity_research_reporting','running','{}');""",
        """insert into ai.prompt_template(template_id,template_name,template_version,system_purpose,template_text)
            overriding system value values (44,'test','test','test','test');""",
    ])


class TestExecutor(PsqlCommandExecutor):
    def _run(self, sql):
        global SQL_EXECUTIONS
        SQL_EXECUTIONS += 1
        return super()._run(sql)


class EquityAtomicPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        service = os.getenv('STOCKA_ATOMIC_TEST_CONTAINER','')
        if not service: raise unittest.SkipTest('Dedicated atomic PostgreSQL service required')
        if os.getenv('GITHUB_ACTIONS') != 'true' or not re.fullmatch('[a-f0-9]{12,64}', service):
            raise RuntimeError('Only the explicit CI service is supported; no runtime DB URL or host accepted')
        # Actual production psql executor, with an outer process deadline and
        # test-only server timeouts. No host-exposed database port is used.
        cls.db = TestExecutor(['timeout','25s','docker','exec','-i',
            '-e','PGOPTIONS=-c statement_timeout=10000 -c lock_timeout=5000', service,
            'psql','-h','/var/run/postgresql','-U','postgres','-d','stocka_atomic_test'])
        dbname, version = cls.db.execute_scalar("select current_database() || '|' || current_setting('server_version');").split('|',1)
        if dbname != 'stocka_atomic_test': raise RuntimeError('Wrong database for destructive test setup')
        global POSTGRES_VERSION
        POSTGRES_VERSION = version
        cls.assert_clean()

    @classmethod
    def assert_clean(cls):
        count = cls.db.execute_scalar("select count(*) from pg_namespace where nspname in ('ops','ref','ai','research');")
        if count != '0': raise AssertionError('Test schemas were not cleaned or pre-existed; refusing setup')

    def setUp(self):
        self.assert_clean()
        self.addCleanup(self.cleanup_tables)
        self.db.execute_non_query(schema())

    def cleanup_tables(self):
        self.db.execute_non_query('drop schema if exists research,ai,ref,ops cascade;')
        self.assert_clean()

    def persist(self, **changes):
        args = arguments(); args.update(changes)
        raw = self.db.execute_scalar(render_atomic_result_sql(**args))
        return parse_acknowledgement(raw, run_id=args['run_id'], request_hash=args['request_hash'])

    def counts(self):
        return json.loads(self.db.execute_scalar(f"""select jsonb_build_object(
          'invocations',(select count(*) from ai.model_invocation),
          'artifacts',(select count(*) from research.equity_research_artifact),
          'receipts',(select count(*) from ops.pipeline_run p cross join lateral
              jsonb_object_keys(coalesce(p.config_json->'{RECEIPTS_KEY}','{{}}'::jsonb)) keys)
        )::text;"""))

    def failure_invocation(self, *, run_id=901, request_hash=HASH):
        return int(self.db.execute_scalar(equity.render_equity_research_model_invocation_insert_sql(
            run_id=run_id, provider='codex_oauth', model_name='failed-fixture', reasoning_effort=None,
            prompt_template_id=44, input_token_count=None, output_token_count=None,
            cached_input_token_count=None, estimated_cost_usd=None, latency_ms=None,
            status='failed', error_summary='provider_failed', request_hash=request_hash,
        )))

    def test_old_separate_writes_leave_a_successful_invocation_without_report(self):
        self.db.execute_non_query("alter table research.equity_research_artifact add constraint reject_report check (false);")
        args=arguments(); r=args['response']
        self.db.execute_scalar(equity.render_equity_research_model_invocation_insert_sql(
            run_id=901,provider=r.provider,model_name=r.model_name,reasoning_effort=r.reasoning_effort,
            prompt_template_id=44,input_token_count=None,output_token_count=None,cached_input_token_count=None,
            estimated_cost_usd=None,latency_ms=None,status='succeeded',error_summary=None,request_hash=HASH))
        with self.assertRaises(PsqlExecutionError):
            self.db.execute_scalar(equity.render_equity_research_artifact_upsert_sql(
                context=args['context'],response=r,as_of_date=DAY,source_run_id=901))
        self.assertEqual(self.counts(),{'invocations':1,'artifacts':0,'receipts':0})

    def test_primary_commits_all_three_and_read_only_reconciliation_matches(self):
        receipt=self.persist()
        self.assertEqual(self.counts(),{'invocations':1,'artifacts':1,'receipts':1})
        result=reconcile_result(self.db,run_id=901,request_hash=HASH)
        self.assertEqual(result['status'],'matching');self.assertEqual(result['receipt'],receipt)
        self.assertFalse(result['automatic_retry_allowed'])
        self.assertEqual(self.db.execute_scalar("select config_json->>'keep' from ops.pipeline_run where run_id=901;"),'unchanged')
        self.assertEqual(self.db.execute_scalar("select valuation_sensitivity_json->>'confidence' from research.equity_research_artifact;"),'0.0')

    def test_artifact_constraint_failure_rolls_back_log_and_receipt(self):
        self.db.execute_non_query("alter table research.equity_research_artifact add constraint reject_report check (false);")
        with self.assertRaises(PsqlExecutionError):self.persist()
        self.assertEqual(self.counts(),{'invocations':0,'artifacts':0,'receipts':0})

    def test_invocation_constraint_failure_rolls_back_artifact_and_receipt(self):
        with self.assertRaises(PsqlExecutionError):self.persist(response=replace(response(),input_token_count=-1))
        self.assertEqual(self.counts(),{'invocations':0,'artifacts':0,'receipts':0})

    def test_receipt_write_error_rolls_back_both_prior_ctes(self):
        self.db.execute_non_query(f"alter table ops.pipeline_run add constraint refuse_receipt check (not (config_json ? '{RECEIPTS_KEY}'));")
        with self.assertRaises(PsqlExecutionError):self.persist()
        self.assertEqual(self.counts(),{'invocations':0,'artifacts':0,'receipts':0})

    def test_inactive_or_wrong_pipeline_cannot_commit_an_unreceipted_pair(self):
        for assignment in ("status='failed'", "status='running', pipeline_name='wrong'"):
            self.db.execute_non_query(f'update ops.pipeline_run set {assignment} where run_id=901;')
            with self.assertRaises(PsqlExecutionError):self.persist()
            self.assertEqual(self.counts(),{'invocations':0,'artifacts':0,'receipts':0})

    def test_invalid_receipt_container_does_not_allow_silent_jsonb_set_noop(self):
        for data in ('[]','null',f'{{"{RECEIPTS_KEY}":[]}}',f'{{"{RECEIPTS_KEY}":null}}'):
            self.db.execute_non_query(f"update ops.pipeline_run set config_json='{data}'::jsonb where run_id=901;")
            with self.assertRaises(PsqlExecutionError):self.persist()
            self.assertEqual(self.db.execute_scalar('select count(*) from ai.model_invocation;'),'0')
            self.assertEqual(self.db.execute_scalar('select count(*) from research.equity_research_artifact;'),'0')

    def test_missing_run_foreign_key_does_not_allow_an_orphan(self):
        with self.assertRaises(PsqlExecutionError):self.persist(run_id=999)
        self.assertEqual(self.counts(),{'invocations':0,'artifacts':0,'receipts':0})

    def test_failed_upsert_preserves_existing_content_and_receipt(self):
        first=self.persist()
        self.db.execute_non_query("alter table research.equity_research_artifact add constraint title_guard check (title not like '%broken%');")
        bad=replace(response(),output=replace(response().output,title='AAPL broken'))
        with self.assertRaises(PsqlExecutionError):self.persist(response=bad,request_hash='2'*64)
        self.assertEqual(self.counts(),{'invocations':1,'artifacts':1,'receipts':1})
        self.assertEqual(reconcile_result(self.db,run_id=901,request_hash=HASH)['receipt'],first)
        self.assertEqual(reconcile_result(self.db,run_id=901,request_hash=HASH)['status'],'matching')

    def test_duplicate_same_run_hash_rolls_back_instead_of_overwriting_receipt(self):
        first=self.persist()
        with self.assertRaises(PsqlExecutionError):self.persist()
        self.assertEqual(self.counts(),{'invocations':1,'artifacts':1,'receipts':1})
        self.assertEqual(reconcile_result(self.db,run_id=901,request_hash=HASH)['receipt'],first)

    def test_concurrent_same_hash_has_one_pair_without_duplicate_success_log(self):
        sql=render_atomic_result_sql(**arguments());barrier=Barrier(2)
        def submit():
            barrier.wait(timeout=10)
            try:return self.db.execute_scalar(sql)
            except PsqlExecutionError:return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            a=pool.submit(submit);b=pool.submit(submit);results=[a.result(),b.result()]
        self.assertEqual(sum(r is not None for r in results),1)
        self.assertEqual(self.counts(),{'invocations':1,'artifacts':1,'receipts':1})
        self.assertEqual(reconcile_result(self.db,run_id=901,request_hash=HASH)['status'],'matching')

    def test_concurrent_different_symbols_preserve_both_receipt_entries(self):
        barrier=Barrier(2)
        def submit(symbol,key):
            barrier.wait(timeout=10);return self.persist(context=context(symbol),request_hash=key)
        with ThreadPoolExecutor(max_workers=2) as pool:
            a=pool.submit(submit,'AAPL',HASH);b=pool.submit(submit,'NVDA','2'*64)
            a.result();b.result()
        self.assertEqual(self.counts(),{'invocations':2,'artifacts':2,'receipts':2})
        for key in (HASH,'2'*64):self.assertEqual(reconcile_result(self.db,run_id=901,request_hash=key)['status'],'matching')

    def test_fallback_keeps_failed_attempt_and_commits_artifact_receipt_without_model_success(self):
        failed=self.failure_invocation()
        receipt=self.persist(response=replace(response(),provider='fixture'),failed_invocation_id=failed)
        self.assertEqual(self.counts(),{'invocations':1,'artifacts':1,'receipts':1})
        self.assertIsNone(receipt['invocation_id']);self.assertEqual(receipt['failed_invocation_id'],failed)
        self.assertEqual(self.db.execute_scalar('select status from ai.model_invocation;'),'failed')
        self.assertEqual(reconcile_result(self.db,run_id=901,request_hash=HASH)['status'],'matching')

    def test_fallback_write_failure_preserves_real_failed_attempt_but_no_artifact(self):
        failed=self.failure_invocation()
        self.db.execute_non_query("alter table research.equity_research_artifact add constraint reject_report check (false);")
        with self.assertRaises(PsqlExecutionError):self.persist(response=replace(response(),provider='fixture'),failed_invocation_id=failed)
        self.assertEqual(self.counts(),{'invocations':1,'artifacts':0,'receipts':0})

    def test_missing_or_wrong_failed_attempt_cannot_commit_fallback(self):
        failed=self.failure_invocation(run_id=902)
        for key in (failed,999):
            with self.assertRaises(PsqlExecutionError):self.persist(response=replace(response(),provider='fixture'),failed_invocation_id=key)
        self.assertEqual(self.counts(),{'invocations':1,'artifacts':0,'receipts':0})

    def test_receipt_detects_report_and_invocation_modification(self):
        self.persist()
        self.db.execute_non_query("update research.equity_research_artifact set title='changed';")
        self.assertEqual(reconcile_result(self.db,run_id=901,request_hash=HASH)['status'],'conflicting')
        # A separate fresh result gives a valid artifact but changed invocation.
        self.persist(request_hash='2'*64,context=context('NVDA'))
        self.db.execute_non_query("update ai.model_invocation set status='failed';")
        self.assertEqual(reconcile_result(self.db,run_id=901,request_hash='2'*64)['status'],'conflicting')

    def test_later_run_overwrite_is_not_mistaken_for_prior_result(self):
        first=self.persist()
        self.persist(run_id=902,request_hash='2'*64)
        self.assertEqual(self.counts(),{'invocations':2,'artifacts':1,'receipts':2})
        old=reconcile_result(self.db,run_id=901,request_hash=HASH)
        self.assertEqual(old['receipt'],first);self.assertEqual(old['status'],'conflicting')
        self.assertEqual(reconcile_result(self.db,run_id=902,request_hash='2'*64)['status'],'matching')

    def test_not_observed_is_never_proof_that_retry_is_safe(self):
        self.failure_invocation()
        result=reconcile_result(self.db,run_id=901,request_hash=HASH)
        self.assertEqual(result['status'],'not_observed');self.assertFalse(result['automatic_retry_allowed'])

    def test_literal_source_and_timezones_do_not_corrupt_receipt_fingerprints(self):
        r=replace(response(),output=replace(response().output,korean_summary="AAPL's 수익; select 'x'; \\ data <tag>"))
        self.persist(response=r)
        for zone in ('UTC','Asia/Seoul','America/New_York'):
            class Zoned:
                def execute_scalar(_,sql):return self.db.execute_scalar(f"set timezone='{zone}';\n"+sql)
            self.assertEqual(reconcile_result(Zoned(),run_id=901,request_hash=HASH)['status'],'matching')

    def test_actual_runner_lost_ack_preserves_committed_result_and_stops_without_retry(self):
        calls=[];db=self.db
        class Hybrid:
            def execute_scalar(_,sql):
                if sql.startswith('-- equity research symbol lookup'):return '["AAPL"]'
                if sql.startswith('-- equity research context lookup'):return json.dumps(context('AAPL'))
                raw=db.execute_scalar(sql)
                if sql.startswith('-- equity atomic result'):
                    calls.append(sql);raise PsqlExecutionError('synthetic acknowledgement lost AFTER COMMIT')
                return raw
            def execute_non_query(_,sql):return db.execute_non_query(sql)
        with self.assertRaises(EquityResearchBatchError) as caught:
            equity.run_equity_research_reporting(config=SimpleNamespace(),as_of_date=DAY,executor=Hybrid(),
                provider=equity.CODEX_OAUTH_PROVIDER,provider_runner=lambda *_:response(),execute=True)
        report=caught.exception.report
        self.assertEqual(len(calls),1);self.assertEqual(report['inserted_artifact_count'],0)
        self.assertTrue(report['fatal_error']['persistence_outcome_unknown'])
        self.assertEqual(self.counts(),{'invocations':1,'artifacts':1,'receipts':1})
        result=reconcile_result(db,run_id=report['run_id'],request_hash=report['results'][0]['request_hash'])
        self.assertEqual(result['status'],'matching');self.assertFalse(result['automatic_retry_allowed'])

    def test_actual_runner_uses_committed_receipt_on_normal_success(self):
        db=self.db
        class Hybrid:
            def execute_scalar(_,sql):
                if sql.startswith('-- equity research symbol lookup'):return '["AAPL"]'
                if sql.startswith('-- equity research context lookup'):return json.dumps(context('AAPL'))
                return db.execute_scalar(sql)
            def execute_non_query(_,sql):return db.execute_non_query(sql)
        report=equity.run_equity_research_reporting(config=SimpleNamespace(),as_of_date=DAY,executor=Hybrid(),
                provider=equity.CODEX_OAUTH_PROVIDER,provider_runner=lambda *_:response(),execute=True)
        self.assertEqual(report['status'],'completed')
        result=reconcile_result(db,run_id=report['run_id'],request_hash=report['results'][0]['request_hash'])
        self.assertEqual(result['status'],'matching')
        self.assertEqual(result['receipt'],report['results'][0]['result_receipt'])


if __name__=='__main__':unittest.main()
