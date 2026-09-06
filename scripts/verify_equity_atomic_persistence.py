"""Verify committed atomic writes only in the explicitly isolated CI PostgreSQL."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'src')]
from tests import test_equity_atomic_postgres as checks
from tests import test_equity_result_check_postgres as operator_checks

suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(checks),
                            unittest.defaultTestLoader.loadTestsFromModule(operator_checks)])
result=unittest.TextTestRunner(verbosity=2).run(suite)
passed=result.wasSuccessful() and result.testsRun>0 and not result.skipped
report={
    'verification':'equity-atomic-persistence-v1','tests_run':result.testsRun,
    'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
    'postgres_version':checks.POSTGRES_VERSION,'sql_executions':checks.SQL_EXECUTIONS,'passed':passed,
    'target':'disposable_ci_postgres_unix_socket','data':'synthetic committed fixtures, schemas removed after each case',
    'write_tables':'original checked-in ops.pipeline_run, ai.prompt_template, ai.model_invocation and research.equity_research_artifact DDL',
    'production_database_access':False,'live_model_calls':0,'automatic_retry':False,'operator_cli_executions':operator_checks.CLI_EXECUTIONS,
}
(ROOT/'equity-atomic-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
raise SystemExit(0 if passed else 1)
