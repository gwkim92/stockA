from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    """Raised when runtime configuration is invalid or incomplete."""


@dataclass(frozen=True)
class RuntimeConfig:
    sec_user_agent: str | None = None
    fred_api_key: str | None = None
    alpha_vantage_api_key: str | None = None
    twelve_data_api_key: str | None = None
    database_url: str | None = None
    psql_command: str | None = None

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        return cls(
            sec_user_agent=_read_optional("STOCKANALYSIS_SEC_USER_AGENT"),
            fred_api_key=_read_optional("STOCKANALYSIS_FRED_API_KEY"),
            alpha_vantage_api_key=_read_optional("STOCKANALYSIS_ALPHA_VANTAGE_API_KEY"),
            twelve_data_api_key=_read_optional("STOCKANALYSIS_TWELVE_DATA_API_KEY"),
            database_url=_read_optional("STOCKANALYSIS_DATABASE_URL"),
            psql_command=_read_optional("STOCKANALYSIS_PSQL_COMMAND"),
        )

    def resolve(self, env_name: str, *, required: bool) -> str:
        value = getattr(self, _ENV_TO_FIELD[env_name])
        if value:
            return value
        if required:
            raise ConfigError(f"Missing required environment variable: {env_name}")
        return f"<env:{env_name}>"


def _read_optional(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


_ENV_TO_FIELD = {
    "STOCKANALYSIS_SEC_USER_AGENT": "sec_user_agent",
    "STOCKANALYSIS_FRED_API_KEY": "fred_api_key",
    "STOCKANALYSIS_ALPHA_VANTAGE_API_KEY": "alpha_vantage_api_key",
    "STOCKANALYSIS_TWELVE_DATA_API_KEY": "twelve_data_api_key",
    "STOCKANALYSIS_DATABASE_URL": "database_url",
    "STOCKANALYSIS_PSQL_COMMAND": "psql_command",
}
