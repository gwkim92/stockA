"""Run generated SQL against the dedicated disposable CI service; never a runtime DB."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from tests import test_equity_context_cutoff_postgres as checks

result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(checks))
passed = result.wasSuccessful() and result.testsRun > 0 and not result.skipped
report = {
    'verification': 'equity-context-cutoff-v1', 'tests_run': result.testsRun,
    'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
    'postgres_version': checks.POSTGRES_VERSION, 'sql_executions': checks.SQL_EXECUTIONS,
    'passed': passed, 'target': 'disposable_ci_postgres_unix_socket',
    'schema_data': 'synthetic rollback-only fixtures', 'production_database_access': False,
    'live_model_calls': 0, 'full_point_in_time_reconstruction': False,
}
(ROOT / 'equity-cutoff-report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
raise SystemExit(0 if passed else 1)
