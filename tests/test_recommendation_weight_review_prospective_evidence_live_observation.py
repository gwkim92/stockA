from __future__ import annotations

import copy
import json
import unittest

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.recommendation_weight_review_prospective_evidence_foundation import (
    build_recommendation_weight_review_prospective_evidence_foundation,
)
from stockanalysis.operations.recommendation_weight_review_prospective_evidence_live_observation import (
    DATABASE_IDENTITY_CONTRACT_VERSION,
    LiveObservationIntegrityError,
    build_legacy_surface_snapshot,
    build_recommendation_weight_review_prospective_evidence_live_observation,
    normalize_live_observation_database_identity,
    render_live_observation_database_identity_sql,
    render_live_observation_eval_insert_sql,
    render_live_observation_guarded_bundle_lookup_sql,
    render_live_observation_pipeline_run_insert_sql,
    render_live_observation_pipeline_run_status_sql,
    run_recommendation_weight_review_prospective_evidence_live_observation,
)
from tests.recommendation_weight_review_prospective_evidence_fixtures import (
    AUDIT_DATE,
    _bundle,
    _contains_write,
)


class LiveObservationFakeExecutor:
    def __init__(
        self,
        *,
        bundle: dict[str, object] | None = None,
        bundle_after: dict[str, object] | None = None,
        database_identity: dict[str, object] | None = None,
    ) -> None:
        self.bundle = copy.deepcopy(bundle or _bundle())
        self.bundle_after = (
            copy.deepcopy(bundle_after) if bundle_after is not None else None
        )
        self.database_identity = copy.deepcopy(
            database_identity or _database_identity_payload()
        )
        self.bundle_read_count = 0
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        lowered = sql.lower()
        if "live observation database identity v1" in lowered:
            return json.dumps(self.database_identity)
        if "prospective evidence foundation v1 atomic lookup" in lowered:
            self.bundle_read_count += 1
            if self.bundle_after is not None and self.bundle_read_count > 1:
                return json.dumps(self.bundle_after)
            return json.dumps(self.bundle)
        if "insert into ops.pipeline_run" in lowered:
            return "9901"
        if "insert into ai.eval_run" in lowered:
            return "8901"
        if "update ops.pipeline_run" in lowered:
            return "9901"
        raise AssertionError(f"Unexpected scalar SQL: {sql[:200]}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class ProspectiveEvidenceLiveObservationTests(unittest.TestCase):
    def test_database_identity_sql_is_read_only_and_relation_scoped(self) -> None:
        sql = render_live_observation_database_identity_sql()
        lowered = sql.lower()

        self.assertIn("live observation database identity v1", lowered)
        self.assertIn("current_database()", lowered)
        self.assertIn("current_user", lowered)
        self.assertIn("to_regclass('ai.eval_run')", lowered)
        self.assertIn("to_regclass('signal.recommendation')", lowered)
        self.assertFalse(_contains_write(sql))
        self.assertNotIn("database_url", lowered)
        self.assertNotIn("password", lowered)

    def test_database_identity_hash_is_stable_under_relation_order(self) -> None:
        payload = _database_identity_payload()
        reversed_payload = copy.deepcopy(payload)
        relations = reversed(list(reversed_payload["required_relations"].items()))
        reversed_payload["required_relations"] = dict(relations)

        first = normalize_live_observation_database_identity(payload)
        second = normalize_live_observation_database_identity(reversed_payload)

        self.assertTrue(first["complete"])
        self.assertEqual(first["sha256"], second["sha256"])

    def test_guarded_bundle_lookup_asserts_identity_in_same_psql_statement(self) -> None:
        identity = _normalized_database_identity()
        sql = render_live_observation_guarded_bundle_lookup_sql(
            as_of_date=AUDIT_DATE,
            lineage_eval_run_id=501,
            portfolio_feedback_calibration_eval_run_id=601,
            portfolio_name="Long Term Paper",
            database_identity=identity,
        )
        lowered = sql.lower()

        self.assertTrue(lowered.startswith("do $stockanalysis_live_observation_guard$"))
        self.assertIn("current_database() = 'stockanalysis'", lowered)
        self.assertIn("current_user::text = 'stockanalysis_app'", lowered)
        self.assertIn("to_regclass('signal.recommendation') is not null", lowered)
        self.assertIn("eval_run.eval_run_id = 501", lowered)
        self.assertIn("eval_run.eval_run_id = 601", lowered)
        self.assertFalse(_contains_write(sql))

    def test_every_allowed_write_statement_contains_database_identity_guard(self) -> None:
        identity = _normalized_database_identity()
        statements = (
            render_live_observation_pipeline_run_insert_sql(
                config_json={"mode": "test"},
                database_identity=identity,
            ),
            render_live_observation_eval_insert_sql(
                score_json={"status": "live_observation_complete_fresh_read_only"},
                database_identity=identity,
            ),
            render_live_observation_pipeline_run_status_sql(
                run_id=9901,
                status="succeeded",
                database_identity=identity,
            ),
            render_live_observation_pipeline_run_status_sql(
                run_id=9901,
                status="failed",
                database_identity=identity,
                error_summary="test failure",
            ),
        )

        for sql in statements:
            with self.subTest(statement=sql.splitlines()[0]):
                lowered = sql.lower()
                self.assertIn("current_database() = 'stockanalysis'", lowered)
                self.assertIn("current_user::text = 'stockanalysis_app'", lowered)
                self.assertIn(
                    "to_regclass('signal.recommendation') is not null",
                    lowered,
                )
                self.assertTrue(_contains_write(sql))

    def test_legacy_surface_changes_when_recommendation_weight_changes(self) -> None:
        bundle = _bundle()
        foundation = build_recommendation_weight_review_prospective_evidence_foundation(
            as_of_date=AUDIT_DATE,
            bundle=bundle,
        )
        first = build_legacy_surface_snapshot(bundle=bundle, foundation=foundation)

        changed = copy.deepcopy(bundle)
        changed["recommendations"][0]["recommended_weight"] = "0.15"
        changed_foundation = (
            build_recommendation_weight_review_prospective_evidence_foundation(
                as_of_date=AUDIT_DATE,
                bundle=changed,
            )
        )
        second = build_legacy_surface_snapshot(
            bundle=changed,
            foundation=changed_foundation,
        )

        self.assertNotEqual(first["payload_sha256"], second["payload_sha256"])

    def test_environment_mismatch_is_fail_closed(self) -> None:
        bundle = _bundle()
        foundation = build_recommendation_weight_review_prospective_evidence_foundation(
            as_of_date=AUDIT_DATE,
            bundle=bundle,
        )
        surface = build_legacy_surface_snapshot(bundle=bundle, foundation=foundation)

        observation = (
            build_recommendation_weight_review_prospective_evidence_live_observation(
                as_of_date=AUDIT_DATE,
                environment_label="stockA-live",
                expected_database_identity_sha256="0" * 64,
                database_identity_payload=_database_identity_payload(),
                lineage_eval_run_id=501,
                portfolio_feedback_calibration_eval_run_id=601,
                bundle=bundle,
                foundation=foundation,
                legacy_surface_before=surface,
            )
        )

        self.assertEqual(
            observation["status"],
            "live_observation_blocked_environment_mismatch",
        )
        self.assertFalse(observation["database_identity"]["attested"])
        self.assertFalse(observation["weight_mutation_allowed"])
        self.assertFalse(observation["automatic_order_allowed"])
        self.assertFalse(observation["broker_submit_allowed"])

    def test_dry_run_reads_identity_and_exact_bundle_without_writes(self) -> None:
        executor = LiveObservationFakeExecutor()
        expected_sha256 = _database_identity_sha256(executor.database_identity)

        report = run_recommendation_weight_review_prospective_evidence_live_observation(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=AUDIT_DATE,
            lineage_eval_run_id=501,
            portfolio_feedback_calibration_eval_run_id=601,
            environment_label="stockA-live",
            expected_database_identity_sha256=expected_sha256,
            execute=False,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(len(executor.scalar_sql), 2)
        self.assertEqual(executor.bundle_read_count, 1)
        self.assertEqual(executor.non_query_sql, [])
        self.assertTrue(all(not _contains_write(sql) for sql in executor.scalar_sql))
        lookup = executor.scalar_sql[1]
        self.assertIn("do $stockanalysis_live_observation_guard$", lookup.lower())
        self.assertIn("eval_run.eval_run_id = 501", lookup)
        self.assertIn("eval_run.eval_run_id = 601", lookup)
        self.assertTrue(report["observation"]["database_identity"]["attested"])
        self.assertFalse(report["observation"]["proposal_generation_allowed"])
        self.assertEqual(
            report["write_boundary"]["sql_write_statement_count"],
            0,
        )

    def test_execute_writes_only_guarded_pipeline_lifecycle_and_one_eval(self) -> None:
        executor = LiveObservationFakeExecutor()
        expected_sha256 = _database_identity_sha256(executor.database_identity)

        report = run_recommendation_weight_review_prospective_evidence_live_observation(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=AUDIT_DATE,
            lineage_eval_run_id=501,
            portfolio_feedback_calibration_eval_run_id=601,
            environment_label="stockA-live",
            expected_database_identity_sha256=expected_sha256,
            execute=True,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9901)
        self.assertEqual(report["eval_run_id"], 8901)
        self.assertEqual(executor.bundle_read_count, 2)
        self.assertEqual(
            sum(
                "insert into ops.pipeline_run" in sql.lower()
                for sql in executor.scalar_sql
            ),
            1,
        )
        self.assertEqual(
            sum(
                "insert into ai.eval_run" in sql.lower()
                for sql in executor.scalar_sql
            ),
            1,
        )
        self.assertEqual(
            sum(
                "update ops.pipeline_run" in sql.lower()
                for sql in executor.scalar_sql
            ),
            1,
        )
        self.assertEqual(executor.non_query_sql, [])
        all_writes = [sql for sql in executor.scalar_sql if _contains_write(sql)]
        self.assertEqual(len(all_writes), 3)
        self.assertTrue(
            all(
                "current_database() = 'stockanalysis'" in sql.lower()
                for sql in all_writes
            )
        )
        self.assertTrue(
            all(
                "ops.pipeline_run" in sql or "ai.eval_run" in sql
                for sql in all_writes
            )
        )
        self.assertEqual(report["write_boundary"]["pipeline_lifecycle_count"], 1)
        self.assertEqual(report["write_boundary"]["append_only_eval_count"], 1)
        self.assertEqual(
            report["write_boundary"]["sql_write_statement_count"],
            3,
        )
        observation = report["observation"]
        self.assertTrue(observation["legacy_surface"]["unchanged"])
        self.assertTrue(observation["legacy_surface"]["stability_attested"])
        self.assertFalse(observation["manual_review_eligible"])
        self.assertFalse(observation["weight_mutation_allowed"])

    def test_execute_environment_mismatch_performs_no_domain_read_or_write(self) -> None:
        executor = LiveObservationFakeExecutor()

        report = run_recommendation_weight_review_prospective_evidence_live_observation(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=AUDIT_DATE,
            lineage_eval_run_id=501,
            portfolio_feedback_calibration_eval_run_id=601,
            environment_label="wrong-target",
            expected_database_identity_sha256="0" * 64,
            execute=True,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(
            report["write_boundary"]["sql_write_statement_count"],
            0,
        )
        self.assertEqual(len(executor.scalar_sql), 1)
        self.assertEqual(executor.bundle_read_count, 0)
        self.assertEqual(executor.non_query_sql, [])
        self.assertTrue(all(not _contains_write(sql) for sql in executor.scalar_sql))

    def test_missing_required_relation_stops_before_domain_read(self) -> None:
        identity = _database_identity_payload()
        identity["required_relations"]["signal.recommendation"] = False
        executor = LiveObservationFakeExecutor(database_identity=identity)
        expected_sha256 = _database_identity_sha256(identity)

        report = run_recommendation_weight_review_prospective_evidence_live_observation(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=AUDIT_DATE,
            lineage_eval_run_id=501,
            portfolio_feedback_calibration_eval_run_id=601,
            environment_label="incomplete-target",
            expected_database_identity_sha256=expected_sha256,
            execute=False,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(executor.bundle_read_count, 0)
        self.assertEqual(
            report["observation"]["status"],
            "live_observation_incomplete_fail_closed",
        )

    def test_execute_aborts_before_eval_when_surface_drifts(self) -> None:
        changed = _bundle()
        changed["recommendations"][0]["total_score"] = "0.99"
        executor = LiveObservationFakeExecutor(bundle_after=changed)
        expected_sha256 = _database_identity_sha256(executor.database_identity)

        with self.assertRaises(LiveObservationIntegrityError):
            run_recommendation_weight_review_prospective_evidence_live_observation(
                config=RuntimeConfig(psql_command="psql"),
                as_of_date=AUDIT_DATE,
                lineage_eval_run_id=501,
                portfolio_feedback_calibration_eval_run_id=601,
                environment_label="stockA-live",
                expected_database_identity_sha256=expected_sha256,
                execute=True,
                executor=executor,  # type: ignore[arg-type]
            )

        self.assertEqual(
            sum(
                "insert into ops.pipeline_run" in sql.lower()
                for sql in executor.scalar_sql
            ),
            1,
        )
        self.assertEqual(
            sum(
                "insert into ai.eval_run" in sql.lower()
                for sql in executor.scalar_sql
            ),
            0,
        )
        failed_updates = [
            sql
            for sql in executor.scalar_sql
            if "update ops.pipeline_run" in sql.lower()
        ]
        self.assertEqual(len(failed_updates), 1)
        self.assertIn("status = 'failed'", failed_updates[0].lower())
        self.assertIn("current_database() = 'stockanalysis'", failed_updates[0].lower())
        self.assertEqual(executor.non_query_sql, [])

    def test_eval_insert_is_append_only_guarded_and_secret_free(self) -> None:
        sql = render_live_observation_eval_insert_sql(
            score_json={
                "status": "live_observation_complete_fresh_read_only",
                "database_identity": {"sha256": "a" * 64},
            },
            database_identity=_normalized_database_identity(),
        )
        lowered = sql.lower()

        self.assertEqual(lowered.count("insert into"), 1)
        self.assertIn("insert into ai.eval_run", lowered)
        self.assertIn("prospective_evidence_live_observation_v1", lowered)
        self.assertIn("current_database() = 'stockanalysis'", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)
        self.assertNotIn("postgresql://", lowered)
        self.assertNotIn("password", lowered)
        self.assertNotIn("portfolio.position", lowered)
        self.assertNotIn("broker.", lowered)

    def test_exact_source_ids_and_identity_sha_are_required(self) -> None:
        executor = LiveObservationFakeExecutor()
        expected_sha256 = _database_identity_sha256(executor.database_identity)

        for kwargs in (
            {"lineage_eval_run_id": 0},
            {"portfolio_feedback_calibration_eval_run_id": 0},
            {"expected_database_identity_sha256": "not-a-sha"},
            {"environment_label": ""},
        ):
            arguments = {
                "config": RuntimeConfig(psql_command="psql"),
                "as_of_date": AUDIT_DATE,
                "lineage_eval_run_id": 501,
                "portfolio_feedback_calibration_eval_run_id": 601,
                "environment_label": "stockA-live",
                "expected_database_identity_sha256": expected_sha256,
                "execute": False,
                "executor": executor,
            }
            arguments.update(kwargs)
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                run_recommendation_weight_review_prospective_evidence_live_observation(
                    **arguments  # type: ignore[arg-type]
                )


def _database_identity_payload() -> dict[str, object]:
    return {
        "contract_version": DATABASE_IDENTITY_CONTRACT_VERSION,
        "database_name": "stockanalysis",
        "role_name": "stockanalysis_app",
        "server_version_num": "160004",
        "server_address": "10.0.0.10",
        "server_port": 5432,
        "required_relations": {
            "signal.recommendation": True,
            "ai.eval_run": True,
            "portfolio.portfolio": True,
            "performance.recommendation_outcome": True,
            "ops.pipeline_run": True,
            "signal.recommendation_score_component": True,
            "signal.recommendation_batch": True,
        },
    }


def _normalized_database_identity() -> dict[str, object]:
    return normalize_live_observation_database_identity(_database_identity_payload())


def _database_identity_sha256(payload: dict[str, object]) -> str:
    normalized = normalize_live_observation_database_identity(payload)
    return str(normalized["sha256"])


if __name__ == "__main__":
    unittest.main()
