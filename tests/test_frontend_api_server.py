from __future__ import annotations

import asyncio
import json
import unittest

from fastapi.testclient import TestClient

from stockanalysis.frontend.api_server import create_app
from stockanalysis.frontend.runtime_policy import FrontendRuntimePolicy


class FakeLiveExecutor:
    def __init__(self) -> None:
        self.scalar_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- frontend dashboard state lookup"):
            return json.dumps(
                {
                    "portfolio_name": "Long Term Paper",
                    "as_of_date": "2024-11-01",
                    "daily_automation": "succeeded",
                    "latest_run_id": 9101,
                    "failed_pipeline_count": 0,
                    "open_ticket_count": 1,
                    "critical_blind_spot_count": 1,
                    "missing_thesis_count": 1,
                    "missing_outcome_count": 0,
                    "top_actions": [
                        {
                            "symbol": "BABA",
                            "action": "needs_thesis_review",
                            "reason": "coverage status missing_thesis",
                            "suggested_runner": "thesis_or_position_link_review",
                            "risk_level": "high",
                        }
                    ],
                    "latest_metrics": {
                        "covered_weight": "0.0500",
                        "missing_thesis_weight": "0.0300",
                        "cash_weight": "0.9200",
                        "weight_coverage_ratio": "0.6250",
                    },
                }
            )
        raise AssertionError(f"unexpected SQL: {sql[:80]}")


class FailingPool:
    def check(self) -> None:
        raise RuntimeError("database unavailable")


class FrontendApiServerTests(unittest.TestCase):
    def test_health_is_public_and_exposes_safe_runtime_metadata(self) -> None:
        policy = FrontendRuntimePolicy(profile="local", source="live", auth_mode="disabled")
        app = create_app(runtime_policy=policy, executor=FakeLiveExecutor())

        with TestClient(app) as client:
            response = client.get("/__health", headers={"X-Request-ID": "req-local-001"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Request-ID"], "req-local-001")
        payload = response.json()
        self.assertEqual(payload["service"], "frontend-api-server")
        self.assertEqual(payload["runtime"]["runtime_profile"], "local")
        self.assertEqual(payload["request_timeout_seconds"], 30.0)
        self.assertNotIn("database_url", payload["runtime"])
        self.assertNotIn("read_token", payload["runtime"])

    def test_live_and_ready_are_public_and_do_not_expose_secrets(self) -> None:
        policy = FrontendRuntimePolicy(profile="local", source="live", auth_mode="disabled")
        app = create_app(runtime_policy=policy, executor=FakeLiveExecutor())

        with TestClient(app) as client:
            live = client.get("/__live")
            ready = client.get("/__ready")

        self.assertEqual(live.status_code, 200)
        self.assertEqual(live.json()["status"], "ok")
        self.assertEqual(ready.status_code, 200)
        payload = ready.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["connection_boundary"], "injected_executor")
        self.assertNotIn("database_url", json.dumps(payload))
        self.assertNotIn("read_token", json.dumps(payload))

    def test_ready_reports_pool_failure_without_leaking_details(self) -> None:
        policy = FrontendRuntimePolicy(
            profile="production",
            source="live",
            allowed_origin="https://cockpit.example",
            auth_mode="read-token",
            read_token="secret",
            database_url="postgresql://example.invalid/db",
        )
        app = create_app(runtime_policy=policy, executor=FakeLiveExecutor())

        with TestClient(app) as client:
            client.app.state.frontend_connection_boundary = "psycopg_pool"
            client.app.state.frontend_pool = FailingPool()
            response = client.get("/__ready")

        self.assertEqual(response.status_code, 503)
        payload = response.json()
        self.assertEqual(payload["status"], "not_ready")
        self.assertIn({"name": "database_pool", "status": "failed", "connection_boundary": "psycopg_pool"}, payload["checks"])
        self.assertNotIn("database unavailable", json.dumps(payload))

    def test_read_token_auth_protects_endpoints_and_api_paths(self) -> None:
        policy = FrontendRuntimePolicy(
            profile="local",
            source="live",
            auth_mode="read-token",
            read_token="server-secret",
        )
        app = create_app(runtime_policy=policy, executor=FakeLiveExecutor())

        with TestClient(app) as client:
            unauthorized = client.get("/__endpoints")
            authorized = client.get("/__endpoints", headers={"Authorization": "Bearer server-secret"})
            api_unauthorized = client.get("/api/dashboard/today")

        self.assertEqual(unauthorized.status_code, 401)
        self.assertEqual(unauthorized.json()["error"]["code"], "Unauthorized")
        self.assertIn("request_id", unauthorized.json())
        self.assertEqual(authorized.status_code, 200)
        self.assertEqual(authorized.json()["contract_version"], "frontend-api-v0.1")
        self.assertEqual(api_unauthorized.status_code, 401)

    def test_request_id_is_generated_when_inbound_value_is_invalid(self) -> None:
        policy = FrontendRuntimePolicy(profile="local", source="live", auth_mode="disabled")
        app = create_app(runtime_policy=policy, executor=FakeLiveExecutor())

        with TestClient(app) as client:
            response = client.get("/__live", headers={"X-Request-ID": "bad value with spaces"})

        self.assertEqual(response.status_code, 200)
        request_id = response.headers["X-Request-ID"]
        self.assertNotEqual(request_id, "bad value with spaces")
        self.assertEqual(len(request_id), 32)

    def test_live_api_path_returns_existing_frontend_dto_shape(self) -> None:
        policy = FrontendRuntimePolicy(profile="local", source="live", auth_mode="disabled")
        app = create_app(runtime_policy=policy, executor=FakeLiveExecutor())

        with TestClient(app) as client:
            response = client.get("/api/dashboard/today")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["portfolio_name"], "Long Term Paper")
        self.assertEqual(payload["data"]["attention_summary"]["missing_thesis_count"], 1)

    def test_structured_access_log_includes_request_id_and_status(self) -> None:
        policy = FrontendRuntimePolicy(profile="local", source="live", auth_mode="disabled")
        app = create_app(runtime_policy=policy, executor=FakeLiveExecutor())

        with self.assertLogs("stockanalysis.frontend.api_server", level="INFO") as logs:
            with TestClient(app) as client:
                response = client.get("/__live", headers={"X-Request-ID": "req-log-001"})

        self.assertEqual(response.status_code, 200)
        event = json.loads(logs.records[-1].getMessage())
        self.assertEqual(event["event"], "frontend_api_access")
        self.assertEqual(event["request_id"], "req-log-001")
        self.assertEqual(event["method"], "GET")
        self.assertEqual(event["path"], "/__live")
        self.assertEqual(event["status_code"], 200)
        self.assertEqual(event["source_mode"], "live")

    def test_request_timeout_returns_stable_error_payload(self) -> None:
        policy = FrontendRuntimePolicy(profile="local", source="live", auth_mode="disabled")
        app = create_app(runtime_policy=policy, executor=FakeLiveExecutor(), request_timeout_seconds=0.01)

        @app.get("/slow")
        async def slow() -> dict[str, str]:
            await asyncio.sleep(0.1)
            return {"status": "late"}

        with TestClient(app) as client:
            response = client.get("/slow", headers={"X-Request-ID": "req-timeout-001"})

        self.assertEqual(response.status_code, 504)
        self.assertEqual(response.headers["X-Request-ID"], "req-timeout-001")
        payload = response.json()
        self.assertEqual(payload["error"]["code"], "FrontendApiRequestTimeout")
        self.assertEqual(payload["request_id"], "req-timeout-001")
        self.assertEqual(payload["error"]["details"]["timeout_seconds"], 0.01)

    def test_production_profile_redacts_adapter_errors(self) -> None:
        policy = FrontendRuntimePolicy(
            profile="production",
            source="live",
            allowed_origin="https://cockpit.example",
            auth_mode="read-token",
            read_token="server-secret",
            database_url="postgresql://example.invalid/db",
        )
        app = create_app(runtime_policy=policy, executor=FakeLiveExecutor())

        with TestClient(app) as client:
            response = client.get("/api/not-supported", headers={"Authorization": "Bearer server-secret"})

        self.assertEqual(response.status_code, 501)
        payload = response.json()
        self.assertEqual(payload["error"]["code"], "FrontendLiveReadUnsupportedPath")
        self.assertEqual(payload["error"]["message"], "Frontend API request could not be resolved.")
        self.assertNotIn("source_mode", payload["error"]["details"])

    def test_write_methods_are_blocked_with_stable_error(self) -> None:
        policy = FrontendRuntimePolicy(profile="local", source="live", auth_mode="disabled")
        app = create_app(runtime_policy=policy, executor=FakeLiveExecutor())

        with TestClient(app) as client:
            response = client.post("/api/dashboard/today", json={})

        self.assertEqual(response.status_code, 405)
        payload = response.json()
        self.assertEqual(payload["error"]["code"], "MethodNotAllowed")
        self.assertEqual(payload["error"]["details"]["method"], "POST")

    def test_production_live_runtime_accepts_database_url_without_psql_command(self) -> None:
        policy = FrontendRuntimePolicy(
            profile="production",
            source="live",
            allowed_origin="https://cockpit.example",
            auth_mode="read-token",
            read_token="server-secret",
            database_url="postgresql://example.invalid/db",
        )

        self.assertEqual(policy.validation_issues(host="127.0.0.1"), [])

    def test_production_live_runtime_still_rejects_missing_database_config(self) -> None:
        policy = FrontendRuntimePolicy(
            profile="production",
            source="live",
            allowed_origin="https://cockpit.example",
            auth_mode="read-token",
            read_token="server-secret",
        )

        self.assertIn(
            "production profile requires STOCKANALYSIS_DATABASE_URL or STOCKANALYSIS_PSQL_COMMAND for live/auto source",
            policy.validation_issues(host="127.0.0.1"),
        )


if __name__ == "__main__":
    unittest.main()
