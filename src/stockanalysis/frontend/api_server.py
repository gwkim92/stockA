from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import time
import uuid
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
from stockanalysis.frontend.observability import (
    OBSERVABILITY_MODE_CHOICES,
    OBSERVABILITY_MODE_ENV,
    OTLP_ENDPOINT_ENV,
    FrontendObservabilityConfig,
    access_telemetry_attributes,
    configure_frontend_observability,
)
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
DEFAULT_REQUEST_TIMEOUT_SECONDS = 30.0
REQUEST_TIMEOUT_ENV = "STOCKANALYSIS_FRONTEND_API_REQUEST_TIMEOUT_SECONDS"
REQUEST_ID_HEADER = "X-Request-ID"
WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
ACCESS_LOGGER = logging.getLogger("stockanalysis.frontend.api_server")


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
    request_timeout_seconds: float | None = None,
    observability_mode: str | None = None,
    otlp_endpoint: str | None = None,
) -> FastAPI:
    selected_policy = runtime_policy or FrontendRuntimePolicy.from_env(
        source=source,
        profile=runtime_profile,
        allowed_origin=allowed_origin,
        auth_mode=auth_mode,
        read_token_env=read_token_env,
    )
    selected_policy.validate_for_startup(host=host)
    selected_observability_config = FrontendObservabilityConfig.from_env(
        mode=observability_mode,
        otlp_endpoint=otlp_endpoint,
        deployment_environment=selected_policy.profile,
    )
    selected_request_timeout_seconds = _resolve_request_timeout_seconds(request_timeout_seconds)
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
        app.state.frontend_pool = None
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
            app.state.frontend_pool = pool
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
        allow_headers=["Authorization", "Content-Type", REQUEST_ID_HEADER],
        expose_headers=[REQUEST_ID_HEADER],
    )

    @app.middleware("http")
    async def add_runtime_boundary(request: Request, call_next: Any) -> Response:
        request_id = _request_id_from_header(request.headers.get(REQUEST_ID_HEADER))
        request.state.request_id = request_id
        started = time.perf_counter()
        status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        try:
            response = await asyncio.wait_for(call_next(request), timeout=selected_request_timeout_seconds)
            status_code = HTTPStatus(response.status_code)
        except asyncio.TimeoutError:
            status_code = HTTPStatus.GATEWAY_TIMEOUT
            response = _json_response(
                _server_error_payload(
                    code="FrontendApiRequestTimeout",
                    message="Frontend API request timed out.",
                    details={
                        "path": request.url.path,
                        "method": request.method,
                        "timeout_seconds": selected_request_timeout_seconds,
                    },
                    request_id=request_id,
                ),
                status_code,
            )
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 3)
            _log_access(
                request=request,
                request_id=request_id,
                status_code=int(status_code),
                duration_ms=duration_ms,
                policy=selected_policy,
            )
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Stockanalysis-Runtime-Profile"] = selected_policy.profile
        response.headers["X-Stockanalysis-Source"] = f"frontend-api-server; mode={selected_policy.source}"
        response.headers[REQUEST_ID_HEADER] = request_id
        return response

    @app.get("/__live")
    async def live() -> JSONResponse:
        return _json_response(
            {
                "status": "ok",
                "service": "frontend-api-server",
                "read_only": True,
            }
        )

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
                "observability": _observability_metadata(app),
                "connection_boundary": getattr(app.state, "frontend_connection_boundary", "not_started"),
                "request_timeout_seconds": selected_request_timeout_seconds,
            }
        )

    @app.get("/__ready")
    async def ready() -> JSONResponse:
        payload, status = await _readiness_payload(
            app=app,
            repo_root=resolved_repo_root,
            policy=selected_policy,
        )
        return _json_response(payload, status)

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
            return _adapter_error_response(
                exc,
                request_path=request_path,
                policy=selected_policy,
                request_id=_request_id_for_request(request),
            )
        except Exception:
            return _unexpected_error_response(
                request_path=request_path,
                policy=selected_policy,
                request_id=_request_id_for_request(request),
            )

    @app.api_route("/{path:path}", methods=list(WRITE_METHODS))
    async def write_method_not_allowed(path: str, request: Request) -> JSONResponse:
        return _json_response(
            _server_error_payload(
                code="MethodNotAllowed",
                message=f"Method {request.method} is not allowed for the frontend API server.",
                details={"method": request.method, "allowed_methods": ["GET", "HEAD", "OPTIONS"]},
                request_id=_request_id_for_request(request),
            ),
            HTTPStatus.METHOD_NOT_ALLOWED,
        )

    app.state.frontend_observability_config = selected_observability_config
    app.state.frontend_observability_runtime = configure_frontend_observability(
        app=app,
        config=selected_observability_config,
    )
    return app


def _json_response(payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> JSONResponse:
    return JSONResponse(content=payload, status_code=int(status))


def _observability_metadata(app: FastAPI) -> dict[str, Any]:
    config = getattr(app.state, "frontend_observability_config", None)
    runtime = getattr(app.state, "frontend_observability_runtime", None)
    metadata: dict[str, Any] = {}
    if config is not None:
        metadata.update(config.public_metadata())
    if runtime is not None:
        metadata.update(runtime.public_metadata())
    return metadata


def _server_error_payload(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    payload = build_server_error_payload(code=code, message=message, details=details)
    if request_id:
        payload["request_id"] = request_id
    return payload


def _unauthorized_response_if_needed(
    request: Request,
    policy: FrontendRuntimePolicy,
) -> JSONResponse | None:
    if policy.is_authorized(request.headers.get("Authorization")):
        return None
    return _json_response(
        _server_error_payload(
            code="Unauthorized",
            message="A valid bearer token is required for this frontend API runtime.",
            details={"required_role": "viewer", "auth_mode": policy.auth_mode},
            request_id=_request_id_for_request(request),
        ),
        HTTPStatus.UNAUTHORIZED,
    )


def _adapter_error_response(
    exc: FrontendApiAdapterError,
    *,
    request_path: str,
    policy: FrontendRuntimePolicy,
    request_id: str | None = None,
) -> JSONResponse:
    details = {"path": request_path, "method": "GET", "source_mode": policy.source}
    message = str(exc)
    if not policy.exposes_detailed_errors:
        details = {"path": request_path, "method": "GET"}
        message = "Frontend API request could not be resolved."
    return _json_response(
        _server_error_payload(code=exc.code, message=message, details=details, request_id=request_id),
        _status_for_adapter_error(exc),
    )


def _unexpected_error_response(
    *,
    request_path: str,
    policy: FrontendRuntimePolicy,
    request_id: str | None = None,
) -> JSONResponse:
    message = "Frontend API server request failed."
    details: dict[str, Any] = {"path": request_path, "method": "GET"}
    if policy.exposes_detailed_errors:
        details["source_mode"] = policy.source
    return _json_response(
        _server_error_payload(
            code="FrontendApiServerError",
            message=message,
            details=details,
            request_id=request_id,
        ),
        HTTPStatus.INTERNAL_SERVER_ERROR,
    )


def _status_for_adapter_error(exc: FrontendApiAdapterError) -> HTTPStatus:
    if exc.code == "FrontendPaginationInvalid":
        return HTTPStatus.BAD_REQUEST
    if exc.code == "FrontendLiveReadUnavailable":
        return HTTPStatus.SERVICE_UNAVAILABLE
    if exc.code == "FrontendLiveReadUnsupportedPath":
        return HTTPStatus.NOT_IMPLEMENTED
    return HTTPStatus.NOT_FOUND


async def _readiness_payload(
    *,
    app: FastAPI,
    repo_root: Path | None,
    policy: FrontendRuntimePolicy,
) -> tuple[dict[str, Any], HTTPStatus]:
    checks: list[dict[str, Any]] = []
    ready = True

    try:
        index = load_contract_index(repo_root)
        checks.append(
            {
                "name": "frontend_contract",
                "status": "ok",
                "contract_version": index["contract_version"],
                "endpoint_count": len(index["endpoints"]),
            }
        )
    except Exception:
        ready = False
        checks.append({"name": "frontend_contract", "status": "failed"})

    connection_boundary = getattr(app.state, "frontend_connection_boundary", "not_started")
    pool = getattr(app.state, "frontend_pool", None)
    if connection_boundary == "psycopg_pool" and pool is not None:
        try:
            await run_in_threadpool(pool.check)
            checks.append({"name": "database_pool", "status": "ok", "connection_boundary": connection_boundary})
        except Exception:
            ready = False
            checks.append({"name": "database_pool", "status": "failed", "connection_boundary": connection_boundary})
    elif connection_boundary == "not_started":
        ready = False
        checks.append({"name": "runtime_lifespan", "status": "failed", "connection_boundary": connection_boundary})
    else:
        checks.append({"name": "database_pool", "status": "not_applicable", "connection_boundary": connection_boundary})

    payload = {
        "status": "ok" if ready else "not_ready",
        "service": "frontend-api-server",
        "read_only": True,
        "source_mode": policy.source,
        "runtime": policy.public_metadata(),
        "connection_boundary": connection_boundary,
        "checks": checks,
    }
    return payload, HTTPStatus.OK if ready else HTTPStatus.SERVICE_UNAVAILABLE


def _request_id_from_header(raw_request_id: str | None) -> str:
    if raw_request_id and REQUEST_ID_PATTERN.fullmatch(raw_request_id):
        return raw_request_id
    return uuid.uuid4().hex


def _request_id_for_request(request: Request) -> str | None:
    request_id = getattr(request.state, "request_id", None)
    if isinstance(request_id, str) and request_id:
        return request_id
    return None


def _resolve_request_timeout_seconds(value: float | None) -> float:
    raw_value = value if value is not None else os.environ.get(REQUEST_TIMEOUT_ENV)
    if raw_value is None:
        return DEFAULT_REQUEST_TIMEOUT_SECONDS
    timeout_seconds = float(raw_value)
    if timeout_seconds <= 0:
        raise ValueError("request timeout seconds must be greater than 0")
    return timeout_seconds


def _log_access(
    *,
    request: Request,
    request_id: str,
    status_code: int,
    duration_ms: float,
    policy: FrontendRuntimePolicy,
) -> None:
    attributes = access_telemetry_attributes(
        request=request,
        status_code=status_code,
        runtime_profile=policy.profile,
        source_mode=policy.source,
    )
    ACCESS_LOGGER.info(
        json.dumps(
            {
                "event": "frontend_api_access",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "route_template": attributes["route_template"],
                "status_code": status_code,
                "status_class": attributes["status_class"],
                "duration_ms": duration_ms,
                "runtime_profile": policy.profile,
                "source_mode": policy.source,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


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
    parser.add_argument(
        "--request-timeout-seconds",
        type=float,
        default=None,
        help=f"HTTP request timeout. Defaults to {REQUEST_TIMEOUT_ENV} or {DEFAULT_REQUEST_TIMEOUT_SECONDS}.",
    )
    parser.add_argument(
        "--observability-mode",
        choices=OBSERVABILITY_MODE_CHOICES,
        default=None,
        help=f"Observability mode. Defaults to {OBSERVABILITY_MODE_ENV} or disabled.",
    )
    parser.add_argument(
        "--otlp-endpoint",
        default=None,
        help=f"OTLP/HTTP Collector base endpoint. Defaults to {OTLP_ENDPOINT_ENV}. Not printed in metadata.",
    )
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
        request_timeout_seconds=args.request_timeout_seconds,
        observability_mode=args.observability_mode,
        otlp_endpoint=args.otlp_endpoint,
    )
    print(
        json.dumps(
            {
                "status": "serving",
                "service": "frontend-api-server",
                "base_url": f"http://{args.host}:{args.port}",
                "health": f"http://{args.host}:{args.port}/__health",
                "live": f"http://{args.host}:{args.port}/__live",
                "ready": f"http://{args.host}:{args.port}/__ready",
                "read_only": True,
                "request_timeout_seconds": _resolve_request_timeout_seconds(args.request_timeout_seconds),
                "source_mode": app.state.frontend_source if hasattr(app.state, "frontend_source") else args.source,
                "database_env": DATABASE_URL_ENV,
                "observability": _observability_metadata(app),
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
