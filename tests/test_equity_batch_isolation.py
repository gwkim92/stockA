from __future__ import annotations

from copy import deepcopy
from contextlib import ExitStack
from pathlib import Path
from dataclasses import replace
from datetime import date, datetime
import io
import itertools
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from stockanalysis.ai import equity_research_reporting as equity
from stockanalysis.ai.equity_research_batch import EquityResearchBatchError
from stockanalysis.ai_agents.prompt_contract import PromptContractError
from stockanalysis.ingest.psql import PsqlExecutionError
from tests.test_equity_research_reporting import FakeEquityResearchExecutor, _context_payload
from tests.test_equity_research_contract_v3 import response

DAY = date(2026, 5, 25)


def context(symbol):
    data = deepcopy(_context_payload())
    data['query']['symbol'] = symbol
    data['instrument']['primary_symbol'] = symbol
    data['instrument']['instrument_id'] = {'AAPL': 101, 'NVDA': 102, 'MSFT': 103}.get(symbol, 999)
    data['recent_events'][0]['document_id'] = data['instrument']['instrument_id'] + 7000
    return data


class BatchExecutor(FakeEquityResearchExecutor):
    def __init__(self, symbols=('AAPL', 'NVDA', 'MSFT'), inputs=None, fail_stage=None):
        super().__init__()
        self.symbols = list(symbols)
        self.inputs = {s: context(s) for s in symbols}
        self.inputs.update(inputs or {})
        self.fail_stage = fail_stage
        self.writes = []
        self.lookups = []
        self.fail_after_recording = False

    def execute_scalar(self, sql):
        if sql.startswith('-- equity research symbol lookup'):
            self.scalar_sql.append(sql)
            if self.fail_stage == 'symbol_lookup':
                raise PsqlExecutionError('private-database-address')
            return json.dumps(self.symbols)
        if sql.startswith('-- equity research context lookup'):
            self.scalar_sql.append(sql)
            symbol = next(s for s in self.symbols if f"'{s}'" in sql)
            self.lookups.append(symbol)
            value = self.inputs[symbol]
            if isinstance(value, BaseException):
                raise value
            return value if isinstance(value, str) else json.dumps(value)
        stage = next((key for key, marker in (
            ('result_write', '-- equity atomic result v1'),
            ('pipeline_start', 'insert into ops.pipeline_run'),
            ('prompt_registration', 'insert into ai.prompt_template'),
            ('artifact_write', 'insert into research.equity_research_artifact'),
            ('failure_record', "    'failed',"), ('success_record', "    'succeeded',"),
        ) if marker in sql), None)
        self.writes.append((stage, sql))
        if self.fail_stage == stage:
            self.scalar_sql.append(sql)
            raise PsqlExecutionError('private-database-address secret-input')
        return super().execute_scalar(sql)

    def execute_non_query(self, sql):
        self.non_query_sql.append(sql)
        if self.fail_stage == 'pipeline_finish' and "status = 'succeeded'" in sql:
            raise PsqlExecutionError('private-status-update-error')


def run(executor, runner=None, execute=True, **kwargs):
    return equity.run_equity_research_reporting(
        config=SimpleNamespace(), as_of_date=DAY, provider=equity.CODEX_OAUTH_PROVIDER,
        executor=executor, provider_runner=runner, execute=execute, **kwargs,
    )


def provider(seen, fail=()):
    def invoke(data, *_):
        symbol = data['instrument']['primary_symbol']
        seen.append(symbol)
        if symbol in fail:
            raise RuntimeError('private-model-body credentials=do-not-log')
        return response(0)
    return invoke


def artifact_sql(executor):
    return [sql for stage, sql in executor.writes if stage in ('artifact_write', 'result_write')]


class BatchInputTests(unittest.TestCase):
    def oversized(self, symbol):
        data = context(symbol)
        data['thesis']['summary'] = 'private-risk-' * 10000
        return data

    def assert_counts(self, report):
        self.assertEqual(report['symbol_count'], len(report['results']))
        self.assertEqual(report['symbol_count'], report['inserted_artifact_count'] + report['unreported_artifact_count'])
        self.assertEqual(report['inserted_artifact_count'], report['primary_report_count'] + report['fallback_artifact_count'])
        self.assertFalse(report['recommendation_scoring_mutated'])
        self.assertFalse(report['broker_order_submit_enabled'])

    def test_bad_symbol_in_every_position_does_not_stop_other_symbols(self):
        for symbols in itertools.permutations(['AAPL', 'NVDA', 'MSFT']):
            with self.subTest(order=symbols):
                executor = BatchExecutor(symbols, {'NVDA': self.oversized('NVDA')})
                seen = []
                with self.assertRaises(EquityResearchBatchError) as caught:
                    run(executor, provider(seen))
                report = caught.exception.report
                self.assertEqual(seen, [s for s in symbols if s != 'NVDA'])
                self.assertEqual([r['symbol'] for r in report['results']], list(symbols))
                self.assertEqual(report['status'], 'completed_with_failures')
                self.assertEqual(report['prepared_symbol_count'], 2)
                self.assertEqual(report['input_error_count'], 1)
                self.assertEqual(len(artifact_sql(executor)), 2)
                rejected = next(r for r in report['results'] if r['symbol'] == 'NVDA')
                self.assertEqual(rejected['error_code'], 'input_budget_exceeded')
                self.assertFalse(rejected['provider_attempted'])
                self.assertTrue(any("status = 'failed'" in s for s in executor.non_query_sql))
                self.assertNotIn('private-risk-', str(caught.exception))
                self.assert_counts(report)

    def test_all_rejected_inputs_make_no_run_invocation_or_artifact(self):
        executor = BatchExecutor(('AAPL', 'NVDA'), {s: self.oversized(s) for s in ('AAPL', 'NVDA')})
        seen = []
        with self.assertRaisesRegex(PromptContractError, 'input_budget_exceeded') as caught:
            run(executor, provider(seen))
        self.assertEqual(caught.exception.report['status'], 'failed')
        self.assertIsNone(caught.exception.report['run_id'])
        self.assertEqual(executor.writes, [])
        self.assertEqual(executor.non_query_sql, [])
        self.assertEqual(seen, [])
        self.assert_counts(caught.exception.report)

    def test_malformed_json_and_missing_instruments_are_item_local(self):
        for bad in ('not-json', '[]', {'instrument': None}, '{"instrument":null,"instrument":{}}'):
            with self.subTest(bad=bad):
                executor = BatchExecutor(('AAPL', 'NVDA'), {'AAPL': bad})
                seen = []
                with self.assertRaises(EquityResearchBatchError) as caught:
                    run(executor, provider(seen))
                self.assertEqual(seen, ['NVDA'])
                self.assertEqual(caught.exception.report['input_error_count'], 1)
                self.assertEqual(caught.exception.report['inserted_artifact_count'], 1)

    def test_context_symbol_date_and_integer_identity_are_required(self):
        samples = []
        for field, value in [('primary_symbol', 'OTHER'), ('instrument_id', True), ('instrument_id', '101'), ('instrument_id', 0)]:
            data = context('AAPL'); data['instrument'][field] = value; samples.append(data)
        for field, value in [('symbol', 'OTHER'), ('as_of_date', '2026-05-26')]:
            data = context('AAPL'); data['query'][field] = value; samples.append(data)
        for data in samples:
            with self.subTest(data=data['instrument']):
                executor = BatchExecutor(('AAPL', 'NVDA'), {'AAPL': data}); seen = []
                with self.assertRaises(EquityResearchBatchError):
                    run(executor, provider(seen))
                self.assertEqual(seen, ['NVDA'])
                self.assertEqual(len(artifact_sql(executor)), 1)
                self.assertIn("values (\n    102,", artifact_sql(executor)[0])

    def test_nonfinite_nested_input_cannot_be_coerced_into_a_valid_context(self):
        data = context('AAPL'); data['valuations'][0]['confidence'] = float('nan')
        executor = BatchExecutor(('AAPL', 'NVDA'), {'AAPL': data}); seen = []
        with self.assertRaises(EquityResearchBatchError) as caught:
            run(executor, provider(seen))
        self.assertEqual(seen, ['NVDA'])
        self.assertEqual(caught.exception.report['results'][0]['error_code'], 'nonfinite_json_number')

    def test_no_selected_symbols_is_a_noop_with_complete_zero_counts(self):
        executor = BatchExecutor(())
        report = run(executor, provider([]))
        self.assertEqual(report['status'], 'completed')
        self.assertEqual(report['results'], [])
        self.assertIsNone(report['run_id'])
        self.assertEqual(executor.writes, [])
        self.assert_counts(report)

    def test_single_healthy_symbol_retains_public_success_semantics(self):
        executor = BatchExecutor(('NVDA',)); seen = []
        report = run(executor, provider(seen))
        self.assertEqual(report['status'], 'completed')
        self.assertEqual(report['failed_artifact_count'], 0)
        self.assertEqual(report['results'][0]['status'], 'reported')
        self.assertIn('"confidence": 0.0', artifact_sql(executor)[0])
        self.assert_counts(report)

    def test_invalid_global_options_fail_before_lookup(self):
        for key, values in {'limit': [True, 0, 51, '5', 5.5], 'as_of_date': [None, '2026-05-25', datetime(2026,5,25)]}.items():
            for value in values:
                executor = BatchExecutor()
                args = dict(config=SimpleNamespace(), executor=executor, as_of_date=DAY, execute=True)
                args[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    equity.run_equity_research_reporting(**args)
                self.assertEqual(executor.scalar_sql, [])

    def test_context_lookup_database_failure_is_fatal_not_a_skipped_symbol(self):
        executor = BatchExecutor(inputs={'NVDA': PsqlExecutionError('private-database-address')}); seen = []
        with self.assertRaises(EquityResearchBatchError) as caught:
            run(executor, provider(seen))
        self.assertEqual(caught.exception.report['fatal_error']['stage'], 'context_lookup')
        self.assertEqual(executor.lookups, ['AAPL', 'NVDA'])
        self.assertEqual(executor.writes, [])
        self.assertEqual(seen, [])
        self.assertNotIn('private-database-address', str(caught.exception))

    def test_context_lookup_programming_error_is_not_silently_skipped(self):
        executor = BatchExecutor(inputs={'AAPL': TypeError('implementation defect')})
        with self.assertRaises(EquityResearchBatchError) as caught:
            run(executor, provider([]))
        self.assertIn('fatal_error', caught.exception.report)
        self.assertEqual(executor.lookups, ['AAPL'])


class BatchProviderTests(unittest.TestCase):
    def test_primary_fallback_and_rejected_input_counts_do_not_overlap(self):
        bad = context('MSFT'); bad['thesis']['summary'] = 'x' * 50000
        executor = BatchExecutor(inputs={'MSFT': bad}); seen = []
        with self.assertRaises(EquityResearchBatchError) as caught:
            run(executor, provider(seen, fail={'NVDA'}))
        report = caught.exception.report
        self.assertEqual(seen, ['AAPL', 'NVDA'])
        self.assertEqual(report['primary_report_count'], 1)
        self.assertEqual(report['fallback_artifact_count'], 1)
        self.assertEqual(report['unreported_artifact_count'], 1)
        self.assertEqual(report['failed_artifact_count'], 2)
        self.assertEqual(report['provider_failure_count'], 1)
        self.assertEqual(report['input_error_count'], 1)
        self.assertEqual(report['results'][1]['status'], 'reported_with_fallback')
        self.assertIsNone(report['results'][1]['invocation_id'])
        self.assertGreater(report['results'][1]['failed_invocation_id'], 0)

    def test_all_primary_failures_with_valid_fallback_keep_existing_status(self):
        executor = BatchExecutor(); seen = []
        report = run(executor, provider(seen, fail=executor.symbols))
        self.assertEqual(report['status'], 'completed_with_fallback')
        self.assertEqual(report['fallback_artifact_count'], 3)
        self.assertEqual(report['failed_artifact_count'], 3)
        self.assertEqual(report['unreported_artifact_count'], 0)
        self.assertTrue(any("status = 'succeeded_with_fallback'" in s for s in executor.non_query_sql))

    def test_fallback_generation_failure_does_not_stop_later_primary_results(self):
        executor = BatchExecutor(); seen = []
        original = equity.build_fixture_equity_research_response
        def fallback(data, *args):
            if data['query']['symbol'] == 'NVDA':
                raise ValueError('private-fallback-data')
            return original(data, *args)
        with patch.object(equity, 'build_fixture_equity_research_response', side_effect=fallback):
            with self.assertRaises(EquityResearchBatchError) as caught:
                run(executor, provider(seen, fail={'NVDA'}))
        self.assertEqual(seen, executor.symbols)
        self.assertEqual(caught.exception.report['results'][1]['stage'], 'fallback')
        self.assertEqual(caught.exception.report['inserted_artifact_count'], 2)
        self.assertNotIn('private-fallback-data', str(caught.exception))

    def test_all_failed_fallbacks_are_failed_not_successful_empty_batch(self):
        executor = BatchExecutor(); seen = []
        with patch.object(equity, 'build_fixture_equity_research_response', side_effect=ValueError('bad fallback')):
            with self.assertRaises(EquityResearchBatchError) as caught:
                run(executor, provider(seen, fail=executor.symbols))
        self.assertEqual(caught.exception.report['status'], 'failed')
        self.assertEqual(caught.exception.report['inserted_artifact_count'], 0)
        self.assertEqual(len(artifact_sql(executor)), 0)
        self.assertEqual(seen, executor.symbols)

    def test_provider_mutation_cannot_change_saved_symbol_or_source_inventory(self):
        executor = BatchExecutor(('AAPL',))
        before = deepcopy(executor.inputs['AAPL'])
        def mutate(data, *_):
            data['instrument']['primary_symbol'] = 'EVIL'
            data['instrument']['instrument_id'] = 999999
            data['recent_events'].append({'document_id': 999999})
            data['query']['point_in_time_complete'] = True
            return response()
        report = run(executor, mutate)
        self.assertEqual(report['results'][0]['symbol'], 'AAPL')
        self.assertNotIn('999999', artifact_sql(executor)[0])
        self.assertIn("'[7101]'", artifact_sql(executor)[0])
        self.assertEqual(executor.inputs['AAPL'], before)

    def test_mutation_then_provider_error_cannot_poison_fallback(self):
        executor = BatchExecutor(('AAPL',))
        def mutate(data, *_):
            data['instrument']['primary_symbol'] = 'EVIL'
            data['recent_events'][0]['document_id'] = 999999
            raise ValueError('bad output')
        report = run(executor, mutate)
        self.assertEqual(report['status'], 'completed_with_fallback')
        self.assertIn("'[7101]'", artifact_sql(executor)[0])
        self.assertNotIn('EVIL', artifact_sql(executor)[0])

    def test_invalid_typed_output_and_invalid_fallback_never_reach_artifact(self):
        executor = BatchExecutor(('NVDA',))
        bad = replace(response(), output=replace(response().output, key_points='not-a-list'))
        with patch.object(equity, 'build_fixture_equity_research_response', return_value=bad):
            with self.assertRaises(EquityResearchBatchError):
                run(executor, lambda *_: bad)
        self.assertEqual(artifact_sql(executor), [])
        self.assertTrue(all(stage != 'success_record' for stage, _ in executor.writes))

    def test_provider_errors_are_codes_not_raw_source_in_reports_or_audit_sql(self):
        executor = BatchExecutor(('NVDA',))
        report = run(executor, provider([], fail={'NVDA'}))
        serialized = json.dumps(report) + '\n'.join(executor.scalar_sql + executor.non_query_sql)
        self.assertNotIn('private-model-body', serialized)
        self.assertNotIn('credentials=do-not-log', serialized)
        self.assertIn('provider_failed', serialized)


class BatchPersistenceTests(unittest.TestCase):
    def test_write_failure_is_never_treated_as_provider_failure(self):
        for stage in ['pipeline_start', 'prompt_registration', 'result_write', 'pipeline_finish']:
            with self.subTest(stage=stage):
                executor = BatchExecutor(('AAPL', 'NVDA'), fail_stage=stage); seen = []
                with patch.object(equity, 'build_fixture_equity_research_response', side_effect=AssertionError('fallback must not run')):
                    with self.assertRaises(EquityResearchBatchError) as caught:
                        run(executor, provider(seen))
                report = caught.exception.report
                self.assertEqual(report['fatal_error']['stage'], stage)
                self.assertTrue(report['fatal_error']['persistence_outcome_unknown'])
                self.assertEqual(report['provider_failure_count'], 0)
                self.assertNotIn('private-', str(caught.exception))
                self.assertEqual(seen, [] if stage in {'pipeline_start','prompt_registration'} else ['AAPL','NVDA'] if stage == 'pipeline_finish' else ['AAPL'])

    def test_failed_invocation_log_error_is_fatal_and_not_swallowed(self):
        executor = BatchExecutor(fail_stage='failure_record'); seen = []
        with patch.object(equity, 'build_fixture_equity_research_response') as fallback:
            with self.assertRaises(EquityResearchBatchError) as caught:
                run(executor, provider(seen, fail={'AAPL'}))
            fallback.assert_not_called()
        self.assertEqual(seen, ['AAPL'])
        self.assertEqual(caught.exception.report['fatal_error']['stage'], 'failure_record')

    def test_prior_acknowledged_artifacts_remain_counted_when_later_write_fails(self):
        executor = BatchExecutor(); original = executor.execute_scalar
        def write(sql):
            if 'insert into research.equity_research_artifact' in sql and "values (\n    102," in sql:
                raise PsqlExecutionError('connection lost after possible commit')
            return original(sql)
        executor.execute_scalar = write
        with self.assertRaises(EquityResearchBatchError) as caught:
            run(executor, provider([]))
        report = caught.exception.report
        self.assertEqual(report['inserted_artifact_count'], 1)
        self.assertEqual(report['results'][2]['status'], 'not_attempted')
        self.assertEqual(report['status'], 'failed')
        self.assertTrue(report['fatal_error']['persistence_outcome_unknown'])

    def test_control_interrupts_are_propagated_without_fallback_or_next_symbol(self):
        for exception in [KeyboardInterrupt(), SystemExit(2)]:
            executor = BatchExecutor(); seen = []
            def stop(data, *_):
                seen.append(data['query']['symbol']); raise exception
            with self.subTest(exception=type(exception).__name__), patch.object(equity, 'build_fixture_equity_research_response') as fallback:
                with self.assertRaises(type(exception)):
                    run(executor, stop)
                fallback.assert_not_called()
            self.assertEqual(seen, ['AAPL'])
            self.assertEqual(artifact_sql(executor), [])
            self.assertTrue(any('equity_batch_interrupted' in sql for sql in executor.non_query_sql))

    def test_resource_exhaustion_is_batch_fatal_instead_of_fallback(self):
        executor = BatchExecutor(); seen=[]
        def exhaust(data,*_):
            seen.append(data['query']['symbol']); raise MemoryError('private-resource-error')
        with patch.object(equity,'build_fixture_equity_research_response') as fallback:
            with self.assertRaises(EquityResearchBatchError) as caught:
                run(executor,exhaust)
            fallback.assert_not_called()
        self.assertEqual(seen,['AAPL'])
        self.assertEqual(caught.exception.report['fatal_error']['stage'],'provider')


class BatchPlanningAndCallerTests(unittest.TestCase):
    def test_execute_does_not_run_preview_to_block_a_valid_primary_report(self):
        executor = BatchExecutor(('NVDA',))
        with patch.object(equity, 'build_fixture_equity_research_response', side_effect=ValueError('broken preview')):
            report = run(executor, provider([]))
        self.assertEqual(report['status'], 'completed')
        self.assertEqual(report['artifact_preview'], [])

    def test_plan_has_no_provider_calls_writes_or_paid_generation(self):
        executor = BatchExecutor(); seen = []
        report = run(executor, provider(seen), execute=False)
        self.assertEqual(report['status'], 'planned')
        self.assertEqual(report['preview_symbols'], executor.symbols)
        self.assertEqual(len(report['artifact_preview']), 3)
        self.assertEqual(executor.writes, [])
        self.assertEqual(executor.non_query_sql, [])
        self.assertEqual(seen, [])

    def test_dry_run_reports_rejected_context_and_still_previews_valid_symbols(self):
        bad = context('NVDA'); bad['thesis']['summary'] = 'x' * 50000
        executor = BatchExecutor(inputs={'NVDA': bad})
        with self.assertRaises(EquityResearchBatchError) as caught:
            run(executor, provider([]), execute=False)
        report = caught.exception.report
        self.assertEqual(report['status'], 'planned_with_failures')
        self.assertEqual(report['preview_symbols'], ['AAPL', 'MSFT'])
        self.assertEqual(executor.writes, [])
        self.assertNotIn('artifact_preview', json.loads(str(caught.exception)))

    def test_preview_failure_is_diagnosed_without_discarding_other_previews(self):
        executor = BatchExecutor(); original = equity.build_fixture_equity_research_response
        def preview(data, *args):
            if data['query']['symbol'] == 'NVDA': raise ValueError('private-preview')
            return original(data, *args)
        with patch.object(equity,'build_fixture_equity_research_response',side_effect=preview):
            with self.assertRaises(EquityResearchBatchError) as caught:
                run(executor, execute=False)
        self.assertEqual(caught.exception.report['preview_symbols'],['AAPL','MSFT'])
        self.assertEqual(caught.exception.report['preview_error_count'],1)
        self.assertEqual(executor.writes,[])
        self.assertNotIn('private-preview',str(caught.exception))

    def test_existing_cli_emits_nonzero_and_structured_stderr_after_partial_execution(self):
        # Actual handler/main code, real runner with a fake DB and provider.
        from stockanalysis.operations.cli import main
        executor=BatchExecutor(inputs={'NVDA':{'instrument':None}})
        seen=[]
        def actual(**kwargs):
            kwargs.update(executor=executor,provider_runner=provider(seen))
            return equity.run_equity_research_reporting(**kwargs)
        out,err=io.StringIO(),io.StringIO()
        with patch('stockanalysis.operations.cli.run_equity_research_reporting',side_effect=actual):
            exit_code=main(['equity-research-reporting-run','--as-of-date','2026-05-25','--execute'],stdout=out,stderr=err)
        self.assertEqual(exit_code,1)
        self.assertEqual(out.getvalue(),'')
        result=json.loads(err.getvalue())
        self.assertEqual(result['inserted_artifact_count'],2)
        self.assertEqual(result['results'][1]['error_code'],'context_instrument_missing')
        self.assertEqual(seen,['AAPL','MSFT'])

    def test_existing_parent_pipeline_marks_failure_after_partial_child(self):
        from stockanalysis.operations import professional_coverage_expansion as parent
        from tests.test_professional_coverage_expansion import FakeCoverageExpansionExecutor
        parent_executor = FakeCoverageExpansionExecutor()
        child_executor = BatchExecutor(('AAPL', 'BABA'), {'BABA': {'instrument': None}})
        seen = []
        def child(**kwargs):
            kwargs.update(executor=child_executor, provider_runner=provider(seen))
            return equity.run_equity_research_reporting(**kwargs)
        with ExitStack() as stack:
            for name in ('run_sec_companyfacts_upsert', 'run_financial_metric_normalization',
                         'run_peer_relative_analysis', 'run_financial_forecast_inputs',
                         'run_reported_segment_footnote_parser', 'run_segment_footnote_evidence',
                         'run_sum_of_parts_valuation', 'run_valuation_snapshot',
                         'run_industry_competitive_positioning'):
                stack.enter_context(patch.object(parent, name, return_value={}))
            stack.enter_context(patch.object(parent, 'run_equity_research_reporting', side_effect=child))
            with self.assertRaises(EquityResearchBatchError) as caught:
                parent.run_professional_coverage_expansion(
                    config=SimpleNamespace(), as_of_date=DAY, limit=3, companyfacts_limit=1,
                    research_limit=2, research_provider='fixture', execute=True,
                    company_tickers_json_path=str(Path(__file__).parent / 'fixtures/sec_company_tickers_exchange_sample.json'),
                    executor=parent_executor,
                )
        self.assertEqual(seen, ['AAPL'])
        self.assertEqual(caught.exception.report['inserted_artifact_count'], 1)
        self.assertTrue(any("status = 'failed'" in sql for sql in parent_executor.non_query_sql))
        self.assertFalse(any("status = 'succeeded'" in sql for sql in parent_executor.non_query_sql))

    def test_retry_of_only_failed_symbol_does_not_touch_prior_good_symbols(self):
        bad=context('NVDA');bad['thesis']['summary']='x'*50000
        executor=BatchExecutor(inputs={'NVDA':bad})
        with self.assertRaises(EquityResearchBatchError) as caught:
            run(executor,provider([]))
        failed=[r['symbol'] for r in caught.exception.report['results'] if r['status']=='failed']
        retry=BatchExecutor(failed);seen=[]
        report=run(retry,provider(seen),symbols=failed)
        self.assertEqual(seen,['NVDA'])
        self.assertEqual(report['inserted_artifact_count'],1)
        self.assertEqual(len(artifact_sql(retry)),1)
        self.assertEqual(report['status'],'completed')


if __name__ == '__main__':
    unittest.main()
