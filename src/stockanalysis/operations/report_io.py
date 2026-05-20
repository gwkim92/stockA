from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, TextIO


def load_json_object(path: str | Path, *, label: str) -> dict[str, object]:
    resolved_path = Path(path)
    payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object.")
    return payload


def write_json_report(
    report: dict[str, object],
    *,
    output_path: str | Path | None = None,
    stdout: TextIO | None = None,
) -> None:
    stream = stdout or sys.stdout
    text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if output_path is None:
        stream.write(text)
        return

    path = Path(output_path)
    path.write_text(text, encoding="utf-8")
    stream.write(str(path) + "\n")


def print_json(payload: dict[str, Any], *, stdout: TextIO | None = None, sort_keys: bool = True) -> None:
    stream = stdout or sys.stdout
    stream.write(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=sort_keys) + "\n")
