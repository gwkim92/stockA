from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


CONTRACT_INDEX_PATH = Path("docs/api/frontend/contract-index.json")


class FrontendApiAdapterError(RuntimeError):
    """Raised when a frontend API fixture contract cannot be resolved."""


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


def resolve_frontend_response(api_path: str, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or resolve_repo_root()
    for endpoint in list_frontend_endpoints(root):
        if endpoint.path == api_path:
            example_path = root / endpoint.example
            with example_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            return payload
    raise FrontendApiAdapterError(f"Unknown frontend API path: {api_path}")


def build_error_payload(message: str) -> dict[str, Any]:
    return {
        "error": {
            "code": "FrontendApiPathNotFound",
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

    get_parser = subparsers.add_parser("get", help="Return the fixture payload for an exact API path.")
    get_parser.add_argument("--path", required=True, help="Exact API path from docs/api/frontend/contract-index.json.")

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
            _print_json(resolve_frontend_response(args.path))
            return 0
    except FrontendApiAdapterError as exc:
        _print_json(build_error_payload(str(exc)))
        return 1
    raise FrontendApiAdapterError(f"Unhandled command: {args.command!r}")


def main_entry() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    main_entry()
