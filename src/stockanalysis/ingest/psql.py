from __future__ import annotations

import shlex
import subprocess

from stockanalysis.ingest.config import ConfigError, RuntimeConfig


class PsqlExecutionError(RuntimeError):
    """Raised when a psql command fails or returns invalid output."""


class PsqlCommandExecutor:
    def __init__(self, base_command: list[str]) -> None:
        if not base_command:
            raise ValueError("psql base command must not be empty")
        self._base_command = list(base_command)

    @classmethod
    def from_config(cls, config: RuntimeConfig) -> "PsqlCommandExecutor":
        command_text = config.resolve("STOCKANALYSIS_PSQL_COMMAND", required=True)
        try:
            argv = shlex.split(command_text)
        except ValueError as exc:
            raise ConfigError("Invalid STOCKANALYSIS_PSQL_COMMAND value") from exc
        return cls(argv)

    def execute_scalar(self, sql: str) -> str:
        completed = self._run(sql)
        output = completed.stdout.strip()
        if not output:
            raise PsqlExecutionError("psql returned no rows for scalar query")
        return output.splitlines()[-1].strip()

    def execute_non_query(self, sql: str) -> None:
        self._run(sql)

    def _run(self, sql: str) -> subprocess.CompletedProcess[str]:
        command = [*self._base_command, "-v", "ON_ERROR_STOP=1", "-X", "-q", "-t", "-A"]
        completed = subprocess.run(
            command,
            input=sql,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.strip() or completed.stdout.strip() or "psql command failed"
            raise PsqlExecutionError(stderr)
        return completed
