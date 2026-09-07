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
    mocked_probes: list[str] = []

    def denied(*args, **kwargs):
        # Report call sites, not commands/arguments that may contain source data.
        frames = traceback.extract_stack()[:-1]
        sites = [f'{Path(f.filename).name}:{f.lineno}:{f.name}' for f in frames if '/stockA/' in f.filename][-8:]
        attempts.append({'kind': 'external_io', 'sites': sites})
        raise RuntimeError('External IO forbidden in research display regression')

    def synthetic_login_probe(command, input_text, timeout_seconds, cwd):
        # Existing registry tests cover billing/cache fields and also probe CLI
        # login status. Stub that narrow process boundary; never run local auth.
        from stockanalysis.frontend.codex_oauth_operator import CommandResult
        if list(command) != ['codex', 'login', 'status'] or input_text is not None:
            return denied()
        mocked_probes.append('codex_login_status')
        return CommandResult(returncode=1, stdout='', stderr='Not logged in (synthetic test probe)')

    with ExitStack() as guards:
        for target in ('socket.socket.connect', 'socket.create_connection', 'subprocess.Popen'):
            guards.enter_context(patch(target, side_effect=denied))
        guards.enter_context(patch('stockanalysis.frontend.codex_oauth_operator._subprocess_runner', side_effect=synthetic_login_probe))
        suite = unittest.defaultTestLoader.loadTestsFromNames(SUITES)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = result.wasSuccessful() and not result.skipped and not attempts
    report = {'verification': 'research-display-contract-v1', 'suites': SUITES,
              'tests_run': result.testsRun, 'failures': len(result.failures),
              'errors': len(result.errors), 'skipped': len(result.skipped),
              'unexpected_io_attempts': len(attempts), 'io_call_sites': attempts,
              'mocked_login_status_probes': len(mocked_probes), 'passed': passed,
              'production_database_access': False, 'live_model_calls': 0}
    (ROOT / 'research-display-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
