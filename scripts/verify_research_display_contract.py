"""Offline display contract and existing live-adapter regression (no DB/model IO)."""
from __future__ import annotations
from contextlib import ExitStack
import json
from pathlib import Path
import sys
import traceback
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
SUITES = ['tests.test_research_display_contract', 'tests.test_research_display_aliases', 'tests.test_frontend_live_adapter']


def main() -> int:
    attempts: list[dict[str, object]] = []
    def denied(*args, **kwargs):
        # Report call sites, not commands/arguments that may contain source data.
        frames = traceback.extract_stack()[:-1]
        sites = [f'{Path(f.filename).name}:{f.lineno}:{f.name}' for f in frames if '/stockA/' in f.filename][-8:]
        attempts.append({'kind': 'external_io', 'sites': sites})
        raise RuntimeError('External IO forbidden in research display regression')
    with ExitStack() as guards:
        for target in ('socket.socket.connect', 'socket.create_connection', 'subprocess.Popen'):
            guards.enter_context(patch(target, side_effect=denied))
        suite = unittest.defaultTestLoader.loadTestsFromNames(SUITES)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = result.wasSuccessful() and not result.skipped and not attempts
    report = {'verification': 'research-display-contract-v1', 'suites': SUITES,
              'tests_run': result.testsRun, 'failures': len(result.failures),
              'errors': len(result.errors), 'skipped': len(result.skipped),
              'unexpected_io_attempts': len(attempts), 'io_call_sites': attempts, 'passed': passed,
              'production_database_access': False, 'live_model_calls': 0}
    (ROOT / 'research-display-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
