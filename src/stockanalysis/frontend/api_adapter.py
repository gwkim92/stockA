from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import parse_qs, urlsplit

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.frontend.pagination import (
    FrontendPaginationError,
    apply_frontend_pagination,
    canonical_frontend_path_for_pagination,
)


CONTRACT_INDEX_PATH = Path("docs/api/frontend/contract-index.json")


class FrontendApiAdapterError(RuntimeError):
    """Raised when a frontend API fixture contract cannot be resolved."""

    def __init__(self, message: str, *, code: str = "FrontendApiPathNotFound") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class FrontendEndpoint:
    method: str
    path: str
    response_dto: str
    example: str
    route_owner: str
    description: str


def resolve_repo_root(start: Path | None = None) -> Path:
    current = (start or Path(__file__)).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / CONTRACT_INDEX_PATH).is_file():
            return candidate
    raise FrontendApiAdapterError("Could not locate frontend API contract index.")


def load_contract_index(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or resolve_repo_root()
    index_path = root / CONTRACT_INDEX_PATH
    with index_path.open("r", encoding="utf-8") as handle:
        index = json.load(handle)
    if index.get("contract_version") != "frontend-api-v0.1":
        raise FrontendApiAdapterError(f"Unsupported contract version: {index.get('contract_version')!r}")
    if not isinstance(index.get("endpoints"), list):
        raise FrontendApiAdapterError("Contract index is missing endpoints.")
    return index


def list_frontend_endpoints(repo_root: Path | None = None) -> list[FrontendEndpoint]:
    index = load_contract_index(repo_root)
    endpoints: list[FrontendEndpoint] = []
    for raw_endpoint in index["endpoints"]:
        endpoints.append(
            FrontendEndpoint(
                method=raw_endpoint["method"],
                path=raw_endpoint["path"],
                response_dto=raw_endpoint["response_dto"],
                example=raw_endpoint["example"],
                route_owner=raw_endpoint["route_owner"],
                description=raw_endpoint["description"],
            )
        )
    return endpoints


def resolve_frontend_response(
    api_path: str,
    repo_root: Path | None = None,
    *,
    source: str = "fixture",
    config: RuntimeConfig | None = None,
    executor: Any | None = None,
) -> dict[str, Any]:
    try:
        if source not in {"fixture", "live", "auto"}:
            raise FrontendApiAdapterError(f"Unsupported frontend API source: {source}", code="FrontendApiSourceInvalid")
        if source == "live":
            return _resolve_live_frontend_response(api_path, config=config, executor=executor)
        if source == "auto" and _should_try_live_source(api_path, config=config, executor=executor):
            return _resolve_live_frontend_response(api_path, config=config, executor=executor)

        root = repo_root or resolve_repo_root()
        direct_example_path = _fixture_direct_example_path(api_path)
        if direct_example_path is not None:
            with (root / direct_example_path).open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            return apply_frontend_pagination(api_path, payload)

        canonical_path = canonical_frontend_path_for_pagination(api_path)
        candidate_paths = [api_path]
        if canonical_path not in candidate_paths:
            candidate_paths.append(canonical_path)
        alias_path = _fixture_alias_path(api_path)
        if alias_path and alias_path not in candidate_paths:
            candidate_paths.append(alias_path)
        for endpoint in list_frontend_endpoints(root):
            if endpoint.path in candidate_paths:
                example_path = root / endpoint.example
                with example_path.open("r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                return apply_frontend_pagination(api_path, payload)
    except FrontendPaginationError as exc:
        raise FrontendApiAdapterError(str(exc), code=exc.code) from exc
    raise FrontendApiAdapterError(f"Unknown frontend API path: {api_path}")


def _fixture_alias_path(api_path: str) -> str | None:
    """Map live-style frontend queries to stable local fixture examples.

    Fixture files are intentionally tiny and date-stable. Current app routes use
    today's date and extra filter parameters, so local visual smoke needs a
    representative fixture alias without changing live adapter behavior.
    """
    parsed = urlsplit(api_path)
    query = _single_value_query(parsed.query)
    if parsed.path == "/api/events" and query.get("asOfDate"):
        return "/api/events?asOfDate=2024-11-01"
    if parsed.path == "/api/ai/news-clusters":
        return "/api/ai/news-clusters?asOfDate=2026-05-19"
    if parsed.path == "/api/cycles" and query.get("asOfDate"):
        return "/api/cycles?asOfDate=2024-11-01"
    if parsed.path == "/api/cycle-map" and query.get("asOfDate"):
        return "/api/cycle-map?asOfDate=2026-06-05"
    if parsed.path == "/api/market-map" and query.get("asOfDate"):
        return "/api/market-map?asOfDate=2026-06-05"
    if parsed.path.startswith("/api/themes/") and query.get("asOfDate"):
        return "/api/themes/ANNUAL_REPORTING?asOfDate=2024-11-01"
    if parsed.path == "/api/recommendations/recommendation-7101":
        return "/api/recommendations/AAPL-2024-11-01"
    if parsed.path.startswith("/api/portfolio/") and parsed.path.endswith("/coverage") and query.get("asOfDate"):
        return "/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2024-11-01"
    if (
        parsed.path.startswith("/api/performance/")
        and parsed.path.endswith("/outcomes")
        and query.get("measurementEndDate")
    ):
        return "/api/performance/Long%20Term%20Paper/outcomes?measurementEndDate=2024-12-02"
    return None


def _fixture_direct_example_path(api_path: str) -> Path | None:
    parsed = urlsplit(api_path)
    if parsed.path == "/api/stocks/SPY":
        return Path("docs/api/frontend/examples/stock-detail-spy.json")
    if parsed.path == "/api/recommendations/AAPL-professional-2026-06-25":
        return Path("docs/api/frontend/examples/recommendation-detail-professional.json")
    return None


def _single_value_query(raw_query: str) -> dict[str, str]:
    query_values = parse_qs(raw_query, keep_blank_values=True)
    query: dict[str, str] = {}
    for key, values in query_values.items():
        if values:
            query[key] = values[-1]
    return query


def _resolve_live_frontend_response(
    api_path: str,
    *,
    config: RuntimeConfig | None,
    executor: Any | None,
) -> dict[str, Any]:
    from stockanalysis.frontend.live_adapter import FrontendLiveAdapterError, resolve_live_frontend_response

    try:
        return resolve_live_frontend_response(api_path, config=config, executor=executor)
    except FrontendLiveAdapterError as exc:
        raise FrontendApiAdapterError(str(exc), code=exc.code) from exc
    except FrontendPaginationError as exc:
        raise FrontendApiAdapterError(str(exc), code=exc.code) from exc


def _should_try_live_source(
    api_path: str,
    *,
    config: RuntimeConfig | None,
    executor: Any | None,
) -> bool:
    from stockanalysis.frontend.live_adapter import is_live_supported_path

    if not is_live_supported_path(api_path):
        return False
    if executor is not None:
        return True
    runtime_config = config or RuntimeConfig.from_env()
    return bool(runtime_config.psql_command)


def build_error_payload(message: str, *, code: str = "FrontendApiPathNotFound") -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": {},
        }
    }


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stockanalysis-frontend-api",
        description="Read-only frontend API fixture adapter.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List frontend API fixture endpoints.")

    get_parser = subparsers.add_parser("get", help="Return the payload for an exact API path.")
    get_parser.add_argument("--path", required=True, help="Exact API path from docs/api/frontend/contract-index.json.")
    get_parser.add_argument(
        "--source",
        choices=("fixture", "live", "auto"),
        default="fixture",
        help="Read source. `auto` uses live only when STOCKANALYSIS_PSQL_COMMAND is configured.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            endpoints = [
                {
                    "method": endpoint.method,
                    "path": endpoint.path,
                    "response_dto": endpoint.response_dto,
                    "example": endpoint.example,
                    "route_owner": endpoint.route_owner,
                }
                for endpoint in list_frontend_endpoints()
            ]
            _print_json({"contract_version": load_contract_index()["contract_version"], "endpoints": endpoints})
            return 0
        if args.command == "get":
            _print_json(resolve_frontend_response(args.path, source=args.source))
            return 0
    except FrontendApiAdapterError as exc:
        _print_json(build_error_payload(str(exc), code=exc.code))
        return 1
    raise FrontendApiAdapterError(f"Unhandled command: {args.command!r}")


def main_entry() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    main_entry()
