"""Bounded batch policy, atomic progress and read-only systemd observations."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import time
from datetime import datetime, timezone
from typing import Callable, Mapping
from uuid import uuid4

SLICE_NAME = "stockanalysis-batch.slice"
SLICE_CONTENTS = """[Unit]
Description=Stockanalysis batch resource budget

[Slice]
CPUAccounting=yes
MemoryAccounting=yes
CPUQuota=100%
CPUWeight=25
IOWeight=25
MemoryHigh=1536M
MemoryMax=2048M
MemorySwapMax=0
TasksMax=512
"""


def service_guard_lines(profile_id: str) -> str:
    deadline = 900 if profile_id == "research-maintenance" else (
        14400 if profile_id in {"decision-daily", "sec-filings-weekly", "full-recovery"} else 7200)
    return (f"Slice={SLICE_NAME}\nMemoryAccounting=yes\nCPUAccounting=yes\n"
            "MemoryHigh=768M\nMemoryMax=1024M\nTasksMax=256\nCPUWeight=25\nIOWeight=25\n"
            f"TimeoutStartSec={deadline}\nTimeoutStopSec=30\nKillMode=control-group\nOOMPolicy=kill\nNice=10\n")


def atomic_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False)
            handle.write("\n")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def boot_id() -> str:
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    except OSError:
        return "unavailable"


class BatchProgress:
    def __init__(self, runtime_root: Path, profile: str, timeout_seconds: int):
        if not re.fullmatch(r"[a-z0-9-]+", profile):
            raise ValueError("Invalid batch profile")
        self.path = runtime_root / "batch-progress" / (profile + ".json")
        self.data: dict[str, object] = {"profile": profile, "run_id": uuid4().hex, "pid": os.getpid(),
            "boot_id": boot_id(), "started_monotonic": time.monotonic(), "completed_steps": 0,
            "timeout_seconds": timeout_seconds}
        self.step("preparing")

    def step(self, step_id: str) -> None:
        self.data.update(status="running", step_id=step_id, step_started_monotonic=time.monotonic(),
                         updated_at=datetime.now(timezone.utc).isoformat())
        atomic_json(self.path, self.data)

    def completed_step(self) -> None:
        self.data["completed_steps"] = int(self.data["completed_steps"]) + 1
        self.data["updated_at"] = datetime.now(timezone.utc).isoformat()
        atomic_json(self.path, self.data)

    def finish(self, status: str) -> None:
        self.data.update(status=status, updated_at=datetime.now(timezone.utc).isoformat())
        atomic_json(self.path, self.data)


def run_profile_with_progress(run: Callable, **kwargs):
    if not kwargs.get("execute"):
        return run(**kwargs)
    from stockanalysis.operations.path_policy import ensure_repo_outside
    root = ensure_repo_outside(Path(kwargs["runtime_root"]).expanduser().resolve(),
                               repo_root=kwargs.get("repo_root"), label="batch runtime root")
    progress = BatchProgress(root, kwargs["profile"], kwargs["timeout_seconds"])
    try:
        report = run(**kwargs, _progress=progress)
        progress.finish("succeeded" if report["run_status"] == "completed" else "failed")
        return report
    except BaseException:
        progress.finish("interrupted")
        raise


UNIT_PROPERTIES = ("LoadState,ActiveState,SubState,Result,Slice,MemoryHigh,MemoryMax,MemoryCurrent,"
                   "CPUUsageNSec,TimeoutStartUSec,InactiveExitTimestampMonotonic")


def observe_profile(properties: str, progress_path: Path | None, *, now: float | None = None,
                    current_boot_id: str | None = None) -> dict[str, object]:
    props = dict(line.split("=", 1) for line in properties.splitlines() if "=" in line)
    current = time.monotonic() if now is None else now
    current_boot = boot_id() if current_boot_id is None else current_boot_id
    def number(key):
        value = props.get(key, "")
        return int(value) if value.isdecimal() else None
    memory_max = number("MemoryMax")
    # systemctl formats durations as e.g. "15min" or "2h", not just integers.
    timeout = props.get("TimeoutStartUSec", "")
    protected = (props.get("Slice") == SLICE_NAME and memory_max is not None
                 and 0 < memory_max <= 1024 ** 3 and timeout not in {"", "infinity"})
    result: dict[str, object] = {"status": "not_run", "resource_limits_applied": protected,
        "memory_current_bytes": number("MemoryCurrent"), "memory_max_bytes": memory_max,
        "step_id": "", "step_elapsed_seconds": None, "completed_steps": 0,
        "attention_required": False}
    active = props.get("ActiveState") in {"active", "activating", "deactivating"}
    failed = props.get("Result", "") not in {"", "success"}
    progress = None
    if progress_path is not None and progress_path.exists():
        try:
            with progress_path.open("rb") as handle:
                raw = handle.read(16385)
            if len(raw) > 16384:
                raise ValueError("Oversize progress")
            progress = json.loads(raw)
            if not isinstance(progress, dict):
                raise ValueError("Invalid progress")
            if not isinstance(progress.get("status"), str):
                raise ValueError("Invalid progress status")
            for key in ("started_monotonic", "step_started_monotonic", "timeout_seconds", "completed_steps"):
                if not isinstance(progress.get(key), (float, int)) or not 0 <= progress[key] < 1e12:
                    raise ValueError("Invalid progress number")
        except (OSError, ValueError, TypeError):
            result.update(status="invalid_progress", attention_required=True)
            return result
    activation = (number("InactiveExitTimestampMonotonic") or 0) / 1_000_000
    belongs_to_current_run = (progress is not None and progress.get("boot_id") == current_boot
                             and progress["started_monotonic"] >= activation - 1)
    if active and not belongs_to_current_run:
        result["status"] = "awaiting_progress" if activation and current - activation <= 120 else "progress_missing"
    elif active and progress:
        elapsed = max(0, current - progress["step_started_monotonic"])
        result.update(status="stalled" if elapsed > progress["timeout_seconds"] + 30 else "running",
                      step_id=re.sub(r"[^a-zA-Z0-9_-]", "", str(progress.get("step_id", "")))[:100],
                      step_elapsed_seconds=round(elapsed), completed_steps=int(progress["completed_steps"]))
    elif failed:
        result["status"] = "unit_failed"
    elif progress:
        result["status"] = progress.get("status") if progress.get("status") in {"succeeded", "failed", "interrupted"} else "interrupted"
        result["completed_steps"] = int(progress["completed_steps"])
    elif props.get("LoadState") == "not-found":
        result["status"] = "not_installed"
    result["attention_required"] = result["status"] in {"stalled", "progress_missing", "unit_failed", "failed", "interrupted"}
    return result


def public_observation(value: object) -> dict[str, object]:
    """Whitelist only typed guard fields from a local status artifact."""
    if not isinstance(value, Mapping):
        return {}
    statuses = {"not_run", "not_installed", "awaiting_progress", "progress_missing", "running",
                "stalled", "unit_failed", "failed", "interrupted", "succeeded", "invalid_progress"}
    status = value.get("status")
    result = {"status": status if isinstance(status, str) and status in statuses else "invalid_progress"}
    for key in ("resource_limits_applied", "attention_required"):
        result[key] = value.get(key) is True
    for key in ("memory_current_bytes", "memory_max_bytes", "step_elapsed_seconds", "completed_steps"):
        number = value.get(key)
        result[key] = number if isinstance(number, int) and not isinstance(number, bool) and 0 <= number < 10**15 else None
    result["step_id"] = re.sub(r"[^a-zA-Z0-9_-]", "", str(value.get("step_id", "")))[:100]
    return result
