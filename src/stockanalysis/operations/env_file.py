from __future__ import annotations

import os
import shlex
from pathlib import Path
from typing import Mapping


def load_env_file_values(env_file: str | Path) -> dict[str, str]:
    path = Path(env_file)
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            tokens = shlex.split(line, comments=True, posix=True)
        except ValueError as exc:
            raise ValueError(f"Invalid env file syntax at line {line_number}: {path}") from exc
        if not tokens:
            continue
        if tokens[0] == "export":
            tokens = tokens[1:]
        if len(tokens) != 1 or "=" not in tokens[0]:
            raise ValueError(f"Invalid env assignment at line {line_number}: {path}")
        key, value = tokens[0].split("=", 1)
        key = key.strip()
        if not key or not _is_valid_env_name(key):
            raise ValueError(f"Invalid env name at line {line_number}: {path}")
        values[key] = value
    return values


def merged_env_with_file(
    env_file: str | Path,
    *,
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    merged = dict(base_env if base_env is not None else os.environ)
    merged.update(load_env_file_values(env_file))
    return merged


def _is_valid_env_name(value: str) -> bool:
    if not (value[0].isalpha() or value[0] == "_"):
        return False
    return all(char.isalnum() or char == "_" for char in value)
