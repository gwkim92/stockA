"""Resume only the observed post-swap, pre-timer checkpoint; never rebuild/re-pull."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import urllib.request

BASE = Path('/opt/stockanalysis/runtime/research-automation-20260911')
APP = Path('/opt/stockanalysis/app')
EXPECTED = '502eb6795dbcd328ea5a9b6bc6aa503be0061408'
SERVICES = ['stockanalysis-frontend-api.service', 'stockanalysis-web.service', 'stockanalysis-web-public-13000.service']


def capture(args):
    return subprocess.check_output(args, text=True, timeout=30).strip()


def main():
    spec = importlib.util.spec_from_file_location('activation', '/tmp/stocka-research-activate-guarded.py')
    activation = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(activation)
    identity = activation.identity()
    assert not (BASE / 'activation.json').exists()
    checkpoint = json.loads((BASE / 'started.json').read_text())
    assert checkpoint['expected'] == EXPECTED
    assert capture(['git', '-C', str(APP), 'rev-parse', 'HEAD']) == EXPECTED
    assert capture(['git', '-C', str(APP), 'branch', '--show-current']) == 'develop'
    assert not capture(['git', '-C', str(APP), 'status', '--porcelain', '--untracked-files=no'])
    manifest = json.loads((BASE / 'linux-build-manifest.json').read_text())
    build_id = (APP / 'apps/web/.next/BUILD_ID').read_text().strip()
    assert build_id == manifest['build_id']
    assert capture(['git', '-C', str(APP), 'rev-parse', EXPECTED + ':apps/web']) == manifest['web_tree']
    assert (BASE / 'previous-next/BUILD_ID').is_file()
    for filename, digest in checkpoint['settings_hashes'].items():
        assert hashlib.sha256((BASE.parent / filename).read_bytes()).hexdigest() == digest
    plan = json.loads((BASE / 'manifest-plan.json').read_text())
    files = [Path(row['path']) for row in plan['profiles'][0]['manifest_file_previews']
             if row['kind'] in ('systemd_service', 'systemd_timer')]
    assert {p.name for p in files} == {'stockanalysis-operating-data-research-maintenance.service',
                                     'stockanalysis-operating-data-research-maintenance.timer'}
    for source in files:
        assert source.parent == BASE / 'manifests'
        subprocess.run(['sudo', '-n', 'install', '-m', '644', str(source), '/etc/systemd/system/' + source.name], check=True)
    subprocess.run(['sudo', '-n', 'systemctl', 'daemon-reload'], check=True)
    subprocess.run(['sudo', '-n', 'systemctl', 'enable', '--now', 'stockanalysis-operating-data-research-maintenance.timer'], check=True)
    for service in SERVICES:
        assert capture(['systemctl', 'is-active', service]) == 'active'
    for timer in checkpoint['timers']:
        assert capture(['systemctl', 'is-active', timer]) == 'active'
    for port, path in ((8787, '/__ready'), (3000, '/data-health'), (13000, '/data-health')):
        with urllib.request.urlopen(f'http://127.0.0.1:{port}{path}', timeout=30) as response:
            assert response.status == 200
    result = {'identity': identity, 'previous_commit': checkpoint['previous'], 'commit': EXPECTED,
              'build_id': build_id, 'services_active': True, 'routes_200': True,
              'settings_unchanged': True, 'schema_changed': False, 'previous_timers_restored': True,
              'new_timer_active': capture(['systemctl', 'is-active', 'stockanalysis-operating-data-research-maintenance.timer']) == 'active',
              'resumed_stage': 'install_generated_systemd_files_only',
              'activated_at': datetime.now(timezone.utc).isoformat()}
    (BASE / 'activation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
