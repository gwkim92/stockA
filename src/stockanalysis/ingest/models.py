from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DatasetDefinition:
    name: str
    description: str
    documentation_url: str
    required_params: tuple[str, ...]
    optional_params: tuple[str, ...] = ()
    required_env_vars: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class HttpRequest:
    source_name: str
    dataset_name: str
    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes | None = None
    timeout_seconds: float = 30.0

    def as_dict(self) -> dict[str, Any]:
        redacted_headers = {
            key: ("<redacted>" if key.lower() in {"authorization", "x-tossinvest-account"} else value)
            for key, value in self.headers.items()
        }
        return {
            "source_name": self.source_name,
            "dataset_name": self.dataset_name,
            "method": self.method,
            "url": self.url,
            "headers": redacted_headers,
            "body_length": len(self.body) if self.body is not None else 0,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass(frozen=True)
class FetchResponse:
    status_code: int
    content_type: str
    body: bytes

    def as_json(self) -> Any:
        import json

        return json.loads(self.body.decode("utf-8"))

    def as_text(self) -> str:
        return self.body.decode("utf-8")
