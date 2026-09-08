"""Required integration checks for an explicitly named disposable CI database."""
import os
import unittest
from urllib.parse import urlsplit

import psycopg
from psycopg.types.json import Jsonb
from stockanalysis.frontend.recommendation_eval_history import API_PATH, EVAL_NAME, EvaluationHistoryError, resolve_evaluation_history


class Reader:
    def __init__(self, connection):
        self.connection = connection

    def execute_scalar(self, sql):
        with self.connection.transaction():
            self.connection.execute("SET LOCAL ROLE eval_history_reader")
            return self.connection.execute(sql).fetchone()[0]

    def execute_non_query(self, sql):
        raise AssertionError("History must not write")


class HistoryPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dsn = os.environ["STOCKANALYSIS_TEST_POSTGRES_DSN"]
        parsed = urlsplit(dsn)
        if parsed.hostname not in {"127.0.0.1", "localhost"} or parsed.path != "/eval_history_test":
            raise RuntimeError("Refusing non-disposable database target")
        cls.connection = psycopg.connect(dsn, autocommit=True)
        cls.connection.execute("CREATE ROLE eval_history_reader NOLOGIN")
        cls.connection.execute("GRANT USAGE ON SCHEMA ai TO eval_history_reader")
        cls.connection.execute("GRANT SELECT ON ai.eval_run, ai.recommendation_eval_snapshot TO eval_history_reader")
        cls.reader = Reader(cls.connection)

        def add_run(name=EVAL_NAME, count=None):
            config = None if count is None else {"snapshot_schema_version": "recommendation-eval-snapshot-v1", "snapshot_count": count}
            return cls.connection.execute(
                "INSERT INTO ai.eval_run (eval_name,dataset_version,provider,model_name,score_json,config_json) VALUES (%s,'synthetic-v1','test','test',%s,%s) RETURNING eval_run_id",
                (name, Jsonb({"zero": 0, "unknown": None}), Jsonb(config) if config is not None else None),
            ).fetchone()[0]

        cls.legacy = add_run()
        cls.empty = add_run(count=0)
        cls.recorded = add_run(count=2)
        cls.other = add_run(name="unrelated_evaluation")
        cls.raw = {"snapshot_schema_version": "recommendation-eval-snapshot-v1",
                   "recommendation": {"recommendation_id": 700001, "total_score": 0},
                   "thesis": {"summary": "평가 당시 판단 <literal>"}, "selected_outcome": None}
        for identifier in (700001, 700002):
            cls.connection.execute(
                """INSERT INTO ai.recommendation_eval_snapshot (
                    eval_run_id,snapshot_schema_version,source_recommendation_id,source_batch_id,
                    primary_symbol,recommendation_action,recommendation_total_score,snapshot_json,snapshot_sha256)
                    VALUES (%s,'recommendation-eval-snapshot-v1',%s,700001,'SYNTHETIC','watch',0,%s,%s)""",
                (cls.recorded, identifier, Jsonb(cls.raw), "a"*64),
            )

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()

    def get(self, path=API_PATH):
        return resolve_evaluation_history(path, source="live", executor=self.reader)

    def detail(self):
        return self.get(API_PATH+f"/eval-run-{self.recorded}")

    def test_01_scoped_list(self):
        rows = self.get()["runs"]
        self.assertEqual([row["eval_run_id"] for row in rows], [str(self.recorded), str(self.empty), str(self.legacy)])
        self.assertEqual([row["snapshot_state"] for row in rows], ["recorded", "recorded_empty", "legacy_unavailable"])

    def test_02_list_cursor(self):
        first = self.get(API_PATH+"?limit=1")
        second = self.get(API_PATH+"?limit=1&before="+first["pagination"]["next_cursor"])
        self.assertEqual(first["runs"][0]["eval_run_id"], str(self.recorded))
        self.assertEqual(second["runs"][0]["eval_run_id"], str(self.empty))

    def test_03_frozen_values_with_absent_sources(self):
        # No source recommendation or thesis is inserted; historical IDs must stand alone.
        data = self.detail()
        self.assertEqual(len(data["snapshots"]), 2)
        self.assertEqual(data["snapshots"][0]["snapshot_json"], self.raw)
        self.assertEqual(data["snapshots"][0]["snapshot_sha256"], "a"*64)
        self.assertIsNone(data["snapshots"][0]["source_outcome_id"])
        self.assertEqual(data["run"]["stored_score"], {"zero": 0, "unknown": None})

    def test_04_detail_cursor(self):
        first = self.get(API_PATH+f"/eval-run-{self.recorded}?limit=1")
        second = self.get(API_PATH+f"/eval-run-{self.recorded}?limit=1&after="+first["pagination"]["next_cursor"])
        self.assertNotEqual(first["snapshots"][0]["snapshot_id"], second["snapshots"][0]["snapshot_id"])
        self.assertFalse(second["pagination"]["has_more"])
        self.assertEqual(second["run"]["snapshot_count"], 2)

    def test_05_other_family_and_missing_id(self):
        for identifier in (self.other, 9223372036854775807):
            with self.subTest(identifier=identifier), self.assertRaises(EvaluationHistoryError) as error:
                self.get(API_PATH+f"/eval-run-{identifier}")
            self.assertEqual(error.exception.code, "FrontendApiPathNotFound")

    def test_06_reader_cannot_write(self):
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with self.connection.transaction():
                self.connection.execute("SET LOCAL ROLE eval_history_reader")
                self.connection.execute("DELETE FROM ai.recommendation_eval_snapshot")
        self.assertEqual(len(self.detail()["snapshots"]), 2)

    def test_07_repeated_reads_preserve_rows(self):
        sql = "SELECT jsonb_agg(to_jsonb(s) ORDER BY snapshot_id) FROM ai.recommendation_eval_snapshot s"
        before = self.connection.execute(sql).fetchone()[0]
        self.detail()
        self.get()
        self.assertEqual(before, self.connection.execute(sql).fetchone()[0])

    def test_08_missing_schema_is_unavailable(self):
        with self.connection.transaction(force_rollback=True):
            self.connection.execute("ALTER TABLE ai.recommendation_eval_snapshot RENAME TO history_test_hidden")
            with self.assertRaises(EvaluationHistoryError) as error:
                self.get()
            self.assertEqual(error.exception.code, "FrontendLiveReadUnavailable")


if __name__ == "__main__":
    unittest.main(verbosity=2)
