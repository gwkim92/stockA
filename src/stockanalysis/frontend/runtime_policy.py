from __future__ import annotations

import hmac
import os
from dataclasses import dataclass


PROFILE_CHOICES = ("local", "production")
AUTH_MODE_CHOICES = ("disabled", "read-token")
DEFAULT_ALLOWED_ORIGIN = "*"
DEFAULT_READ_TOKEN_ENV = "STOCKANALYSIS_FRONTEND_API_READ_TOKEN"
PRODUCTION_DB_ENV = "STOCKANALYSIS_PSQL_COMMAND"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
SOURCE_CHOICES = ("fixture", "live", "auto")


@dataclass(frozen=True)
class FrontendRuntimePolicy:
    profile: str = "local"
    source: str = "fixture"
    allowed_origin: str = DEFAULT_ALLOWED_ORIGIN
    auth_mode: str = "disabled"
    read_token_env: str = DEFAULT_READ_TOKEN_ENV
    read_token: str | None = None
    psql_command: str | None = None

    @classmethod
    def from_env(
        cls,
        *,
        source: str,
        profile: str | None = None,
        allowed_origin: str | None = None,
        auth_mode: str | None = None,
        read_token_env: str = DEFAULT_READ_TOKEN_ENV,
    ) -> "FrontendRuntimePolicy":
        selected_profile = profile or os.environ.get("STOCKANALYSIS_FRONTEND_RUNTIME_PROFILE") or "local"
        selected_origin = allowed_origin or os.environ.get("STOCKANALYSIS_FRONTEND_API_ALLOWED_ORIGIN") or DEFAULT_ALLOWED_ORIGIN
        selected_auth_mode = auth_mode or os.environ.get("STOCKANALYSIS_FRONTEND_API_AUTH_MODE") or "disabled"
        return cls(
            profile=selected_profile,
            source=source,
            allowed_origin=selected_origin,
            auth_mode=selected_auth_mode,
            read_token_env=read_token_env,
            read_token=os.environ.get(read_token_env) or None,
            psql_command=os.environ.get(PRODUCTION_DB_ENV) or None,
        )

    @property
    def requires_auth(self) -> bool:
        return self.auth_mode == "read-token"

    @property
    def exposes_detailed_errors(self) -> bool:
        return self.profile == "local"

    def validate_for_startup(self, *, host: str) -> None:
        issues = self.validation_issues(host=host)
        if issues:
            raise ValueError("Invalid frontend runtime policy: " + "; ".join(issues))

    def validation_issues(self, *, host: str) -> list[str]:
        issues: list[str] = []
        if self.profile not in PROFILE_CHOICES:
            issues.append(f"runtime profile must be one of {PROFILE_CHOICES}")
        if self.source not in SOURCE_CHOICES:
            issues.append(f"source must be one of {SOURCE_CHOICES}")
        if self.auth_mode not in AUTH_MODE_CHOICES:
            issues.append(f"auth mode must be one of {AUTH_MODE_CHOICES}")
        if self.requires_auth and not self.read_token:
            issues.append(f"{self.read_token_env} is required when auth_mode=read-token")

        if self.profile == "local":
            if not _is_loopback_host(host) and not self.requires_auth:
                issues.append("local profile cannot bind non-loopback host without read-token auth")
        elif self.profile == "production":
            if self.source == "fixture":
                issues.append("production profile cannot use fixture source")
            if self.auth_mode != "read-token":
                issues.append("production profile requires auth_mode=read-token")
            if self.allowed_origin in {"", "*"}:
                issues.append("production profile requires an explicit allowed origin")
            if self.source in {"live", "auto"} and not self.psql_command:
                issues.append(f"production profile requires {PRODUCTION_DB_ENV} for live/auto source")

        return issues

    def is_authorized(self, authorization_header: str | None) -> bool:
        if not self.requires_auth:
            return True
        if not self.read_token:
            return False
        expected = f"Bearer {self.read_token}"
        return hmac.compare_digest(authorization_header or "", expected)

    def public_metadata(self) -> dict[str, object]:
        return {
            "runtime_profile": self.profile,
            "source_mode": self.source,
            "auth_mode": self.auth_mode,
            "read_auth_required": self.requires_auth,
            "allowed_origin": self.allowed_origin,
        }


def _is_loopback_host(host: str) -> bool:
    normalized = host.strip().lower()
    return normalized in LOOPBACK_HOSTS
