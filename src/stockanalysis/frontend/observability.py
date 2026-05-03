from __future__ import annotations

import importlib
import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit, urlunsplit


OBSERVABILITY_MODE_ENV = "STOCKANALYSIS_FRONTEND_API_OBSERVABILITY_MODE"
OTLP_ENDPOINT_ENV = "STOCKANALYSIS_FRONTEND_API_OTLP_ENDPOINT"
DEFAULT_OBSERVABILITY_MODE = "disabled"
OBSERVABILITY_MODE_CHOICES = ("disabled", "otlp")
DEFAULT_OTEL_SERVICE_NAME = "stockanalysis-frontend-api"
DEFAULT_OTEL_SERVICE_NAMESPACE = "stockanalysis"
DEFAULT_OTEL_SERVICE_VERSION = "0.1.0"
OTEL_EXTRA_REQUIREMENT = "stockanalysis[otel]"


class FrontendObservabilityError(ValueError):
    pass


@dataclass(frozen=True)
class FrontendObservabilityConfig:
    mode: str = DEFAULT_OBSERVABILITY_MODE
    otlp_endpoint: str | None = None
    service_name: str = DEFAULT_OTEL_SERVICE_NAME
    service_namespace: str = DEFAULT_OTEL_SERVICE_NAMESPACE
    service_version: str = DEFAULT_OTEL_SERVICE_VERSION
    deployment_environment: str | None = None

    @classmethod
    def from_env(
        cls,
        *,
        mode: str | None = None,
        otlp_endpoint: str | None = None,
        deployment_environment: str | None = None,
    ) -> "FrontendObservabilityConfig":
        selected_mode = _normalize_mode(mode if mode is not None else os.environ.get(OBSERVABILITY_MODE_ENV))
        selected_endpoint = otlp_endpoint if otlp_endpoint is not None else os.environ.get(OTLP_ENDPOINT_ENV)
        normalized_endpoint = _normalize_otlp_endpoint(selected_endpoint)
        config = cls(
            mode=selected_mode,
            otlp_endpoint=normalized_endpoint,
            deployment_environment=deployment_environment,
        )
        config.validate_for_startup()
        return config

    def validate_for_startup(self) -> None:
        if self.mode not in OBSERVABILITY_MODE_CHOICES:
            raise FrontendObservabilityError(
                f"unsupported observability mode: {self.mode}. expected one of {OBSERVABILITY_MODE_CHOICES}"
            )
        if self.mode == "otlp" and not self.otlp_endpoint:
            raise FrontendObservabilityError(f"{OTLP_ENDPOINT_ENV} is required when observability mode is otlp")

    def public_metadata(self) -> dict[str, Any]:
        return {
            "observability_mode": self.mode,
            "otlp_configured": self.mode == "otlp" and bool(self.otlp_endpoint),
            "service_name": self.service_name,
            "service_namespace": self.service_namespace,
            "service_version": self.service_version,
        }

    def resource_attributes(self) -> dict[str, str]:
        attributes = {
            "service.name": self.service_name,
            "service.namespace": self.service_namespace,
            "service.version": self.service_version,
        }
        if self.deployment_environment:
            attributes["deployment.environment.name"] = self.deployment_environment
        return attributes


@dataclass(frozen=True)
class FrontendObservabilityRuntime:
    mode: str
    exporter: str
    instrumented: bool

    def public_metadata(self) -> dict[str, Any]:
        return {
            "observability_mode": self.mode,
            "exporter": self.exporter,
            "instrumented": self.instrumented,
        }


def configure_frontend_observability(
    *,
    app: Any,
    config: FrontendObservabilityConfig,
) -> FrontendObservabilityRuntime:
    if config.mode == "disabled":
        return FrontendObservabilityRuntime(mode=config.mode, exporter="none", instrumented=False)

    modules = _load_otel_modules()
    resource = modules["Resource"].create(config.resource_attributes())
    trace_provider = modules["TracerProvider"](resource=resource)
    metric_reader = modules["PeriodicExportingMetricReader"](
        modules["OTLPMetricExporter"](endpoint=_otlp_signal_endpoint(config.otlp_endpoint, "v1/metrics"))
    )
    meter_provider = modules["MeterProvider"](resource=resource, metric_readers=[metric_reader])
    trace_provider.add_span_processor(
        modules["BatchSpanProcessor"](
            modules["OTLPSpanExporter"](endpoint=_otlp_signal_endpoint(config.otlp_endpoint, "v1/traces"))
        )
    )
    modules["trace"].set_tracer_provider(trace_provider)
    modules["metrics"].set_meter_provider(meter_provider)
    modules["FastAPIInstrumentor"].instrument_app(
        app,
        tracer_provider=trace_provider,
        meter_provider=meter_provider,
    )
    return FrontendObservabilityRuntime(mode=config.mode, exporter="otlp_http", instrumented=True)


def access_telemetry_attributes(
    *,
    request: Any,
    status_code: int,
    runtime_profile: str,
    source_mode: str,
) -> dict[str, str]:
    return {
        "route_template": route_template_for_request(request),
        "method": str(request.method),
        "status_class": status_class_for_status_code(status_code),
        "runtime_profile": runtime_profile,
        "source_mode": source_mode,
    }


def route_template_for_request(request: Any) -> str:
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)
    if isinstance(route_path, str) and route_path:
        return route_path
    return "__unmatched__"


def status_class_for_status_code(status_code: int) -> str:
    if status_code < 100 or status_code > 599:
        return "unknown"
    return f"{status_code // 100}xx"


def _normalize_mode(raw_mode: str | None) -> str:
    if raw_mode is None or raw_mode.strip() == "":
        return DEFAULT_OBSERVABILITY_MODE
    return raw_mode.strip().lower()


def _normalize_otlp_endpoint(raw_endpoint: str | None) -> str | None:
    if raw_endpoint is None or raw_endpoint.strip() == "":
        return None
    endpoint = raw_endpoint.strip().rstrip("/")
    parsed = urlsplit(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise FrontendObservabilityError(f"{OTLP_ENDPOINT_ENV} must be an http or https URL")
    if parsed.username or parsed.password:
        raise FrontendObservabilityError(f"{OTLP_ENDPOINT_ENV} must not contain username or password")
    if parsed.query or parsed.fragment:
        raise FrontendObservabilityError(f"{OTLP_ENDPOINT_ENV} must not contain query string or fragment")
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", ""))


def _otlp_signal_endpoint(base_endpoint: str | None, signal_path: str) -> str:
    if base_endpoint is None:
        raise FrontendObservabilityError(f"{OTLP_ENDPOINT_ENV} is required when observability mode is otlp")
    parsed = urlsplit(base_endpoint)
    base_path = parsed.path.rstrip("/")
    signal_suffix = f"/{signal_path.strip('/')}"
    path = signal_suffix if base_path in {"", "/"} else f"{base_path}{signal_suffix}"
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def _load_otel_modules() -> dict[str, Any]:
    try:
        trace_module = importlib.import_module("opentelemetry.trace")
        metrics_module = importlib.import_module("opentelemetry.metrics")
        resource_module = importlib.import_module("opentelemetry.sdk.resources")
        trace_provider_module = importlib.import_module("opentelemetry.sdk.trace")
        trace_export_module = importlib.import_module("opentelemetry.sdk.trace.export")
        metric_provider_module = importlib.import_module("opentelemetry.sdk.metrics")
        metric_export_module = importlib.import_module("opentelemetry.sdk.metrics.export")
        otlp_trace_module = importlib.import_module("opentelemetry.exporter.otlp.proto.http.trace_exporter")
        otlp_metric_module = importlib.import_module("opentelemetry.exporter.otlp.proto.http.metric_exporter")
        fastapi_module = importlib.import_module("opentelemetry.instrumentation.fastapi")
    except ModuleNotFoundError as exc:
        raise FrontendObservabilityError(
            f"OpenTelemetry packages are required for otlp mode. Install optional extra: {OTEL_EXTRA_REQUIREMENT}"
        ) from exc

    return {
        "trace": trace_module,
        "metrics": metrics_module,
        "Resource": resource_module.Resource,
        "TracerProvider": trace_provider_module.TracerProvider,
        "BatchSpanProcessor": trace_export_module.BatchSpanProcessor,
        "MeterProvider": metric_provider_module.MeterProvider,
        "PeriodicExportingMetricReader": metric_export_module.PeriodicExportingMetricReader,
        "OTLPSpanExporter": otlp_trace_module.OTLPSpanExporter,
        "OTLPMetricExporter": otlp_metric_module.OTLPMetricExporter,
        "FastAPIInstrumentor": fastapi_module.FastAPIInstrumentor,
    }
