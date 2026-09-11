"""Deploy an exact, CI-verified develop revision and reversible resource drop-ins."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import urllib.request

APP = Path('/opt/stockanalysis/app')
RUNTIME = Path('/opt/stockanalysis/runtime')
BASE = RUNTIME / 'batch-guard-20260911'
PYTHON = '/opt/stockanalysis/venv/bin/python'
STATUS = 'stockanalysis-operating-data-scheduler-status'


def capture(argv):
    return subprocess.check_output(argv, text=True, timeout=60).strip()


def run(argv):
    subprocess.run(argv, check=True, timeout=120)


def save(name, value):
    (BASE / name).write_text(json.dumps(value, indent=2) + '\n')


def identity():
    request = urllib.request.Request('http://169.254.169.254/latest/api/token', method='PUT',
        headers={'X-aws-ec2-metadata-token-ttl-seconds': '60'})
    with urllib.request.urlopen(request, timeout=3) as response:
        token = response.read().decode()
    request = urllib.request.Request('http://169.254.169.254/latest/dynamic/instance-identity/document',
        headers={'X-aws-ec2-metadata-token': token})
    with urllib.request.urlopen(request, timeout=3) as response:
        data = json.load(response)
    assert (data['accountId'], data['instanceId'], data['instanceType']) == ('115623963546', 'i-029d51b163fb07b61', 't3.large')
    return {key: data[key] for key in ('accountId', 'instanceId', 'instanceType', 'region')}


def main():
    expected = sys.argv[1]
    assert len(expected) == 40 and all(c in '0123456789abcdef' for c in expected)
    ident = identity()
    BASE.mkdir(mode=0o700, exist_ok=True)
    assert not (BASE / 'started.json').exists(), 'Inspect checkpoint; never blindly replay deployment'
    assert capture(['git', '-C', str(APP), 'branch', '--show-current']) == 'develop'
    assert not capture(['git', '-C', str(APP), 'status', '--porcelain', '--untracked-files=no'])
    previous = capture(['git', '-C', str(APP), 'rev-parse', 'HEAD'])
    run(['git', '-C', str(APP), 'fetch', 'origin', 'develop'])
    assert capture(['git', '-C', str(APP), 'rev-parse', 'FETCH_HEAD']) == expected
    run(['git', '-C', str(APP), 'merge-base', '--is-ancestor', previous, expected])
    run(['git', '-C', str(APP), 'diff', '--exit-code', previous, expected, '--', 'apps/web', 'db/migrations', 'pyproject.toml'])
    build_id = (APP / 'apps/web/.next/BUILD_ID').read_text().strip()
    settings = {name: hashlib.sha256((RUNTIME / name).read_bytes()).hexdigest()
                for name in ('data-operations.env', 'frontend-api.env', 'web.env', 'ai-model-settings.sqlite3')}
    timers = [row.split()[0] for row in capture(['systemctl', 'list-units', '--type=timer', '--state=active',
                                               '--plain', '--no-legend', 'stockanalysis-*']).splitlines()]
    services = [name[:-6] + '.service' for name in timers if name != STATUS + '.timer']
    assert len(services) == 13 and all(name.startswith('stockanalysis-operating-data-') for name in services)
    container = json.loads(capture(['docker', 'inspect', 'stockanalysis-postgres']))[0]
    assert container['Name'] == '/stockanalysis-postgres' and container['State']['Running']
    pid = container['State']['Pid']
    cgroup = next(line.split('::', 1)[1] for line in Path(f'/proc/{pid}/cgroup').read_text().splitlines() if line.startswith('0::'))
    database_bytes = int((Path('/sys/fs/cgroup') / cgroup.lstrip('/') / 'memory.current').read_text())
    assert database_bytes < 2 * 1024**3, 'DB usage too close to proposed 3GiB cap'
    host = container['HostConfig']
    db_limits = {key: host[key] for key in ('Memory', 'MemorySwap', 'MemoryReservation')}
    assert db_limits == {'Memory': 0, 'MemorySwap': 0, 'MemoryReservation': 0}, 'Unexpected prior DB policy'
    save('started.json', {'identity': ident, 'previous': previous, 'expected': expected, 'timers': timers,
                         'services': services, 'build_id': build_id, 'settings_hashes': settings,
                         'database_id': container['Id'], 'database_previous_limits': db_limits,
                         'database_memory_before': database_bytes})
    run(['git', '-C', str(APP), 'archive', '--format=tar.gz', '--output=' + str(BASE / 'previous-source.tar.gz'), previous])
    backup = {}
    def install(path, content):
        destination = Path(path)
        backup[path] = destination.read_text() if destination.exists() else None
        save('unit-backup.json', backup)
        source = BASE / ('install-' + str(len(backup)))
        source.write_text(content)
        run(['sudo', '-n', 'mkdir', '-p', str(destination.parent)])
        run(['sudo', '-n', 'install', '-m', '644', str(source), path])
    try:
        run(['sudo', '-n', 'systemctl', 'stop', *timers])
        assert not capture(['systemctl', 'list-units', '--type=service', '--state=running,activating',
                            '--plain', '--no-legend', 'stockanalysis-operating-data-*']), 'Wait for active batch; do not interrupt it'
        run(['git', '-C', str(APP), 'pull', '--ff-only', 'origin', 'develop'])
        assert capture(['git', '-C', str(APP), 'rev-parse', 'HEAD']) == expected
        sys.path.insert(0, str(APP / 'src'))
        from stockanalysis.operations.batch_runtime import SLICE_NAME, SLICE_CONTENTS, service_guard_lines
        install('/etc/systemd/system/' + SLICE_NAME, SLICE_CONTENTS)
        for service in services:
            profile = service.removeprefix('stockanalysis-operating-data-').removesuffix('.service')
            install('/etc/systemd/system/' + service + '.d/60-batch-guard.conf', '[Service]\n' + service_guard_lines(profile))
        install('/etc/systemd/system/' + STATUS + '.service.d/60-batch-guard.conf',
            '[Service]\nExecStart=\nExecStart=' + PYTHON + ' -m stockanalysis.operations.cli operating-data-profile-scheduler-status-report'
            ' --repo-root ' + str(APP) + ' --runtime-root ' + str(RUNTIME) + ' --job-name stockanalysis-operating-data'
            ' --output ' + str(RUNTIME / 'operating-data-profile-scheduler-status.json') + '\n'
            'MemoryMax=128M\nCPUQuota=20%\nTimeoutStartSec=60\nTimeoutStopSec=15\n')
        install('/etc/systemd/system/' + STATUS + '.timer.d/60-batch-guard.conf',
                '[Timer]\nOnUnitActiveSec=\nOnUnitActiveSec=1min\nAccuracySec=15s\n')
        run(['sudo', '-n', 'systemd-analyze', 'verify', SLICE_NAME, *services, STATUS + '.service', STATUS + '.timer'])
        # Docker stores these limits in the container config; ordinary restarts preserve them.
        # A future container recreation must carry the same memory flags.
        run(['docker', 'update', '--memory', '3g', '--memory-swap', '3g', container['Id']])
        run(['sudo', '-n', 'systemctl', 'daemon-reload'])
        run(['sudo', '-n', 'systemctl', 'start', SLICE_NAME])
        run(['sudo', '-n', 'systemctl', 'restart', 'stockanalysis-frontend-api.service'])
    except BaseException:
        save('attention.json', {'inspect_before_replay': True, 'previous': previous, 'expected': expected})
        raise
    finally:
        run(['sudo', '-n', 'systemctl', 'start', *timers])
    run(['sudo', '-n', 'systemctl', 'start', STATUS + '.service'])
    for name, digest in settings.items():
        assert hashlib.sha256((RUNTIME / name).read_bytes()).hexdigest() == digest
    assert build_id == (APP / 'apps/web/.next/BUILD_ID').read_text().strip()
    for timer in timers:
        assert capture(['systemctl', 'is-active', timer]) == 'active'
    for port, path in ((8787, '/__ready'), (3000, '/data-health'), (13000, '/data-health')):
        with urllib.request.urlopen(f'http://127.0.0.1:{port}{path}', timeout=30) as response:
            assert response.status == 200
    save('activation.json', {'identity': ident, 'commit': expected, 'previous': previous, 'build_id_unchanged': build_id,
         'settings_unchanged': True, 'routes_200': True, 'restored_timer_count': len(timers),
         'protected_service_count': len(services), 'database_memory_limit': 3 * 1024**3,
         'activated_at': datetime.now(timezone.utc).isoformat()})
    print((BASE / 'activation.json').read_text())


if __name__ == '__main__':
    main()
