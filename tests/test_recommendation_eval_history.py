from __future__ import annotations

import copy
import json
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from stockanalysis.frontend.api_adapter import FrontendApiAdapterError, resolve_frontend_response
from stockanalysis.frontend.api_server import create_app
from stockanalysis.frontend.recommendation_eval_history import (
    API_PATH, EVAL_NAME, MAX_ID, EvaluationHistoryError, HistoryRequest,
    is_evaluation_history_path, parse_evaluation_history_request,
    render_evaluation_history_sql, resolve_evaluation_history,
)
from stockanalysis.frontend.runtime_policy import FrontendRuntimePolicy


def run_row(identifier="9", count=0, config=None):
    return {"eval_run_id": identifier, "eval_name": EVAL_NAME, "pipeline_run_id": None,
            "snapshot_count": count, "stored_config": config, "stored_score": {"alpha": None}}


def snapshot_row(identifier="1", run_id="9"):
    return {"snapshot_id": identifier, "eval_run_id": run_id,
            "source_recommendation_id": str(MAX_ID), "source_batch_id": "2",
            "source_thesis_id": None, "source_outcome_id": None,
            "snapshot_sha256": "a" * 64, "selected_outcome_alpha_pct": None,
            "snapshot_json": {"recommendation": {"total_score": 0}, "selected_outcome": None,
                              "thesis": {"invalidation_conditions": ["historical condition"]}}}


class FakeExecutor:
    def __init__(self, payload=None, ready="true", failure=None):
        self.payload = payload if payload is not None else {"runs": []}
        self.ready = ready
        self.failure = failure
        self.queries = []

    def execute_scalar(self, sql):
        self.queries.append(sql)
        if self.failure:
            raise RuntimeError(self.failure)
        if "pg_catalog.to_regclass" in sql:
            return self.ready
        return json.dumps(self.payload)


class EvaluationHistoryTests(unittest.TestCase):
    def read(self, payload, suffix="", **kwargs):
        executor = FakeExecutor(payload, **kwargs)
        result = resolve_evaluation_history(API_PATH + suffix, source="live", executor=executor)
        self.assertEqual(len(executor.queries), 2)
        return result

    def test_defaults_and_boundary_ids(self):
        self.assertEqual(parse_evaluation_history_request(API_PATH), HistoryRequest())
        self.assertEqual(parse_evaluation_history_request(API_PATH + f"?limit=100&before={MAX_ID}"), HistoryRequest(None, 100, MAX_ID))
        self.assertEqual(parse_evaluation_history_request(API_PATH + f"/eval-run-{MAX_ID}?limit=1&after=1"), HistoryRequest(MAX_ID, 1, 1))

    def test_invalid_selectors_fail_before_config_or_sql(self):
        suffixes = ["/", "/eval-run-0", "/eval-run-01", "/eval-run-+1", "/eval-run--1", "/eval-run-1/extra",
                    f"/eval-run-{MAX_ID + 1}", "/eval-run-1.0", "/eval-run-１", "/eval-run-1%2F2",
                    "?limit=0", "?limit=101", "?limit=01", "?limit=", "?limit", "?limit=1&limit=2",
                    "?before=1&before=2", "?before=0", "?after=1", "?unknown=1", "?limit=1;drop%20table",
                    "?before=1%20OR%201=1", "?limit=true", "?before=%FF", "/eval-run-1?before=2",
                    "?limit=1&before=2&extra=3", "/eval-run-1#fragment", "/eval-run-1\n"]
        for suffix in suffixes:
            with self.subTest(suffix=suffix), patch("stockanalysis.frontend.recommendation_eval_history.RuntimeConfig.from_env", side_effect=AssertionError("unexpected config")):
                executor = FakeExecutor()
                with self.assertRaises(EvaluationHistoryError) as raised:
                    resolve_evaluation_history(API_PATH + suffix, source="live", executor=executor)
                self.assertEqual(raised.exception.code, "FrontendPaginationInvalid")
                self.assertEqual(executor.queries, [])

    def test_route_boundary(self):
        self.assertTrue(is_evaluation_history_path(API_PATH))
        self.assertTrue(is_evaluation_history_path(API_PATH + "/wrong"))
        self.assertFalse(is_evaluation_history_path(API_PATH + "-other"))
        self.assertFalse(is_evaluation_history_path("/api/recommendations"))
        with self.assertRaises(EvaluationHistoryError):
            parse_evaluation_history_request("https://example.invalid" + API_PATH)

    def test_internal_sql_renderer_rejects_noninteger_and_injected_arguments(self):
        for request in [HistoryRequest(limit=True), HistoryRequest(limit=0), HistoryRequest(limit=101),
                        HistoryRequest(eval_run_id="1; delete"), HistoryRequest(cursor=1.1), HistoryRequest(cursor=MAX_ID + 1)]:
            with self.subTest(request=request), self.assertRaises(EvaluationHistoryError):
                render_evaluation_history_sql(request)

    def test_sql_only_reads_history_and_uses_bounded_keysets(self):
        for request in [HistoryRequest(None, 10, 12), HistoryRequest(9, 10, 12)]:
            sql = render_evaluation_history_sql(request).lower()
            self.assertIn("limit 11", sql)
            self.assertIn("recommendation_quality_calibration", sql)
            for forbidden in ["insert ", "update ", "delete ", "alter ", "signal.", "performance.", "ref.instrument", "offset "]:
                self.assertNotIn(forbidden, sql)
        self.assertIn("e.eval_run_id < 12", render_evaluation_history_sql(HistoryRequest(None, 10, 12)))
        self.assertIn("s.snapshot_id > 12", render_evaluation_history_sql(HistoryRequest(9, 10, 12)))

    def test_run_pagination_does_not_aggregate_the_sentinel_row(self):
        result = self.read({"runs": [run_row("9"), run_row("8")]}, "?limit=1")
        self.assertEqual([r["eval_run_id"] for r in result["runs"]], ["9"])
        self.assertEqual(result["pagination"]["next_cursor"], "9")
        self.assertEqual(result["pagination"]["returned_count"], 1)
        self.assertEqual(result["pagination"]["scope"], "returned_page_only")
        self.assertTrue(result["pagination"]["has_more"])

    def test_snapshot_pagination_and_bigint_ids(self):
        config = {"snapshot_count": 2, "snapshot_schema_version": "recommendation-eval-snapshot-v1"}
        result = self.read({"run": run_row(count=2, config=config), "snapshots": [snapshot_row("1"), snapshot_row("2")]}, "/eval-run-9?limit=1")
        self.assertEqual(result["snapshots"][0]["source_recommendation_id"], str(MAX_ID))
        self.assertEqual(result["pagination"]["next_cursor"], "1")
        self.assertEqual(result["pagination"]["cursor_parameter"], "after")
        self.assertEqual(result["run"]["snapshot_count"], 2)
        self.assertEqual(result["run"]["snapshot_state"], "recorded")

    def test_legacy_recorded_empty_and_missing_children_are_distinct(self):
        cases = [(run_row(), "legacy_unavailable"),
                 (run_row(config={"snapshot_count": 0, "snapshot_schema_version": "v1"}), "recorded_empty"),
                 (run_row(config={"snapshot_count": 3, "snapshot_schema_version": "v1"}), "count_mismatch"),
                 (run_row(config={"snapshot_count": True, "snapshot_schema_version": "v1"}), "count_mismatch"),
                 (run_row(count=1), "count_mismatch")]
        for row, state in cases:
            with self.subTest(state=state):
                result = self.read({"runs": [row]})
                self.assertEqual(result["runs"][0]["snapshot_state"], state)

    def test_empty_history_is_not_missing_source(self):
        result = self.read({"runs": []})
        self.assertEqual(result["runs"], [])
        self.assertFalse(result["pagination"]["has_more"])
        self.assertIsNone(result["pagination"]["next_cursor"])

    def test_missing_schema_stops_before_data_query(self):
        executor = FakeExecutor(ready="false")
        with self.assertRaises(EvaluationHistoryError) as raised:
            resolve_evaluation_history(API_PATH, source="live", executor=executor)
        self.assertEqual(raised.exception.code, "FrontendLiveReadUnavailable")
        self.assertEqual(len(executor.queries), 1)

    def test_missing_run_is_not_latest_run(self):
        with self.assertRaises(EvaluationHistoryError) as raised:
            self.read({"run": None, "snapshots": []}, "/eval-run-9")
        self.assertEqual(raised.exception.code, "FrontendApiPathNotFound")

    def test_invalid_payload_and_cross_run_data_fail_closed(self):
        cases = [({}, "/eval-run-9"), ({"run": run_row("8"), "snapshots": []}, "/eval-run-9"),
                 ({"run": run_row(), "snapshots": [snapshot_row(run_id="8")]}, "/eval-run-9"),
                 ({"runs": [run_row("8"), run_row("9")]}, ""), ({"runs": [run_row("9"), run_row("9")]}, ""),
                 ({"runs": [run_row("9")]}, "?before=9"), ({"runs": [run_row(9)]}, ""),
                 ({"runs": [{**run_row(), "eval_name": "other_eval"}]}, "")]
        for payload, suffix in cases:
            with self.subTest(payload=payload), self.assertRaises(EvaluationHistoryError) as raised:
                self.read(payload, suffix)
            self.assertEqual(raised.exception.code, "FrontendLiveReadUnavailable")

    def test_fixture_and_unconfigured_auto_never_invent_history(self):
        executor = FakeExecutor()
        with self.assertRaises(EvaluationHistoryError):
            resolve_evaluation_history(API_PATH, source="fixture", executor=executor)
        self.assertEqual(executor.queries, [])
        with patch("stockanalysis.frontend.recommendation_eval_history.RuntimeConfig.from_env") as config:
            config.return_value.psql_command = None
            with self.assertRaises(EvaluationHistoryError):
                resolve_evaluation_history(API_PATH, source="auto")

    def test_raw_values_preserved_without_mutation_or_quality_assertion(self):
        raw = {"run": run_row(), "snapshots": [snapshot_row()]}
        before = copy.deepcopy(raw)
        result = self.read(raw, "/eval-run-9")
        self.assertEqual(raw, before)
        self.assertIsNone(result["snapshots"][0]["selected_outcome_alpha_pct"])
        self.assertEqual(result["snapshots"][0]["snapshot_json"], raw["snapshots"][0]["snapshot_json"])
        self.assertEqual(result["snapshot_hash_verification"], "not_performed")
        self.assertFalse(result["broker_submit_allowed"])
        self.assertEqual(result["history_basis"], "evaluation_time_snapshot_not_recommendation_creation_time")

    def test_driver_error_is_redacted(self):
        executor = FakeExecutor(failure="postgresql://private:password@host/database SELECT secret")
        with self.assertRaises(EvaluationHistoryError) as raised:
            resolve_evaluation_history(API_PATH, source="live", executor=executor)
        self.assertNotIn("password", str(raised.exception))
        self.assertNotIn("SELECT", str(raised.exception))

    def test_adapter_routes_without_fixture_or_mutable_live_fallback(self):
        executor = FakeExecutor()
        with patch("stockanalysis.frontend.api_adapter._resolve_live_frontend_response", side_effect=AssertionError("mutable fallback")):
            self.assertEqual(resolve_frontend_response(API_PATH, source="auto", executor=executor)["runs"], [])
        with self.assertRaises(FrontendApiAdapterError) as raised:
            resolve_frontend_response(API_PATH + "?limit=0", source="live", executor=executor)
        self.assertEqual(raised.exception.code, "FrontendPaginationInvalid")


class EvaluationHistoryHttpTests(unittest.TestCase):
    def app(self, executor):
        policy = FrontendRuntimePolicy(profile="local", source="live", auth_mode="read-token", read_token="synthetic-token")
        return create_app(runtime_policy=policy, executor=executor, observability_mode="disabled")

    def test_authentication_precedes_database_access(self):
        executor = FakeExecutor()
        with TestClient(self.app(executor)) as client:
            self.assertEqual(client.get(API_PATH).status_code, 401)
            self.assertEqual(executor.queries, [])
            response = client.get(API_PATH, headers={"Authorization": "Bearer synthetic-token"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertTrue(response.json()["read_only"])

    def test_invalid_missing_unavailable_statuses(self):
        cases = [(API_PATH + "?limit=0", FakeExecutor(), 400),
                 (API_PATH + "/eval-run-9", FakeExecutor({"run": None, "snapshots": []}), 404),
                 (API_PATH, FakeExecutor(ready="false"), 503),
                 (API_PATH, FakeExecutor(failure="private password"), 503)]
        for path, executor, status in cases:
            with self.subTest(status=status), TestClient(self.app(executor)) as client:
                response = client.get(path, headers={"Authorization": "Bearer synthetic-token"})
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.headers["cache-control"], "no-store")
                self.assertNotIn("private password", response.text)

    def test_write_methods_are_denied_without_sql(self):
        executor = FakeExecutor()
        with TestClient(self.app(executor)) as client:
            for method in ("POST", "PUT", "PATCH", "DELETE"):
                response = client.request(method, API_PATH, headers={"Authorization": "Bearer synthetic-token"})
                self.assertEqual(response.status_code, 405)
        self.assertEqual(executor.queries, [])


if __name__ == "__main__":
    unittest.main()
