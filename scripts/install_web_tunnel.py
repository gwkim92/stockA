#!/usr/bin/env python3
"""Install the user's reconnecting macOS SSH tunnel; never edit AWS rules."""
import os
from pathlib import Path
import plistlib
import subprocess

LABEL = 'im.stocka.web-tunnel'

if __name__ == '__main__':
    home = Path.home()
    source_key = home / 'Downloads/settle.pem'
    if not source_key.is_file():
        raise SystemExit('The stockA SSH key is missing.')
    # launchd cannot read macOS-protected Downloads even when the interactive
    # terminal can. Keep an owner-only copy in the SSH configuration directory.
    key = home / '.ssh/stocka-web.pem'
    if key.exists() and key.read_bytes() != source_key.read_bytes():
        raise SystemExit('Existing stockA tunnel key differs; refusing to overwrite.')
    if not key.exists():
        fd = os.open(key, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(source_key.read_bytes())
    domain = f'gui/{os.getuid()}'
    target = f'{domain}/{LABEL}'
    plist = home / 'Library/LaunchAgents' / f'{LABEL}.plist'
    logs = home / 'Library/Logs/stockA'
    logs.mkdir(parents=True, exist_ok=True)
    plist.parent.mkdir(parents=True, exist_ok=True)
    args = ['/usr/bin/ssh', '-NT', '-i', str(key), '-o', 'IdentitiesOnly=yes',
        '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
        '-o', 'ConnectTimeout=10', '-o', 'ServerAliveInterval=30',
        '-o', 'ServerAliveCountMax=3', '-o', 'ExitOnForwardFailure=yes',
        '-L', '127.0.0.1:13309:127.0.0.1:3000', 'ec2-user@3.211.40.142']
    payload = {'Label': LABEL, 'ProgramArguments': args, 'RunAtLoad': True,
        'KeepAlive': True, 'ThrottleInterval': 30,
        'StandardErrorPath': str(logs / 'web-tunnel.log')}
    encoded = plistlib.dumps(payload)
    loaded = subprocess.run(['launchctl', 'print', target], capture_output=True).returncode == 0
    if loaded and plist.exists() and plist.read_bytes() == encoded:
        print('Tunnel already installed: http://127.0.0.1:13309')
        raise SystemExit(0)
    if loaded:
        subprocess.run(['launchctl', 'bootout', target], check=True)
    temporary = plist.with_suffix('.tmp')
    temporary.write_bytes(encoded)
    temporary.chmod(0o600)
    temporary.replace(plist)
    subprocess.run(['launchctl', 'bootstrap', domain, str(plist)], check=True)
    print('Tunnel installed: http://127.0.0.1:13309 (reconnects; starts at login)')
