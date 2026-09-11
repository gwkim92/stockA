"""Bounded, read-only incident evidence from the verified personal stockA host."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import urllib.request


def command(argv, *, timeout=12, limit=12000):
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return {"exit_code": result.returncode, "stdout": result.stdout[-limit:], "stderr": result.stderr[-2000:]}
    except subprocess.TimeoutExpired:
        return {"timed_out": True}


def main():
    req = urllib.request.Request("http://169.254.169.254/latest/api/token", method="PUT",
        headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"})
    with urllib.request.urlopen(req, timeout=3) as response:
        token = response.read().decode()
    req = urllib.request.Request("http://169.254.169.254/latest/dynamic/instance-identity/document",
        headers={"X-aws-ec2-metadata-token": token})
    with urllib.request.urlopen(req, timeout=3) as response:
        identity = json.load(response)
    assert (identity["accountId"], identity["instanceId"], identity["region"]) == (
        "115623963546", "i-029d51b163fb07b61", "us-east-1")
    report = {"observed_at": datetime.now(timezone.utc).isoformat(),
        "identity": {key: identity[key] for key in ("accountId", "instanceId", "region", "instanceType")}}
    commands = {
        "uptime": ["uptime"],
        "memory": ["free", "-m"],
        "disk": ["df", "-h", "/", "/opt/stockanalysis"],
        "inodes": ["df", "-i", "/"],
        "vmstat": ["vmstat", "1", "3"],
        "boot_history": ["journalctl", "--list-boots", "--no-pager"],
        "active_profiles": ["systemctl", "list-units", "--type=service", "--state=running,activating", "--plain", "--no-legend", "stockanalysis-operating-data-*"],
        "timers": ["systemctl", "list-timers", "--all", "--no-pager", "stockanalysis-*"],
        "services": ["systemctl", "show", "stockanalysis-frontend-api.service", "stockanalysis-web.service", "stockanalysis-web-public-13000.service", "--property=Id,ActiveState,SubState,Result,MemoryCurrent,MemoryPeak,MemoryMax,MemoryHigh,TasksCurrent,TasksMax,CPUUsageNSec,CPUQuotaPerSecUSec,TimeoutStartUSec"],
        "database_usage": ["docker", "stats", "--no-stream", "--format", "{{.Name}} {{.MemUsage}} {{.CPUPerc}} {{.PIDs}}", "stockanalysis-postgres"],
        "running_commit": ["git", "-C", "/opt/stockanalysis/app", "rev-parse", "HEAD"],
    }
    for key, argv in commands.items():
        report[key] = command(argv)
    processes = command(["ps", "-eo", "pid,ppid,comm,rss,pcpu,stat", "--sort=-rss"])
    processes["stdout"] = "\n".join(processes.get("stdout", "").splitlines()[:20])
    report["largest_processes"] = processes
    for kind in ("memory", "cpu", "io"):
        file = Path("/proc/pressure") / kind
        if file.exists():
            report["pressure_" + kind] = file.read_text()
    for boot in ("0", "-1"):
        logs = command(["sudo", "-n", "journalctl", "-k", "-b", boot, "--no-pager", "--grep",
            "[Oo]ut of memory|[Oo][Oo][Mm]|Killed process|blocked for more than|I/O error|No space left|soft lockup"], limit=16000)
        report["kernel_boot_" + boot] = logs
    build = Path("/opt/stockanalysis/runtime/research-automation-20260911/build.log")
    report["build_log_present"] = build.exists()
    if build.exists():
        report["build_log_bytes"] = build.stat().st_size
        # Never dump arbitrary subprocess logs or environment contents.
        tail = command(["tail", "-n", "80", str(build)])
        report["build_markers"] = [line[:400] for line in tail.get("stdout", "").splitlines()
            if re.search(r"Next.js|Compil|Generating|Collecting|TypeScript|Killed|ENOMEM|heap|Error|error", line)]
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
