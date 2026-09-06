"""Actual operator entrypoint against the existing isolated synthetic database."""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import unittest

from stockanalysis.operations.equity_result_check import _ReadOnlySnapshot
from stockanalysis.ingest.psql import PsqlExecutionError
from tests import test_equity_atomic_postgres as atomic
from tests.test_equity_atomic_persistence import HASH

CLI_EXECUTIONS = 0


class EquityResultCheckPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reuse the existing strict CI-only DB identity guard and original DDL.
        atomic.EquityAtomicPostgresTests.setUpClass()

    def setUp(self):
        self.fixture = atomic.EquityAtomicPostgresTests()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.db = self.fixture.db

    def cli(self, *, missing_database=False):
        global CLI_EXECUTIONS
        command = list(self.db._base_command)
        if missing_database:
            command[command.index('stocka_atomic_test')] = 'stocka_atomic_missing'
        env = {**os.environ, 'STOCKANALYSIS_PSQL_COMMAND': shlex.join(command)}
        CLI_EXECUTIONS += 1
        result = subprocess.run(
            [sys.executable, '-m', 'stockanalysis.operations.equity_result_check',
             '--run-id', '901', '--request-hash', HASH, '--format', 'json'],
            capture_output=True, text=True, check=False, timeout=25, env=env,
        )
        self.assertEqual(result.stderr, '')
        return result.returncode, json.loads(result.stdout)

    def test_actual_command_returns_matching_without_changing_records(self):
        receipt = self.fixture.persist()
        before = self.fixture.counts()
        code, result = self.cli()
        self.assertEqual(code, 0)
        self.assertEqual(result['status'], 'matching')
        self.assertEqual(result['receipt']['artifact_id'], receipt['artifact_id'])
        self.assertEqual(self.fixture.counts(), before)
        self.assertFalse(result['automatic_retry_allowed'])
        self.assertNotIn('model_name', result['receipt'])

    def test_actual_command_detects_overwritten_content(self):
        self.fixture.persist()
        self.db.execute_non_query("update research.equity_research_artifact set title='modified-test-report';")
        before = self.fixture.counts()
        code, result = self.cli()
        self.assertEqual(code, 3)
        self.assertEqual(result['status'], 'conflicting')
        self.assertEqual(self.fixture.counts(), before)

    def test_absent_receipt_is_nonzero_without_write_or_retry(self):
        code, result = self.cli()
        self.assertEqual(code, 4)
        self.assertEqual(result['status'], 'not_observed')
        self.assertEqual(self.fixture.counts(), {'invocations': 0, 'artifacts': 0, 'receipts': 0})
        self.assertFalse(result['automatic_retry_allowed'])

    def test_corrupt_receipt_is_unavailable_not_successful_match(self):
        self.fixture.persist()
        self.db.execute_non_query(f"""update ops.pipeline_run set config_json=jsonb_set(config_json,
            '{{equity_result_receipts_v1,{HASH},artifact_id}}','true'::jsonb) where run_id=901;""")
        code, result = self.cli()
        self.assertEqual(code, 1)
        self.assertEqual(result['error_code'], 'invalid_stored_result')
        self.assertEqual(result['status'], 'unavailable')

    def test_missing_database_is_not_misreported_as_missing_receipt(self):
        code, result = self.cli(missing_database=True)
        self.assertEqual(code, 1)
        self.assertEqual(result['status'], 'unavailable')
        self.assertEqual(result['error_code'], 'database_unavailable')
        self.assertNotIn('stocka_atomic_missing', json.dumps(result))
        self.assertEqual(self.fixture.counts(), {'invocations': 0, 'artifacts': 0, 'receipts': 0})

    def test_matching_receipt_does_not_change_failed_pipeline_status(self):
        self.fixture.persist()
        self.db.execute_non_query("update ops.pipeline_run set status='failed' where run_id=901;")
        code, result = self.cli()
        self.assertEqual(code, 0)
        self.assertFalse(result['pipeline_status_changed'])
        self.assertEqual(self.db.execute_scalar('select status from ops.pipeline_run where run_id=901;'), 'failed')

    def test_read_only_transaction_rejects_accidental_database_update(self):
        with self.assertRaises(PsqlExecutionError):
            _ReadOnlySnapshot(self.db).execute_scalar("update ops.pipeline_run set status='succeeded' where run_id=901 returning run_id;")
        self.assertEqual(self.db.execute_scalar('select status from ops.pipeline_run where run_id=901;'), 'running')

    def test_database_statement_timeout_interrupts_a_stalled_read(self):
        with self.assertRaises(PsqlExecutionError):
            _ReadOnlySnapshot(self.db).execute_scalar('select pg_sleep(6);')
        self.assertEqual(self.fixture.counts(), {'invocations': 0, 'artifacts': 0, 'receipts': 0})


if __name__ == '__main__': unittest.main()
