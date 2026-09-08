"""Contract checks use synthetic records only; never access production sources."""
import copy
import json
import unittest
from unittest.mock import patch

from stockanalysis.frontend.api_adapter import FrontendApiAdapterError, resolve_frontend_response
from stockanalysis.frontend.recommendation_eval_history import (
    API_PATH, EVAL_NAME, MAX_ID, SCHEMA_READINESS_SQL, EvaluationHistoryError,
    HistoryRequest, parse_evaluation_history_request, render_evaluation_history_sql,
    resolve_evaluation_history,
)


def saved_run(identifier="8", count=1, expected=1):
    return {"eval_run_id": identifier, "eval_name": EVAL_NAME,
            "snapshot_count": count, "stored_score": {"unknown": None, "zero": 0},
            "stored_config": {"snapshot_schema_version": "recommendation-eval-snapshot-v1", "snapshot_count": expected}}


def saved_snapshot(identifier="2", run_id="8"):
    return {"snapshot_id": identifier, "eval_run_id": run_id,
            "source_recommendation_id": "91", "source_batch_id": "81",
            "source_thesis_id": None, "source_outcome_id": None,
            "snapshot_sha256": "a" * 64,
            "snapshot_json": {"thesis": {"summary": "평가 당시 판단 <literal>"}, "selected_outcome": None, "zero": 0}}


class ScalarOnlyExecutor:
    def __init__(self, payload=None, ready="true", error=None):
        self.payload = {"runs": []} if payload is None else payload
        self.ready, self.error, self.calls = ready, error, []

    def execute_scalar(self, sql):
        self.calls.append(sql)
        if self.error:
            raise self.error
        return self.ready if sql == SCHEMA_READINESS_SQL else json.dumps(self.payload)

    def execute_non_query(self, sql):
        raise AssertionError("History reader attempted a write")


class ReaderContractTests(unittest.TestCase):
    def read(self, payload, path=API_PATH):
        executor = ScalarOnlyExecutor(payload)
        result = resolve_evaluation_history(path, source="live", executor=executor)
        self.assertEqual(len(executor.calls), 2)
        self.assertTrue(result["read_only"])
        self.assertFalse(result["broker_submit_allowed"])
        return result

    def test_default_and_keyset_selectors(self):
        self.assertEqual(parse_evaluation_history_request(API_PATH), HistoryRequest())
        self.assertEqual(parse_evaluation_history_request(API_PATH+"?limit=2&before=9"), HistoryRequest(None, 2, 9))
        self.assertEqual(parse_evaluation_history_request(API_PATH+"/eval-run-8?limit=2&after=9"), HistoryRequest(8, 2, 9))

    def test_positive_bigint_boundary(self):
        self.assertEqual(parse_evaluation_history_request(API_PATH+f"?before={MAX_ID}").cursor, MAX_ID)
        for value in (str(MAX_ID+1), "0", "01", "-1", "1.5", "1e2", "true", "١", "1%27", "1"*200):
            with self.subTest(value=value), self.assertRaises(EvaluationHistoryError):
                parse_evaluation_history_request(API_PATH+"?before="+value)

    def test_rejects_ambiguous_queries_before_io(self):
        for suffix in ("?limit=0", "?limit=101", "?limit=1&limit=2", "?limit=", "?limit", "?after=1", "?other=1", "?before=1&before=2"):
            executor = ScalarOnlyExecutor()
            with self.subTest(suffix=suffix), self.assertRaises(EvaluationHistoryError):
                resolve_evaluation_history(API_PATH+suffix, source="live", executor=executor)
            self.assertEqual(executor.calls, [])

    def test_invalid_paths_and_absolute_urls(self):
        for path in (API_PATH+"/", API_PATH+"/8", API_PATH+"/eval-run-01", API_PATH+"/eval-run-8/x", API_PATH+"#fragment", "https://example.test"+API_PATH):
            with self.subTest(path=path), self.assertRaises(EvaluationHistoryError):
                parse_evaluation_history_request(path)

    def test_direct_python_callers_cannot_inject_sql(self):
        for request in (HistoryRequest(limit=True), HistoryRequest(limit=101), HistoryRequest(eval_run_id=True), HistoryRequest(cursor="1; DELETE")):
            with self.subTest(request=request), self.assertRaises(EvaluationHistoryError):
                render_evaluation_history_sql(request)

    def test_sql_only_reads_frozen_tables(self):
        for request in (HistoryRequest(), HistoryRequest(8, 1, 2)):
            sql = render_evaluation_history_sql(request)
            self.assertEqual(sql.count(";"), 1)
            self.assertNotRegex(sql.lower(), r"\b(insert|update|delete|truncate|alter|drop|create|grant|call|copy)\b")
            for forbidden in ("signal.", "performance.", "ref.instrument", "ops."):
                self.assertNotIn(forbidden, sql)
            self.assertIn(EVAL_NAME, sql)

    def test_list_page_has_no_duplicates_and_uses_last_visible_cursor(self):
        result = self.read({"runs": [saved_run("8"), saved_run("7"), saved_run("6")]}, API_PATH+"?limit=2")
        self.assertEqual([row["eval_run_id"] for row in result["runs"]], ["8", "7"])
        self.assertEqual(result["pagination"]["next_cursor"], "7")
        self.assertEqual(result["pagination"]["returned_count"], 2)

    def test_legacy_empty_and_count_mismatch_are_distinct(self):
        legacy = saved_run("6", 0, None)
        legacy["stored_config"] = None
        result = self.read({"runs": [saved_run("9"), saved_run("8", 0, 0), saved_run("7", 1, 2), legacy]})
        self.assertEqual([row["snapshot_state"] for row in result["runs"]], ["recorded", "recorded_empty", "count_mismatch", "legacy_unavailable"])

    def test_empty_history_is_success(self):
        result = self.read({"runs": []})
        self.assertEqual(result["runs"], [])
        self.assertFalse(result["pagination"]["has_more"])
        self.assertIsNone(result["pagination"]["next_cursor"])

    def test_snapshot_preserves_original_values_without_mutation(self):
        payload = {"run": saved_run(), "snapshots": [saved_snapshot()]}
        original = copy.deepcopy(payload)
        result = self.read(payload, API_PATH+"/eval-run-8")
        self.assertEqual(result["snapshots"], original["snapshots"])
        self.assertEqual(payload, original)
        self.assertEqual(result["snapshot_hash_verification"], "not_performed")
        self.assertEqual(result["history_basis"], "evaluation_time_snapshot_not_recommendation_creation_time")

    def test_detail_page_cursor(self):
        result = self.read({"run": saved_run(count=2, expected=2), "snapshots": [saved_snapshot("3"), saved_snapshot("4")]}, API_PATH+"/eval-run-8?limit=1&after=2")
        self.assertEqual(result["pagination"]["next_cursor"], "3")
        self.assertEqual(result["pagination"]["cursor_parameter"], "after")
        self.assertEqual(result["run"]["snapshot_count"], 2)

    def test_missing_run_is_not_an_empty_snapshot(self):
        with self.assertRaises(EvaluationHistoryError) as error:
            self.read({"run": None, "snapshots": []}, API_PATH+"/eval-run-8")
        self.assertEqual(error.exception.code, "FrontendApiPathNotFound")

    def test_snapshot_from_another_run_is_rejected(self):
        with self.assertRaises(EvaluationHistoryError) as error:
            self.read({"run": saved_run(), "snapshots": [saved_snapshot(run_id="9")]}, API_PATH+"/eval-run-8")
        self.assertEqual(error.exception.code, "FrontendLiveReadUnavailable")

    def test_malformed_stored_ids_are_server_errors(self):
        for payload in ({"runs": [saved_run("01")]}, {"runs": [saved_run("8"), saved_run("8")]}, {"runs": [saved_run("7"), saved_run("8")]}):
            with self.subTest(payload=payload), self.assertRaises(EvaluationHistoryError) as error:
                self.read(payload)
            self.assertEqual(error.exception.code, "FrontendLiveReadUnavailable")

    def test_schema_unavailable_stops_before_data_query(self):
        executor = ScalarOnlyExecutor(ready="false")
        with self.assertRaises(EvaluationHistoryError) as error:
            resolve_evaluation_history(API_PATH, source="live", executor=executor)
        self.assertEqual(error.exception.code, "FrontendLiveReadUnavailable")
        self.assertEqual(len(executor.calls), 1)

    def test_driver_failure_does_not_leak_secrets(self):
        with self.assertRaises(EvaluationHistoryError) as error:
            resolve_evaluation_history(API_PATH, source="live", executor=ScalarOnlyExecutor(error=RuntimeError("password=synthetic-secret")))
        self.assertNotIn("synthetic-secret", str(error.exception))
        self.assertEqual(error.exception.code, "FrontendLiveReadUnavailable")

    def test_fixture_cannot_manufacture_history(self):
        executor = ScalarOnlyExecutor()
        with self.assertRaises(EvaluationHistoryError):
            resolve_evaluation_history(API_PATH, source="fixture", executor=executor)
        self.assertEqual(executor.calls, [])

    def test_auto_does_not_fall_back_to_fixture(self):
        with patch("stockanalysis.frontend.recommendation_eval_history.RuntimeConfig.from_env") as config:
            config.return_value.psql_command = None
            with self.assertRaises(EvaluationHistoryError):
                resolve_evaluation_history(API_PATH, source="auto")

    def test_adapter_avoids_mutable_live_reader(self):
        with patch("stockanalysis.frontend.api_adapter._resolve_live_frontend_response", side_effect=AssertionError("mutable reader called")):
            result = resolve_frontend_response(API_PATH, source="live", executor=ScalarOnlyExecutor())
        self.assertEqual(result["runs"], [])

    def test_adapter_preserves_validation_error_code(self):
        with self.assertRaises(FrontendApiAdapterError) as error:
            resolve_frontend_response(API_PATH+"?limit=101", source="live", executor=ScalarOnlyExecutor())
        self.assertEqual(error.exception.code, "FrontendPaginationInvalid")

    def test_unrelated_api_dispatch_is_unchanged(self):
        with patch("stockanalysis.frontend.api_adapter._resolve_live_frontend_response", return_value={"data": "existing"}) as previous:
            self.assertEqual(resolve_frontend_response("/api/stocks/AAPL", source="live"), {"data": "existing"})
        previous.assert_called_once()


class HttpContractTests(unittest.TestCase):
    def client(self, executor):
        from fastapi.testclient import TestClient
        from stockanalysis.frontend.api_server import create_app
        from stockanalysis.frontend.runtime_policy import FrontendRuntimePolicy
        policy = FrontendRuntimePolicy(profile="local", source="live", auth_mode="read-token", read_token="synthetic-token")
        return TestClient(create_app(runtime_policy=policy, executor=executor))

    def test_auth_precedes_database_access(self):
        executor = ScalarOnlyExecutor()
        with self.client(executor) as client:
            self.assertEqual(client.get(API_PATH).status_code, 401)
            self.assertEqual(client.get(API_PATH, headers={"Authorization": "Bearer wrong"}).status_code, 401)
        self.assertEqual(executor.calls, [])

    def test_authorized_get_is_uncached(self):
        with self.client(ScalarOnlyExecutor()) as client:
            response = client.get(API_PATH, headers={"Authorization": "Bearer synthetic-token"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertTrue(response.json()["read_only"])

    def test_invalid_query_is_400_before_io(self):
        executor = ScalarOnlyExecutor()
        with self.client(executor) as client:
            response = client.get(API_PATH+"?limit=1&limit=2", headers={"Authorization": "Bearer synthetic-token"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(executor.calls, [])

    def test_missing_eval_is_404(self):
        with self.client(ScalarOnlyExecutor({"run": None, "snapshots": []})) as client:
            response = client.get(API_PATH+"/eval-run-8", headers={"Authorization": "Bearer synthetic-token"})
        self.assertEqual(response.status_code, 404)

    def test_missing_schema_is_503(self):
        with self.client(ScalarOnlyExecutor(ready="false")) as client:
            response = client.get(API_PATH, headers={"Authorization": "Bearer synthetic-token"})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("runs", response.json())

    def test_all_write_methods_are_blocked(self):
        executor = ScalarOnlyExecutor()
        with self.client(executor) as client:
            for method in ("POST", "PUT", "PATCH", "DELETE"):
                with self.subTest(method=method):
                    response = client.request(method, API_PATH, headers={"Authorization": "Bearer synthetic-token"})
                    self.assertEqual(response.status_code, 405)
        self.assertEqual(executor.calls, [])


if __name__ == "__main__":
    unittest.main()
