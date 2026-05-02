from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlsplit

from stockanalysis.frontend.api_adapter import (
    FrontendApiAdapterError,
    list_frontend_endpoints,
    load_contract_index,
    resolve_frontend_response,
)
from stockanalysis.frontend.runtime_policy import (
    DEFAULT_ALLOWED_ORIGIN,
    DEFAULT_READ_TOKEN_ENV,
    AUTH_MODE_CHOICES,
    PROFILE_CHOICES,
    SOURCE_CHOICES,
    FrontendRuntimePolicy,
)


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


class FrontendFixtureHTTPServer(ThreadingHTTPServer):
    daemon_threads = True


class FrontendFixtureRequestHandler(BaseHTTPRequestHandler):
    server_version = "StockanalysisFrontendFixtureServer/0.1"
    repo_root: Path | None = None
    source = "fixture"
    runtime_policy = FrontendRuntimePolicy()
    verbose_logs = False

    def log_message(self, format: str, *args: Any) -> None:
        if self.verbose_logs:
            super().log_message(format, *args)

    def do_GET(self) -> None:
        self._handle_read_request()

    def do_HEAD(self) -> None:
        self._handle_read_request()

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_common_headers()
        self.send_header("Allow", "GET, HEAD, OPTIONS")
        self.end_headers()

    def do_POST(self) -> None:
        self._handle_method_not_allowed()

    def do_PUT(self) -> None:
        self._handle_method_not_allowed()

    def do_PATCH(self) -> None:
        self._handle_method_not_allowed()

    def do_DELETE(self) -> None:
        self._handle_method_not_allowed()

    def _handle_read_request(self) -> None:
        request_path = self._request_path()
        if request_path == "/__health":
            self._send_json(self._build_health_payload(), HTTPStatus.OK)
            return
        if not self._is_authorized_request():
            self._send_json(
                build_server_error_payload(
                    code="Unauthorized",
                    message="A valid bearer token is required for this frontend API runtime.",
                    details={"required_role": "viewer", "auth_mode": self.runtime_policy.auth_mode},
                ),
                HTTPStatus.UNAUTHORIZED,
            )
            return
        if request_path == "/__endpoints":
            self._send_json(self._build_endpoint_payload(), HTTPStatus.OK)
            return

        try:
            self._send_json(
                resolve_frontend_response(request_path, self.repo_root, source=self.source),
                HTTPStatus.OK,
            )
        except FrontendApiAdapterError as exc:
            details = {"path": request_path, "method": self.command, "source_mode": self.source}
            message = str(exc)
            if not self.runtime_policy.exposes_detailed_errors:
                details = {"path": request_path, "method": self.command}
                message = "Frontend API request could not be resolved."
            self._send_json(
                build_server_error_payload(
                    code=exc.code,
                    message=message,
                    details=details,
                ),
                _status_for_adapter_error(exc),
            )

    def _handle_method_not_allowed(self) -> None:
        self._send_json(
            build_server_error_payload(
                code="MethodNotAllowed",
                message=f"Method {self.command} is not allowed for the frontend fixture server.",
                details={"method": self.command, "allowed_methods": ["GET", "HEAD", "OPTIONS"]},
            ),
            HTTPStatus.METHOD_NOT_ALLOWED,
        )

    def _request_path(self) -> str:
        parsed = urlsplit(self.path)
        if parsed.query:
            return f"{parsed.path}?{parsed.query}"
        return parsed.path

    def _is_authorized_request(self) -> bool:
        return self.runtime_policy.is_authorized(self.headers.get("Authorization"))

    def _build_health_payload(self) -> dict[str, Any]:
        index = load_contract_index(self.repo_root)
        return {
            "status": "ok",
            "service": "frontend-fixture-server",
            "contract_version": index["contract_version"],
            "endpoint_count": len(index["endpoints"]),
            "read_only": True,
            "source": "docs/api/frontend/contract-index.json",
            "source_mode": self.source,
            "runtime": self.runtime_policy.public_metadata(),
        }

    def _build_endpoint_payload(self) -> dict[str, Any]:
        index = load_contract_index(self.repo_root)
        endpoints = [
            {
                "method": endpoint.method,
                "path": endpoint.path,
                "response_dto": endpoint.response_dto,
                "example": endpoint.example,
                "route_owner": endpoint.route_owner,
                "description": endpoint.description,
            }
            for endpoint in list_frontend_endpoints(self.repo_root)
        ]
        return {
            "contract_version": index["contract_version"],
            "source_mode": self.source,
            "runtime": self.runtime_policy.public_metadata(),
            "data": {"endpoints": endpoints},
        }

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self._send_common_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _send_common_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", self.runtime_policy.allowed_origin)
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Stockanalysis-Runtime-Profile", self.runtime_policy.profile)
        self.send_header("X-Stockanalysis-Source", f"frontend-fixture-server; mode={self.source}")


def build_server_error_payload(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details or {}}}


def _status_for_adapter_error(exc: FrontendApiAdapterError) -> HTTPStatus:
    if exc.code == "FrontendLiveReadUnavailable":
        return HTTPStatus.SERVICE_UNAVAILABLE
    if exc.code == "FrontendLiveReadUnsupportedPath":
        return HTTPStatus.NOT_IMPLEMENTED
    return HTTPStatus.NOT_FOUND


def create_frontend_fixture_handler(
    repo_root: Path | str | None = None,
    *,
    source: str = "fixture",
    runtime_profile: str | None = None,
    allowed_origin: str | None = None,
    auth_mode: str | None = None,
    read_token_env: str = DEFAULT_READ_TOKEN_ENV,
    runtime_policy: FrontendRuntimePolicy | None = None,
    host: str = DEFAULT_HOST,
    verbose_logs: bool = False,
) -> type[FrontendFixtureRequestHandler]:
    selected_policy = runtime_policy or FrontendRuntimePolicy.from_env(
        source=source,
        profile=runtime_profile,
        allowed_origin=allowed_origin,
        auth_mode=auth_mode,
        read_token_env=read_token_env,
    )
    selected_policy.validate_for_startup(host=host)
    resolved_repo_root = Path(repo_root).resolve() if repo_root is not None else None

    class ConfiguredFrontendFixtureRequestHandler(FrontendFixtureRequestHandler):
        pass

    ConfiguredFrontendFixtureRequestHandler.repo_root = resolved_repo_root
    ConfiguredFrontendFixtureRequestHandler.source = selected_policy.source
    ConfiguredFrontendFixtureRequestHandler.runtime_policy = selected_policy
    ConfiguredFrontendFixtureRequestHandler.verbose_logs = verbose_logs
    return ConfiguredFrontendFixtureRequestHandler


def create_frontend_fixture_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    repo_root: Path | str | None = None,
    *,
    source: str = "fixture",
    runtime_profile: str | None = None,
    allowed_origin: str | None = None,
    auth_mode: str | None = None,
    read_token_env: str = DEFAULT_READ_TOKEN_ENV,
    runtime_policy: FrontendRuntimePolicy | None = None,
    verbose_logs: bool = False,
) -> FrontendFixtureHTTPServer:
    handler = create_frontend_fixture_handler(
        repo_root,
        source=source,
        runtime_profile=runtime_profile,
        allowed_origin=allowed_origin,
        auth_mode=auth_mode,
        read_token_env=read_token_env,
        runtime_policy=runtime_policy,
        host=host,
        verbose_logs=verbose_logs,
    )
    return FrontendFixtureHTTPServer((host, port), handler)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stockanalysis-frontend-fixture-server",
        description="Local read-only HTTP server for frontend API fixture responses.",
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Bind host. Defaults to {DEFAULT_HOST}.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Bind port. Defaults to {DEFAULT_PORT}.")
    parser.add_argument("--repo-root", default=None, help="Repository root containing docs/api/frontend.")
    parser.add_argument(
        "--source",
        choices=SOURCE_CHOICES,
        default="fixture",
        help="Read source. `auto` uses live only when STOCKANALYSIS_PSQL_COMMAND is configured.",
    )
    parser.add_argument(
        "--runtime-profile",
        choices=PROFILE_CHOICES,
        default=None,
        help="Runtime safety profile. Defaults to STOCKANALYSIS_FRONTEND_RUNTIME_PROFILE or local.",
    )
    parser.add_argument(
        "--allowed-origin",
        default=None,
        help=f"CORS allowed origin. Defaults to STOCKANALYSIS_FRONTEND_API_ALLOWED_ORIGIN or {DEFAULT_ALLOWED_ORIGIN}.",
    )
    parser.add_argument(
        "--auth-mode",
        choices=AUTH_MODE_CHOICES,
        default=None,
        help="Read auth mode. Defaults to STOCKANALYSIS_FRONTEND_API_AUTH_MODE or disabled.",
    )
    parser.add_argument(
        "--read-token-env",
        default=DEFAULT_READ_TOKEN_ENV,
        help=f"Environment variable containing the read bearer token. Defaults to {DEFAULT_READ_TOKEN_ENV}.",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable HTTP request logging.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    server = create_frontend_fixture_server(
        host=args.host,
        port=args.port,
        repo_root=args.repo_root,
        source=args.source,
        runtime_profile=args.runtime_profile,
        allowed_origin=args.allowed_origin,
        auth_mode=args.auth_mode,
        read_token_env=args.read_token_env,
        verbose_logs=args.verbose,
    )
    handler = server.RequestHandlerClass
    host, port = server.server_address
    print(
        json.dumps(
            {
                "status": "serving",
                "service": "frontend-fixture-server",
                "base_url": f"http://{host}:{port}",
                "health": f"http://{host}:{port}/__health",
                "read_only": True,
                "source_mode": handler.source,
                "runtime": handler.runtime_policy.public_metadata(),
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


def main_entry() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    main_entry()
