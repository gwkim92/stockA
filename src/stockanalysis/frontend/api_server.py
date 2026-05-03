from __future__ import annotations

import argparse
import json
from contextlib import asynccontextmanager
from http import HTTPStatus
from pathlib import Path
from typing import Any, AsyncIterator, Sequence

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from psycopg_pool import ConnectionPool
from starlette.concurrency import run_in_threadpool

from stockanalysis.frontend.api_adapter import (
    FrontendApiAdapterError,
    list_frontend_endpoints,
    load_contract_index,
    resolve_frontend_response,
)
from stockanalysis.frontend.db_pool import PsycopgPoolExecutor
from stockanalysis.frontend.fixture_server import build_server_error_payload
from stockanalysis.frontend.runtime_policy import (
    DEFAULT_ALLOWED_ORIGIN,
    DEFAULT_READ_TOKEN_ENV,
    AUTH_MODE_CHOICES,
    DATABASE_URL_ENV,
    PROFILE_CHOICES,
    SOURCE_CHOICES,
    FrontendRuntimePolicy,
)


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
DEFAULT_POOL_MIN_SIZE = 1
DEFAULT_POOL_MAX_SIZE = 4
DEFAULT_POOL_TIMEOUT_SECONDS = 10.0
WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")


def create_app(
    *,
    repo_root: Path | str | None = None,
    source: str = "live",
    runtime_profile: str | None = None,
    allowed_origin: str | None = None,
    auth_mode: str | None = None,
    read_token_env: str = DEFAULT_READ_TOKEN_ENV,
    runtime_policy: FrontendRuntimePolicy | None = None,
    host: str = DEFAULT_HOST,
    executor: Any | None = None,
    pool_min_size: int = DEFAULT_POOL_MIN_SIZE,
    pool_max_size: int = DEFAULT_POOL_MAX_SIZE,
    pool_timeout_seconds: float = DEFAULT_POOL_TIMEOUT_SECONDS,
) -> FastAPI:
    selected_policy = runtime_policy or FrontendRuntimePolicy.from_env(
        source=source,
        profile=runtime_profile,
        allowed_origin=allowed_origin,
        auth_mode=auth_mode,
        read_token_env=read_token_env,
    )
    selected_policy.validate_for_startup(host=host)
    resolved_repo_root = Path(repo_root).resolve() if repo_root is not None else None
    openapi_url = "/openapi.json" if selected_policy.profile == "local" else None
    docs_url = "/docs" if selected_policy.profile == "local" else None

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        pool: ConnectionPool[Any] | None = None
        app.state.frontend_runtime_policy = selected_policy
        app.state.frontend_repo_root = resolved_repo_root
        app.state.frontend_source = selected_policy.source
        app.state.frontend_executor = executor
        app.state.frontend_connection_boundary = "injected_executor" if executor is not None else "psql_command"

        if executor is None and selected_policy.source in {"live", "auto"} and selected_policy.database_url:
            pool = ConnectionPool(
                conninfo=selected_policy.database_url,
                min_size=pool_min_size,
                max_size=pool_max_size,
                open=False,
                timeout=pool_timeout_seconds,
            )
            pool.open()
            pool.wait(timeout=pool_timeout_seconds)
            app.state.frontend_executor = PsycopgPoolExecutor(pool)
            app.state.frontend_connection_boundary = "psycopg_pool"

        try:
            yield
        finally:
            if pool is not None:
                pool.close()

    app = FastAPI(
        title="Stockanalysis Frontend API",
        version="0.1.0",
        summary="Read-only frontend API server for investment cockpit DTOs.",
        openapi_url=openapi_url,
        docs_url=docs_url,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[selected_policy.allowed_origin] if selected_policy.allowed_origin != "*" else ["*"],
        allow_methods=["GET", "HEAD", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.middleware("http")
    async def add_runtime_headers(request: Request, call_next: Any) -> Response:
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Stockanalysis-Runtime-Profile"] = selected_policy.profile
        response.headers["X-Stockanalysis-Source"] = f"frontend-api-server; mode={selected_policy.source}"
        return response

    @app.get("/__health")
    async def health() -> JSONResponse:
        index = load_contract_index(resolved_repo_root)
        return _json_response(
            {
                "status": "ok",
                "service": "frontend-api-server",
                "contract_version": index["contract_version"],
                "endpoint_count": len(index["endpoints"]),
                "read_only": True,
                "source": "docs/api/frontend/contract-index.json",
                "source_mode": selected_policy.source,
                "runtime": selected_policy.public_metadata(),
                "connection_boundary": getattr(app.state, "frontend_connection_boundary", "not_started"),
            }
        )

    @app.get("/__endpoints")
    async def endpoints(request: Request) -> JSONResponse:
        unauthorized = _unauthorized_response_if_needed(request, selected_policy)
        if unauthorized is not None:
            return unauthorized
        index = load_contract_index(resolved_repo_root)
        payload = {
            "contract_version": index["contract_version"],
            "source_mode": selected_policy.source,
            "runtime": selected_policy.public_metadata(),
            "data": {
                "endpoints": [
                    {
                        "method": endpoint.method,
                        "path": endpoint.path,
                        "response_dto": endpoint.response_dto,
                        "example": endpoint.example,
                        "route_owner": endpoint.route_owner,
                        "description": endpoint.description,
                    }
                    for endpoint in list_frontend_endpoints(resolved_repo_root)
                ]
            },
        }
        return _json_response(payload)

    @app.get("/api/{path:path}")
    async def read_api(path: str, request: Request) -> JSONResponse:
        unauthorized = _unauthorized_response_if_needed(request, selected_policy)
        if unauthorized is not None:
            return unauthorized
        request_path = _request_path_from_scope(request)
        try:
            payload = await run_in_threadpool(
                resolve_frontend_response,
                request_path,
                resolved_repo_root,
                source=selected_policy.source,
                executor=getattr(app.state, "frontend_executor", None),
            )
            return _json_response(payload)
        except FrontendApiAdapterError as exc:
            return _adapter_error_response(exc, request_path=request_path, policy=selected_policy)
        except Exception:
            return _unexpected_error_response(request_path=request_path, policy=selected_policy)

    @app.api_route("/{path:path}", methods=list(WRITE_METHODS))
    async def write_method_not_allowed(path: str, request: Request) -> JSONResponse:
        return _json_response(
            build_server_error_payload(
                code="MethodNotAllowed",
                message=f"Method {request.method} is not allowed for the frontend API server.",
                details={"method": request.method, "allowed_methods": ["GET", "HEAD", "OPTIONS"]},
            ),
            HTTPStatus.METHOD_NOT_ALLOWED,
        )

    return app


def _json_response(payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> JSONResponse:
    return JSONResponse(content=payload, status_code=int(status))


def _unauthorized_response_if_needed(
    request: Request,
    policy: FrontendRuntimePolicy,
) -> JSONResponse | None:
    if policy.is_authorized(request.headers.get("Authorization")):
        return None
    return _json_response(
        build_server_error_payload(
            code="Unauthorized",
            message="A valid bearer token is required for this frontend API runtime.",
            details={"required_role": "viewer", "auth_mode": policy.auth_mode},
        ),
        HTTPStatus.UNAUTHORIZED,
    )


def _adapter_error_response(
    exc: FrontendApiAdapterError,
    *,
    request_path: str,
    policy: FrontendRuntimePolicy,
) -> JSONResponse:
    details = {"path": request_path, "method": "GET", "source_mode": policy.source}
    message = str(exc)
    if not policy.exposes_detailed_errors:
        details = {"path": request_path, "method": "GET"}
        message = "Frontend API request could not be resolved."
    return _json_response(
        build_server_error_payload(code=exc.code, message=message, details=details),
        _status_for_adapter_error(exc),
    )


def _unexpected_error_response(*, request_path: str, policy: FrontendRuntimePolicy) -> JSONResponse:
    message = "Frontend API server request failed."
    details: dict[str, Any] = {"path": request_path, "method": "GET"}
    if policy.exposes_detailed_errors:
        details["source_mode"] = policy.source
    return _json_response(
        build_server_error_payload(code="FrontendApiServerError", message=message, details=details),
        HTTPStatus.INTERNAL_SERVER_ERROR,
    )


def _status_for_adapter_error(exc: FrontendApiAdapterError) -> HTTPStatus:
    if exc.code == "FrontendLiveReadUnavailable":
        return HTTPStatus.SERVICE_UNAVAILABLE
    if exc.code == "FrontendLiveReadUnsupportedPath":
        return HTTPStatus.NOT_IMPLEMENTED
    return HTTPStatus.NOT_FOUND


def _request_path_from_scope(request: Request) -> str:
    raw_path = request.scope.get("raw_path")
    if isinstance(raw_path, bytes):
        path = raw_path.decode("ascii")
    else:
        path = request.url.path
    query = request.scope.get("query_string")
    if isinstance(query, bytes) and query:
        return f"{path}?{query.decode('ascii')}"
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stockanalysis-frontend-api-server",
        description="FastAPI read-only frontend API server.",
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Bind host. Defaults to {DEFAULT_HOST}.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Bind port. Defaults to {DEFAULT_PORT}.")
    parser.add_argument("--repo-root", default=None, help="Repository root containing docs/api/frontend.")
    parser.add_argument(
        "--source",
        choices=SOURCE_CHOICES,
        default="live",
        help="Read source. Production profile rejects fixture source.",
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
    parser.add_argument("--pool-min-size", type=int, default=DEFAULT_POOL_MIN_SIZE)
    parser.add_argument("--pool-max-size", type=int, default=DEFAULT_POOL_MAX_SIZE)
    parser.add_argument("--pool-timeout-seconds", type=float, default=DEFAULT_POOL_TIMEOUT_SECONDS)
    parser.add_argument("--log-level", default="info", help="Uvicorn log level.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    app = create_app(
        repo_root=args.repo_root,
        source=args.source,
        runtime_profile=args.runtime_profile,
        allowed_origin=args.allowed_origin,
        auth_mode=args.auth_mode,
        read_token_env=args.read_token_env,
        host=args.host,
        pool_min_size=args.pool_min_size,
        pool_max_size=args.pool_max_size,
        pool_timeout_seconds=args.pool_timeout_seconds,
    )
    print(
        json.dumps(
            {
                "status": "serving",
                "service": "frontend-api-server",
                "base_url": f"http://{args.host}:{args.port}",
                "health": f"http://{args.host}:{args.port}/__health",
                "read_only": True,
                "source_mode": app.state.frontend_source if hasattr(app.state, "frontend_source") else args.source,
                "database_env": DATABASE_URL_ENV,
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        flush=True,
    )
    uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level)
    return 0


def main_entry() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    main_entry()
