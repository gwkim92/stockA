from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import date
import json
import unittest
from unittest.mock import patch

from stockanalysis.ai import equity_research_reporting as equity
from stockanalysis.ai.equity_research_batch import EquityResearchBatchError
from stockanalysis.ai.equity_research_persistence import (
    render_atomic_result_sql, parse_acknowledgement, render_reconciliation_sql,
    reconcile_result, validate_receipt,
)
from stockanalysis.ai_agents.prompt_contract import PromptContractError
from stockanalysis.ingest.psql import PsqlExecutionError
from tests.test_equity_batch_isolation import BatchExecutor, context, provider, run, artifact_sql
from tests.test_equity_research_contract_v3 import response
from tests.equity_persistence_fakes import fake_atomic_ack

HASH = '1' * 64
DAY = date(2026, 5, 25)


def arguments(**changes):
    return dict(context=context('AAPL'), response=response(0), as_of_date=DAY,
                run_id=901, prompt_template_id=44, request_hash=HASH, **changes)


def ack():
    return json.loads(fake_atomic_ack(render_atomic_result_sql(**arguments())))


class AtomicSqlTests(unittest.TestCase):
    def test_primary_reuses_existing_writes_as_one_statement_with_a_durable_receipt(self):
        args = arguments()
        sql = render_atomic_result_sql(**args)
        artifact = equity.render_equity_research_artifact_upsert_sql(context=args['context'], response=args['response'],
                    as_of_date=DAY, source_run_id=901).removesuffix('returning artifact_id;')
        self.assertIn(artifact, sql)
        self.assertEqual(sql.count('insert into ai.model_invocation'), 1)
        self.assertEqual(sql.count('insert into research.equity_research_artifact'), 1)
        self.assertEqual(sql.count('update ops.pipeline_run'), 1)
        self.assertIn('1 / (select count(*) from stored_receipt)', sql)
        self.assertIn("p.status = 'running'", sql)
        self.assertIn('equity_result_receipts_v1', sql)
        self.assertNotIn('create table', sql)
        self.assertNotIn('commit;', sql)

    def test_fallback_references_the_failed_attempt_without_creating_a_successful_model_log(self):
        args = arguments(failed_invocation_id=77)
        args['response'] = replace(args['response'], provider='fixture')
        sql = render_atomic_result_sql(**args)
        self.assertIn('where invocation_id = 77 and run_id = 901', sql)
        self.assertIn("status = 'failed'", sql)
        self.assertNotIn('insert into ai.model_invocation', sql)
        self.assertIn("'invocation_id', null", sql)

    def test_known_builder_tail_is_checked_instead_of_splitting_embedded_semicolons(self):
        args = arguments()
        args['response'] = replace(args['response'], output=replace(args['response'].output,
                               korean_summary="It's a source; not SQL; 한글"))
        sql = render_atomic_result_sql(**args)
        self.assertIn("It''s a source; not SQL; 한글", sql)
        with patch.object(equity, 'render_equity_research_artifact_upsert_sql', return_value='changed contract'):
            with self.assertRaisesRegex(PromptContractError, 'persistence_builder_changed'):
                render_atomic_result_sql(**args)

    def test_invalid_run_hash_prompt_and_fallback_identity_fail_before_io(self):
        for key, values in {'run_id': [True, 0, -1, '901', 2**63], 'request_hash': ['x', "' OR true", 'A'*64],
                            'prompt_template_id': [None, True, 0], 'failed_invocation_id': [0, '1', True]}.items():
            for value in values:
                args = arguments(); args[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(PromptContractError):
                    render_atomic_result_sql(**args)

    def test_non_fixture_fallback_cannot_be_presented_as_deterministic(self):
        with self.assertRaisesRegex(PromptContractError, 'fallback_provider_mismatch'):
            render_atomic_result_sql(**arguments(failed_invocation_id=77))

    def test_schema_invalid_report_is_rejected_during_serialization(self):
        args = arguments(); args['response'] = replace(response(), output=replace(response().output, key_points='bad'))
        with self.assertRaises(PromptContractError):
            render_atomic_result_sql(**args)

    def test_source_input_is_unchanged_by_receipt_construction(self):
        args = arguments(); before = deepcopy(args['context'])
        render_atomic_result_sql(**args)
        self.assertEqual(args['context'], before)


class ReceiptTests(unittest.TestCase):
    def test_primary_ack_retains_exact_identity(self):
        actual = parse_acknowledgement(ack(), run_id=901, request_hash=HASH)
        self.assertEqual(actual['artifact_id'], 9901)
        self.assertEqual(actual['instrument_id'], 101)
        self.assertIsNone(actual['failed_invocation_id'])

    def test_missing_extra_duplicate_and_boolean_acknowledgements_are_rejected(self):
        cases = [{}, {**ack(), 'extra': 'private'}, {**ack(), 'acknowledged': True},
                 {**ack(), 'acknowledged': 0}, '[]', '{"acknowledged":1,"acknowledged":1}']
        for payload in cases:
            with self.subTest(payload=payload), self.assertRaises(PromptContractError):
                parse_acknowledgement(payload, run_id=901, request_hash=HASH)

    def test_swapped_receipt_and_false_integer_ids_are_rejected(self):
        for field, bad in [('run_id', 902), ('run_id', True), ('request_hash', '2'*64),
                           ('artifact_id', True), ('instrument_id', '101'), ('invocation_id', -1),
                           ('as_of_date','2026-02-30'), ('as_of_date','20260525'),
                           ('result_fingerprint','wrong'), ('failed_invocation_id',99)]:
            payload = ack(); payload['receipt'][field] = bad
            with self.subTest(field=field), self.assertRaises(PromptContractError):
                parse_acknowledgement(payload, run_id=901, request_hash=HASH)

    def test_receipt_cannot_smuggle_source_text_into_diagnostics(self):
        payload = ack(); payload['receipt']['raw_source'] = 'private source body'
        with self.assertRaises(PromptContractError) as caught:
            parse_acknowledgement(payload, run_id=901, request_hash=HASH)
        self.assertNotIn('private source body', str(caught.exception))

    def test_fallback_receipt_does_not_invent_a_success_invocation(self):
        args = arguments(failed_invocation_id=77); args['response'] = replace(response(), provider='fixture')
        receipt = parse_acknowledgement(fake_atomic_ack(render_atomic_result_sql(**args)), run_id=901, request_hash=HASH)
        self.assertIsNone(receipt['invocation_id']); self.assertEqual(receipt['failed_invocation_id'], 77)


class ReconciliationTests(unittest.TestCase):
    def test_generated_reconciliation_is_only_a_snapshot_select(self):
        sql = render_reconciliation_sql(run_id=901, request_hash=HASH).lower()
        for forbidden in ('insert into', 'update ', 'delete ', 'for update', 'pg_advisory', 'create '):
            self.assertNotIn(forbidden, sql)
        self.assertIn('request_hash', sql)
        self.assertIn('result_fingerprint', sql)
        self.assertIn('invocation_fingerprint', sql)

    def test_matching_missing_and_conflicting_do_not_authorize_retry(self):
        for state in ('matching', 'not_observed', 'conflicting'):
            class Executor:
                def execute_scalar(self, sql):
                    return json.dumps({'status': state, 'receipt': None if state=='not_observed' else ack()['receipt']})
            data = reconcile_result(Executor(), run_id=901, request_hash=HASH)
            self.assertEqual(data['status'], state); self.assertFalse(data['automatic_retry_allowed'])

    def test_invalid_reconciliation_response_is_not_accepted_as_a_match(self):
        for data in ({'status':'matching','receipt':None}, {'status':'not_observed','receipt':ack()['receipt']},
                     {'status':'matching','receipt':ack()['receipt'],'automatic_retry_allowed':True}):
            class Executor:
                def execute_scalar(self, sql): return json.dumps(data)
            with self.subTest(data=data), self.assertRaises(PromptContractError):
                reconcile_result(Executor(), run_id=901, request_hash=HASH)

    def test_database_outage_is_not_an_absence_result_or_an_automatic_read_retry(self):
        calls = []
        class Executor:
            def execute_scalar(self, sql):
                calls.append(sql); raise PsqlExecutionError('unavailable')
        with self.assertRaises(PsqlExecutionError):
            reconcile_result(Executor(), run_id=901, request_hash=HASH)
        self.assertEqual(len(calls), 1)


class AtomicBatchTests(unittest.TestCase):
    def test_batch_counts_after_single_atomic_ack_not_independent_scalar_ids(self):
        executor = BatchExecutor(('AAPL',))
        report = run(executor, provider([]))
        self.assertEqual(report['inserted_artifact_count'], 1)
        writes = [s for stage,s in executor.writes if stage in ('result_write','success_record','artifact_write')]
        self.assertEqual(len(writes), 1)
        self.assertEqual(report['results'][0]['result_receipt']['request_hash'], report['results'][0]['request_hash'])

    def test_invalid_ack_is_uncertain_not_counted_and_never_triggers_fallback(self):
        executor = BatchExecutor(); original = executor.execute_scalar; seen=[]
        def execute(sql):
            raw = original(sql)
            return '{"acknowledged":1,"receipt":{}}' if sql.startswith('-- equity atomic result') else raw
        executor.execute_scalar = execute
        with patch.object(equity,'build_fixture_equity_research_response') as fallback:
            with self.assertRaises(EquityResearchBatchError) as caught:
                run(executor,provider(seen))
            fallback.assert_not_called()
        report = caught.exception.report
        self.assertEqual(seen,['AAPL']); self.assertEqual(report['inserted_artifact_count'],0)
        self.assertEqual(report['fatal_error']['stage'],'result_acknowledgement')
        self.assertTrue(report['fatal_error']['persistence_outcome_unknown'])
        self.assertIn('request_hash',report['results'][0])

    def test_swapped_instrument_ack_stops_without_counting_wrong_report(self):
        executor = BatchExecutor(('AAPL',)); original = executor.execute_scalar
        def execute(sql):
            raw = original(sql)
            if sql.startswith('-- equity atomic result'):
                data=json.loads(raw);data['receipt']['instrument_id']=999;return json.dumps(data)
            return raw
        executor.execute_scalar=execute
        with self.assertRaises(EquityResearchBatchError) as caught:
            run(executor,provider([]))
        self.assertEqual(caught.exception.report['inserted_artifact_count'],0)

    def test_partial_batch_diagnostic_redacts_model_labels_inside_receipts(self):
        executor=BatchExecutor(('AAPL','NVDA'), inputs={'NVDA':{'instrument':None}})
        with self.assertRaises(EquityResearchBatchError) as caught:
            run(executor,lambda *_:replace(response(),model_name='private-model-label'))
        self.assertEqual(caught.exception.report['inserted_artifact_count'],1)
        self.assertNotIn('private-model-label',str(caught.exception))

    def test_fallback_keeps_original_failure_log_and_has_its_own_result_receipt(self):
        executor=BatchExecutor(('AAPL',))
        report=run(executor,provider([],fail={'AAPL'}))
        self.assertEqual(report['status'],'completed_with_fallback')
        receipt=report['results'][0]['result_receipt']
        self.assertEqual(receipt['outcome'],'fallback')
        self.assertIsNone(receipt['invocation_id'])
        self.assertEqual(receipt['failed_invocation_id'],report['results'][0]['failed_invocation_id'])
        self.assertEqual(sum(stage=='failure_record' for stage,_ in executor.writes),1)
        self.assertEqual(len(artifact_sql(executor)),1)


if __name__=='__main__': unittest.main()
