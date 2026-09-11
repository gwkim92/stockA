"""Reuse verified off-host activation with a task-specific checkpoint directory."""
import importlib.util
from pathlib import Path
import subprocess
import time


def capture(argv):
    # Stopping a timer does not stop its already-started status collector. Allow
    # that short overlap to settle; a longer-running batch still blocks activation.
    deadline = time.monotonic() + 30
    while True:
        output = subprocess.check_output(argv, text=True, timeout=180).strip()
        if (not output or argv[:2] != ['systemctl', 'list-units']
            or '--state=running,activating' not in argv or time.monotonic() >= deadline):
            return output
        time.sleep(0.5)


if __name__ == '__main__':
    path = Path('/opt/stockanalysis/app/docs/tasks/research-automation-20260911/activate.py')
    spec = importlib.util.spec_from_file_location('activation', path)
    activation = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(activation)
    activation.BASE = Path('/opt/stockanalysis/runtime/research-source-refresh-20260911')
    activation.capture = capture
    activation.run = lambda argv, **kwargs: subprocess.run(argv, check=True, timeout=180, **kwargs)
    activation.main()
