from datetime import date
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from stockanalysis.ai import equity_research_reporting as equity
from stockanalysis.ai.equity_research_batch import EquityResearchBatchError
from stockanalysis.ai.research_source_version import public_freshness, same_version, validated_version
from stockanalysis.ingest.sec.financial_periods import PERIOD_POLICY
from stockanalysis.operations import research_report_refresh as refresh
from tests.test_equity_batch_isolation import BatchExecutor, run, provider
from tests.test_equity_atomic_persistence import arguments

DAY = date(2026, 9, 11)
VERSION = {'source_run_id': 42, 'source_sha256': 'a' * 64, 'period_policy': PERIOD_POLICY}


class SourceVersionTests(unittest.TestCase):
    def test_same_source_recollection_does_not_change_version(self):
        self.assertTrue(same_version(VERSION, {**VERSION, 'source_run_id': 43}))
        self.assertFalse(same_version(VERSION, {**VERSION, 'source_sha256': 'b' * 64}))

    def test_public_state_whitelists_fields_and_handles_bad_records(self):
        for bad in ({'source_run_id': True}, {'source_sha256': []}, 'private-value'):
            with self.subTest(bad=bad):
                result = public_freshness({'input_version': bad, 'current_version': VERSION})
                self.assertEqual(result['status'], 'invalid_version')
                self.assertNotIn('private-value', json.dumps(result))
        for used, current, expected in ((None, VERSION, 'not_recorded'), (VERSION, None, 'source_unavailable'),
            (VERSION, VERSION, 'current'), (VERSION, {**VERSION, 'source_sha256': 'b'*64}, 'source_changed')):
            self.assertEqual(public_freshness({'input_version': used, 'current_version': current})['status'], expected)

    def test_batch_records_actual_context_version_and_claim_before_provider(self):
        db = BatchExecutor(symbols=('AAPL',)); db.inputs['AAPL']['financial_source_version'] = VERSION
        seen = []
        result = run(db, provider(seen), limit=1, source_refresh_claim={'claim_id': 7, 'source_version': VERSION})
        self.assertEqual(seen, ['AAPL'])
        manifest = next(sql for stage, sql in db.writes if stage == 'pipeline_start')
        self.assertIn('financial_source_versions', manifest)
        self.assertIn('"source_refresh_claim_id": 7', manifest)
        self.assertIn(VERSION['source_sha256'], manifest)
        self.assertEqual(result['primary_report_count'], 1)

    def test_changed_source_before_provider_leaves_no_model_call(self):
        db = BatchExecutor(symbols=('AAPL',)); db.inputs['AAPL']['financial_source_version'] = {**VERSION, 'source_sha256': 'b'*64}
        seen = []
        with self.assertRaises(EquityResearchBatchError):
            run(db, provider(seen), limit=1, source_refresh_claim={'claim_id': 7, 'source_version': VERSION})
        self.assertFalse(seen)
        self.assertFalse(any(stage == 'result_write' for stage, _ in db.writes))

    def test_input_version_is_in_bounded_prompt_and_request_hash(self):
        db = BatchExecutor(symbols=('AAPL',)); context = db.inputs['AAPL']
        context['financial_source_version'] = VERSION
        bounded = equity._bounded_context_for_prompt(context, max_context_chars=16000)
        self.assertEqual(bounded['financial_source_version'], VERSION)
        first = equity.build_equity_research_request_hash(context=context, provider='codex_oauth', model_name='test', prompt_template_id=1, max_context_chars=16000)
        context['financial_source_version'] = {**VERSION, 'source_sha256': 'b'*64}
        second = equity.build_equity_research_request_hash(context=context, provider='codex_oauth', model_name='test', prompt_template_id=1, max_context_chars=16000)
        self.assertNotEqual(first, second)


class WorkerDB:
    def __init__(self, claim=True, used=0):
        self.used = used; self.claim = claim; self.writes = []; self.reads = []

    def execute_scalar(self, sql):
        self.reads.append(sql)
        if sql.startswith('select (now()'): return DAY.isoformat()
        if sql.startswith('-- pending'): return '[]'
        if sql.startswith('-- research source refresh queue'): return json.dumps({'queue': [], 'daily_used': self.used})
        if sql.startswith('-- reserve'):
            return json.dumps({'daily_used': self.used, 'claim': {'run_id': 9, 'request': {
                'symbol': 'AAPL', 'source_version': VERSION, 'generation_key': 'c'*64}} if self.claim else None})
        raise AssertionError(sql[:80])

    def execute_non_query(self, sql): self.writes.append(sql)


class RefreshRunnerTests(unittest.TestCase):
    def execute(self, db, runner, execute=True):
        return refresh.run_research_report_refresh(config=SimpleNamespace(), as_of_date=DAY, execute=execute,
            executor=db, report_runner=runner, model_name='mock-model')

    def test_budget_exhaustion_and_no_changes_do_not_call_model(self):
        for used, expected in ((5, 'daily_limit'), (0, 'no_op')):
            runner = unittest.mock.Mock()
            result = self.execute(WorkerDB(claim=False, used=used), runner)
            self.assertEqual(result['status'], expected); runner.assert_not_called()

    def test_preview_does_not_reserve_or_generate(self):
        db, runner = WorkerDB(), unittest.mock.Mock()
        self.assertEqual(self.execute(db, runner, False)['status'], 'planned')
        self.assertFalse(any('-- reserve' in sql for sql in db.reads)); runner.assert_not_called()

    def test_success_requires_actual_matching_receipt(self):
        db = WorkerDB(); receipt = {'request_hash': 'd'*64, 'outcome': 'primary'}
        runner = unittest.mock.Mock(return_value={'run_id': 10, 'results': [{'provider_attempted': True, 'result_receipt': receipt}]})
        with patch.object(refresh, 'reconcile_result', return_value={'status': 'matching', 'receipt': receipt}):
            result = self.execute(db, runner)
        self.assertEqual(result['status'], 'succeeded')
        self.assertEqual(runner.call_args.kwargs['limit'], 1)
        self.assertEqual(runner.call_args.kwargs['source_refresh_claim']['source_version'], VERSION)
        self.assertIn("status='succeeded'", db.writes[-1])

    def test_lost_storage_ack_is_retained_and_never_automatically_retried(self):
        db = WorkerDB(); runner = unittest.mock.Mock(side_effect=RuntimeError('private-token'))
        result = self.execute(db, runner)
        self.assertEqual(result['status'], 'reconcile')
        self.assertEqual(runner.call_count, 1); self.assertFalse(db.writes)
        self.assertNotIn('private-token', json.dumps(result))

    def test_fallback_is_not_successful_source_refresh(self):
        db = WorkerDB(); receipt = {'request_hash': 'd'*64, 'outcome': 'fallback'}
        runner = lambda **_: {'run_id': 10, 'results': [{'provider_attempted': True, 'result_receipt': receipt}]}
        with patch.object(refresh, 'reconcile_result', return_value={'status': 'matching', 'receipt': receipt}):
            result = self.execute(db, runner)
        self.assertEqual(result['status'], 'failed')

    def test_generation_policy_changes_for_model_or_prompt_but_not_date(self):
        self.assertEqual(refresh.generation_policy('m'), refresh.generation_policy('m'))
        self.assertNotEqual(refresh.generation_policy('m'), refresh.generation_policy('n'))
        with patch.object(equity, 'DEFAULT_TEMPLATE_VERSION', 'next'):
            changed = refresh.generation_policy('m')
        self.assertNotEqual(refresh.generation_policy('m'), changed)


if __name__ == '__main__': unittest.main()
