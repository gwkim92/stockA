from __future__ import annotations

from copy import deepcopy
import io
import json
import os
from pathlib import Path
import subprocess
import tomllib
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from stockanalysis.operations import equity_result_check as check
from stockanalysis.ai_agents.prompt_contract import PromptContractError
from stockanalysis.ingest.config import ConfigError, RuntimeConfig
from stockanalysis.ingest.psql import PsqlExecutionError
from tests.test_equity_atomic_persistence import ack, HASH


def payload(state='matching'):
    return {'status': state, 'receipt': None if state == 'not_observed' else ack()['receipt']}


class Reader:
    def __init__(self, data=None, error=None):
        self.data = payload() if data is None else data
        self.error = error
        self.calls = []

    def execute_scalar(self, sql):
        self.calls.append(sql)
        if self.error is not None:
            raise self.error
        return json.dumps(self.data)


def invoke(reader, *extra):
    out, err = io.StringIO(), io.StringIO()
    code = check.main(['--run-id', '901', '--request-hash', HASH, *extra],
                      stdout=out, stderr=err, reader=reader)
    return code, out.getvalue(), err.getvalue()


class ResultCheckTests(unittest.TestCase):
    def test_matching_report_retains_ids_but_not_provider_or_model_labels(self):
        reader = Reader()
        result = check.check_result(run_id=901, request_hash=HASH, reader=reader)
        self.assertEqual(result['status'], 'matching')
        self.assertEqual(result['receipt']['artifact_id'], 9901)
        self.assertNotIn('provider', result['receipt'])
        self.assertNotIn('model_name', result['receipt'])
        self.assertEqual(len(reader.calls), 1)
        self.assertTrue(result['read_only'])
        self.assertFalse(result['automatic_retry_allowed'])
        self.assertFalse(result['model_invoked'])
        self.assertFalse(result['pipeline_status_changed'])

    def test_actual_cli_has_distinct_text_and_json_exit_codes(self):
        for state, code in [('matching', 0), ('conflicting', 3), ('not_observed', 4)]:
            for fmt in ['text', 'json']:
                with self.subTest(state=state, format=fmt):
                    actual, out, err = invoke(Reader(payload(state)), '--format', fmt)
                    self.assertEqual(actual, code)
                    self.assertEqual(err, '')
                    if fmt == 'json':
                        result = json.loads(out)
                        self.assertEqual(result['status'], state)
                        self.assertFalse(result['automatic_retry_allowed'])
                    else:
                        self.assertIn(check.MESSAGES[state][0], out)
                        self.assertIn('자동 재시도 없음', out)
                        self.assertIn('분석 정확도', out)

    def test_missing_receipt_does_not_claim_definite_rollback(self):
        code, out, _ = invoke(Reader(payload('not_observed')))
        self.assertEqual(code, 4)
        self.assertIn('저장 실패가 확정된 것은 아닙니다', out)
        self.assertNotIn('보고서 ID:', out)

    def test_fallback_output_does_not_call_it_a_successful_model_invocation(self):
        data = payload()
        data['receipt'].update(outcome='fallback', invocation_id=None, failed_invocation_id=77)
        code, out, _ = invoke(Reader(data))
        self.assertEqual(code, 0)
        self.assertIn('규칙 기반 대체 경로', out)
        self.assertIn('연결 호출 ID: 77', out)
        self.assertNotIn('정상 제공자 경로', out)

    def test_model_source_control_characters_never_reach_public_output(self):
        data = payload()
        data['receipt'].update(provider='secret-provider\x1b[31m', model_name='secret-model\nsource-text')
        for fmt in ('text', 'json'):
            _, out, err = invoke(Reader(data), '--format', fmt)
            self.assertNotIn('secret', out + err)
            self.assertNotIn('\x1b', out + err)
            self.assertNotIn('source-text', out + err)

    def test_reader_receives_one_read_only_transaction_with_local_limits(self):
        reader = Reader()
        check.check_result(run_id=901, request_hash=HASH, reader=reader)
        self.assertEqual(len(reader.calls), 1)
        sql = reader.calls[0]
        self.assertTrue(sql.startswith('BEGIN READ ONLY;'))
        self.assertTrue(sql.endswith('ROLLBACK;\n'))
        for setting in ("statement_timeout = '5s'", "lock_timeout = '1s'",
                        "idle_in_transaction_session_timeout = '8s'", 'search_path = pg_catalog',
                        "TIME ZONE 'UTC'", "DateStyle = 'ISO, YMD'"):
            self.assertIn('SET LOCAL ' + setting, sql)
        for write in ('insert into', 'update ops.', 'delete from', 'for update'):
            self.assertNotIn(write, sql.lower())

    def test_invalid_identity_is_rejected_before_config_or_io(self):
        cases = [(True, HASH), (0, HASH), (2**63, HASH), ('901', HASH), (901, 'secret-value')]
        for run_id, key in cases:
            reader = Reader()
            with self.subTest(run_id=run_id), patch.object(RuntimeConfig, 'from_env') as configuration:
                with self.assertRaises(PromptContractError):
                    check.check_result(run_id=run_id, request_hash=key, reader=reader)
                configuration.assert_not_called()
                self.assertEqual(reader.calls, [])

    def test_help_does_not_construct_runtime_or_connect(self):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(RuntimeConfig, 'from_env') as configuration:
            code = check.main(['--help'], stdout=out, stderr=err)
        self.assertEqual(code, 0)
        self.assertIn('--request-hash', out.getvalue())
        configuration.assert_not_called()

    def test_invalid_and_repeated_cli_options_fail_without_echo_or_database(self):
        base = ['--run-id', '901', '--request-hash', HASH]
        cases = [[], ['--run-id', 'secret-db-url', '--request-hash', HASH],
                 ['--run-id', '901', '--request-hash', 'secret-token'],
                 base + ['--execute'], base + ['--sql', 'secret-query'],
                 base + ['--run-id', '902'], base + ['--request-hash', '2'*64],
                 base + ['--format', 'json', '--format', 'text'],
                 base + ['--format', 'secret-format'],
                 ['--run-id', str(2**63), '--request-hash', HASH]]
        for args in cases:
            reader = Reader(); out, err = io.StringIO(), io.StringIO()
            with self.subTest(args=args), patch.object(RuntimeConfig, 'from_env') as config:
                code = check.main(args, reader=reader, stdout=out, stderr=err)
                config.assert_not_called()
            self.assertEqual(code, 2)
            self.assertEqual(reader.calls, [])
            self.assertNotIn('secret', out.getvalue() + err.getvalue())
            self.assertEqual(out.getvalue(), '')

    def test_configuration_missing_is_an_unavailable_result_not_not_observed(self):
        with patch.object(RuntimeConfig, 'from_env', return_value=RuntimeConfig()):
            result = check.check_result(run_id=901, request_hash=HASH)
        self.assertEqual(result['status'], 'unavailable')
        self.assertEqual(result['error_code'], 'configuration_unavailable')
        self.assertIsNone(result['receipt'])

    def test_database_errors_redact_raw_body_and_do_not_retry(self):
        for error in (PsqlExecutionError('private-db-error source-text'), OSError('private-command'),
                      ConfigError('private-config')):
            reader = Reader(error=error)
            code, out, err = invoke(reader, '--format', 'json')
            self.assertEqual(code, 1)
            self.assertEqual(json.loads(out)['status'], 'unavailable')
            self.assertNotIn('private', out + err)
            self.assertEqual(len(reader.calls), 1)

    def test_process_timeout_is_sanitized_and_never_retried(self):
        reader = Reader(error=subprocess.TimeoutExpired(['psql', 'private-password'], 15, output='secret-body'))
        code, out, err = invoke(reader, '--format', 'json')
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)['error_code'], 'check_timeout')
        self.assertNotIn('private', out + err)
        self.assertNotIn('secret', out + err)
        self.assertEqual(len(reader.calls), 1)

    def test_corrupt_receipt_or_wrong_identity_is_unavailable_not_a_match(self):
        candidates = [{'status': 'matching', 'receipt': None}, {'status': 'invented', 'receipt': None}, payload()]
        candidates[-1]['receipt']['request_hash'] = '2' * 64
        for data in candidates:
            with self.subTest(data=data):
                result = check.check_result(run_id=901, request_hash=HASH, reader=Reader(data))
                self.assertEqual(result['status'], 'unavailable')
                self.assertEqual(result['error_code'], 'invalid_stored_result')

    def test_no_model_or_atomic_write_function_is_invoked(self):
        with patch('stockanalysis.ai.equity_research_reporting._invoke_provider') as provider, \
             patch('stockanalysis.ai.equity_research_persistence.render_atomic_result_sql') as write:
            check.check_result(run_id=901, request_hash=HASH, reader=Reader())
            provider.assert_not_called(); write.assert_not_called()

    def test_interrupts_propagate_without_retry_or_repair(self):
        for error in (KeyboardInterrupt(), SystemExit(9)):
            reader = Reader(error=error)
            with self.subTest(error=type(error).__name__), self.assertRaises(type(error)):
                check.check_result(run_id=901, request_hash=HASH, reader=reader)
            self.assertEqual(len(reader.calls), 1)

    def test_programming_errors_are_not_disguised_as_missing_data(self):
        with self.assertRaises(TypeError):
            check.check_result(run_id=901, request_hash=HASH, reader=Reader(error=TypeError('bug')))

    def test_result_check_does_not_change_environment_or_reader_input(self):
        data = payload(); before = deepcopy(data); environment = dict(os.environ)
        check.check_result(run_id=901, request_hash=HASH, reader=Reader(data))
        self.assertEqual(data, before)
        self.assertEqual(dict(os.environ), environment)

    def test_cli_module_is_registered_without_a_new_dependency(self):
        project = tomllib.loads((Path(__file__).resolve().parents[1]/'pyproject.toml').read_text())['project']
        self.assertEqual(project['scripts']['stockanalysis-equity-result-check'],
                         'stockanalysis.operations.equity_result_check:main_entry')
        self.assertEqual(project['optional-dependencies']['agents'], ['openai-agents>=0.17.5,<0.18'])


class BoundedExecutorTests(unittest.TestCase):
    def test_real_executor_arguments_have_timeout_startup_isolation_and_no_prompt(self):
        db = check._BoundedPsqlReader(['psql', 'host=private-host'])
        with patch.object(subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=json.dumps(payload()), stderr='')) as proc:
            result = check.check_result(run_id=901, request_hash=HASH, reader=db)
        self.assertEqual(result['status'], 'matching')
        self.assertEqual(proc.call_count, 1)
        args, kwargs = proc.call_args
        self.assertIn('-X', args[0]); self.assertIn('-w', args[0]); self.assertIn('ON_ERROR_STOP=1', args[0])
        self.assertEqual(kwargs['timeout'], 15)
        self.assertNotIn('shell', kwargs)
        self.assertTrue(kwargs['input'].startswith('BEGIN READ ONLY;'))

    def test_failed_process_and_empty_response_never_return_receipt_absence(self):
        for result in (SimpleNamespace(returncode=3, stdout='', stderr='secret-sql'),
                       SimpleNamespace(returncode=0, stdout='', stderr='')):
            with patch.object(subprocess, 'run', return_value=result):
                code, out, _ = invoke(check._BoundedPsqlReader(['psql']), '--format', 'json')
            self.assertEqual(code, 1)
            self.assertEqual(json.loads(out)['status'], 'unavailable')
            self.assertNotIn('secret-sql', out)


if __name__ == '__main__': unittest.main()
