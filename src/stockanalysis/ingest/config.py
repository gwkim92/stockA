from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


class ConfigError(RuntimeError):
    """Raised when runtime configuration is invalid or incomplete."""


@dataclass(frozen=True)
class RuntimeConfig:
    sec_user_agent: str | None = None
    fred_api_key: str | None = None
    alpha_vantage_api_key: str | None = None
    twelve_data_api_key: str | None = None
    tossinvest_client_id: str | None = None
    tossinvest_client_secret: str | None = None
    tossinvest_account_seq: str | None = None
    database_url: str | None = None
    psql_command: str | None = None

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        return cls.from_mapping(os.environ)

    @classmethod
    def from_mapping(cls, env: Mapping[str, str]) -> "RuntimeConfig":
        return cls(
            sec_user_agent=_read_optional_from(env, "STOCKANALYSIS_SEC_USER_AGENT"),
            fred_api_key=_read_optional_from(env, "STOCKANALYSIS_FRED_API_KEY"),
            alpha_vantage_api_key=_read_optional_from(env, "STOCKANALYSIS_ALPHA_VANTAGE_API_KEY"),
            twelve_data_api_key=_read_optional_from(env, "STOCKANALYSIS_TWELVE_DATA_API_KEY"),
            tossinvest_client_id=_read_optional_from(env, "STOCKANALYSIS_TOSSINVEST_CLIENT_ID"),
            tossinvest_client_secret=_read_optional_from(env, "STOCKANALYSIS_TOSSINVEST_CLIENT_SECRET"),
            tossinvest_account_seq=_read_optional_from(env, "STOCKANALYSIS_TOSSINVEST_ACCOUNT_SEQ"),
            database_url=_read_optional_from(env, "STOCKANALYSIS_DATABASE_URL"),
            psql_command=_read_optional_from(env, "STOCKANALYSIS_PSQL_COMMAND"),
        )

    def resolve(self, env_name: str, *, required: bool) -> str:
        value = getattr(self, _ENV_TO_FIELD[env_name])
        if value:
            return value
        if required:
            raise ConfigError(f"Missing required environment variable: {env_name}")
        return f"<env:{env_name}>"


def _read_optional(name: str) -> str | None:
    return _read_optional_from(os.environ, name)


def _read_optional_from(env: Mapping[str, str], name: str) -> str | None:
    value = env.get(name)
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


_ENV_TO_FIELD = {
    "STOCKANALYSIS_SEC_USER_AGENT": "sec_user_agent",
    "STOCKANALYSIS_FRED_API_KEY": "fred_api_key",
    "STOCKANALYSIS_ALPHA_VANTAGE_API_KEY": "alpha_vantage_api_key",
    "STOCKANALYSIS_TWELVE_DATA_API_KEY": "twelve_data_api_key",
    "STOCKANALYSIS_TOSSINVEST_CLIENT_ID": "tossinvest_client_id",
    "STOCKANALYSIS_TOSSINVEST_CLIENT_SECRET": "tossinvest_client_secret",
    "STOCKANALYSIS_TOSSINVEST_ACCOUNT_SEQ": "tossinvest_account_seq",
    "STOCKANALYSIS_DATABASE_URL": "database_url",
    "STOCKANALYSIS_PSQL_COMMAND": "psql_command",
}
