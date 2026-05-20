from __future__ import annotations

import unittest
from unittest.mock import patch

from stockanalysis.frontend.observability import (
    FrontendObservabilityConfig,
    FrontendObservabilityError,
    _otlp_signal_endpoint,
    access_telemetry_attributes,
    configure_frontend_observability,
    route_template_for_request,
    status_class_for_status_code,
)


class FakeRoute:
    path = "/api/{path:path}"


class FakeRequest:
    method = "GET"
    scope = {"route": FakeRoute()}


class FrontendObservabilityTests(unittest.TestCase):
    def test_default_mode_is_disabled_without_otel_packages(self) -> None:
        config = FrontendObservabilityConfig.from_env(mode=None, otlp_endpoint=None)

        self.assertEqual(config.mode, "disabled")
        self.assertFalse(config.public_metadata()["otlp_configured"])
        self.assertNotIn("otlp_endpoint", config.public_metadata())

    def test_otlp_mode_requires_endpoint(self) -> None:
        with self.assertRaises(FrontendObservabilityError) as ctx:
            FrontendObservabilityConfig.from_env(mode="otlp", otlp_endpoint=None)

        self.assertIn("STOCKANALYSIS_FRONTEND_API_OTLP_ENDPOINT", str(ctx.exception))

    def test_invalid_mode_is_rejected(self) -> None:
        with self.assertRaises(FrontendObservabilityError):
            FrontendObservabilityConfig.from_env(mode="vendor-direct", otlp_endpoint=None)

    def test_otlp_endpoint_must_be_http_or_https(self) -> None:
        with self.assertRaises(FrontendObservabilityError):
            FrontendObservabilityConfig.from_env(mode="otlp", otlp_endpoint="grpc://collector:4317")

    def test_otlp_endpoint_rejects_userinfo_query_and_fragment(self) -> None:
        for endpoint in (
            "https://user:pass@collector.example:4318",
            "https://collector.example:4318?debug=true",
            "https://collector.example:4318/#secret",
        ):
            with self.subTest(endpoint=endpoint):
                with self.assertRaises(FrontendObservabilityError):
                    FrontendObservabilityConfig.from_env(mode="otlp", otlp_endpoint=endpoint)

    def test_public_metadata_does_not_expose_endpoint(self) -> None:
        config = FrontendObservabilityConfig.from_env(
            mode="otlp",
            otlp_endpoint="https://collector.example:4318/otel",
            deployment_environment="production",
        )

        metadata = config.public_metadata()
        self.assertTrue(metadata["otlp_configured"])
        self.assertNotIn("collector.example", str(metadata))
        self.assertEqual(config.resource_attributes()["deployment.environment.name"], "production")

    def test_signal_endpoint_extends_base_path(self) -> None:
        self.assertEqual(
            _otlp_signal_endpoint("https://collector.example:4318/otel", "v1/traces"),
            "https://collector.example:4318/otel/v1/traces",
        )

    def test_otlp_runtime_requires_optional_packages(self) -> None:
        config = FrontendObservabilityConfig.from_env(
            mode="otlp",
            otlp_endpoint="https://collector.example:4318",
        )

        def missing_optional_module(module_name: str):
            if module_name.startswith("opentelemetry"):
                raise ModuleNotFoundError(module_name)
            return __import__(module_name)

        with patch("stockanalysis.frontend.observability.importlib.import_module", side_effect=missing_optional_module):
            with self.assertRaises(FrontendObservabilityError) as ctx:
                configure_frontend_observability(app=object(), config=config)

        self.assertIn("stockanalysis[otel]", str(ctx.exception))
        self.assertNotIn("collector.example", str(ctx.exception))

    def test_route_template_and_status_class_are_bounded(self) -> None:
        attrs = access_telemetry_attributes(
            request=FakeRequest(),
            status_code=204,
            runtime_profile="local",
            source_mode="live",
        )

        self.assertEqual(attrs["route_template"], "/api/{path:path}")
        self.assertEqual(attrs["status_class"], "2xx")
        self.assertEqual(status_class_for_status_code(700), "unknown")

    def test_route_template_falls_back_to_unmatched_not_raw_path(self) -> None:
        class UnmatchedRequest:
            method = "GET"
            scope = {"path": "/api/recommendations/AAPL-2024-11-01"}

        self.assertEqual(route_template_for_request(UnmatchedRequest()), "__unmatched__")


if __name__ == "__main__":
    unittest.main()
