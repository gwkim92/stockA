"""Opt-in CI only. Uses a fixed loopback disposable DB, never a runtime DSN."""
from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from stockanalysis.frontend.db_pool import PsycopgPoolExecutor
from stockanalysis.frontend.recommendation_eval_history import API_PATH, EVAL_NAME, MAX_ID, EvaluationHistoryError, resolve_evaluation_history

DSN = "host=127.0.0.1 port=55439 dbname=stockanalysis_eval_history_test user=postgres password=postgres connect_timeout=5"
VERSION = "recommendation-eval-snapshot-v1"


class EvaluationHistoryPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("STOCKANALYSIS_EVAL_HISTORY_CI") != "1":
            raise unittest.SkipTest("Requires the dedicated disposable evaluation-history CI service.")
        cls.admin = psycopg.connect(DSN, autocommit=True)
        cls.addClassCleanup(cls.admin.close)
        if cls.admin.execute("select pg_catalog.to_regnamespace('ai')").fetchone()[0] is not None:
            raise RuntimeError("Refusing to initialize a database with an existing ai schema.")
        migrations = sorted((Path(__file__).resolve().parents[1] / "db" / "migrations").glob("*.sql"))
        if not any(p.name == "0035_recommendation_eval_persistence.sql" for p in migrations):
            raise RuntimeError("The real persistence migration is required.")
        for migration in migrations:
            cls.admin.execute(migration.read_text(encoding="utf-8"))
        print(f"Applied {len(migrations)} checked-in migrations to the disposable database.", flush=True)
        cls.admin.execute("create role eval_history_test_reader nologin nosuperuser nocreatedb nocreaterole")
        cls.admin.execute("grant usage on schema ai to eval_history_test_reader")
        cls.admin.execute("grant select on ai.eval_run, ai.recommendation_eval_snapshot to eval_history_test_reader")
        cls.pool = ConnectionPool(DSN, min_size=1, max_size=1, open=False, timeout=5,
                                 kwargs={"options": "-c role=eval_history_test_reader -c default_transaction_read_only=on -c statement_timeout=5000"})
        cls.addClassCleanup(cls.pool.close)
        cls.pool.open()
        cls.pool.wait(timeout=5)
        cls.reader = PsycopgPoolExecutor(cls.pool)

    def setUp(self):
        self.admin.execute("truncate ai.recommendation_eval_snapshot, ai.eval_run restart identity cascade")

    def insert_run(self, *, count=None, name=EVAL_NAME, identifier=None):
        config = None if count is None else {"snapshot_count": count, "snapshot_schema_version": VERSION}
        values = (name, "synthetic-history-test", "test", "test-model", Jsonb({"alpha": None}), Jsonb(config))
        if identifier is None:
            return self.admin.execute("insert into ai.eval_run (eval_name, dataset_version, provider, model_name, score_json, config_json) values (%s,%s,%s,%s,%s,%s) returning eval_run_id", values).fetchone()[0]
        return self.admin.execute("insert into ai.eval_run (eval_run_id, eval_name, dataset_version, provider, model_name, score_json, config_json) overriding system value values (%s,%s,%s,%s,%s,%s,%s) returning eval_run_id", (identifier, *values)).fetchone()[0]

    def insert_snapshot(self, run_id, recommendation_id=100, payload=None):
        raw = payload or {"recommendation": {"recommendation_id": recommendation_id, "total_score": 0},
                          "thesis": {"invalidation_conditions": ["frozen historical condition"]}, "selected_outcome": None}
        return self.admin.execute("""insert into ai.recommendation_eval_snapshot
            (eval_run_id, snapshot_schema_version, source_recommendation_id, source_batch_id,
             primary_symbol, recommendation_action, recommendation_total_score, snapshot_json, snapshot_sha256)
            values (%s,%s,%s,1,'SYNTHETIC','watch',0,%s,%s) returning snapshot_id""",
            (run_id, VERSION, recommendation_id, Jsonb(raw), "a" * 64)).fetchone()[0]

    def read(self, suffix=""):
        return resolve_evaluation_history(API_PATH + suffix, source="live", executor=self.reader)

    def test_empty_database_is_known_empty(self):
        result = self.read()
        self.assertEqual(result["runs"], [])
        self.assertFalse(result["pagination"]["has_more"])

    def test_run_family_isolation_and_keyset(self):
        first = self.insert_run()
        self.insert_run(name="unrelated_news_evaluation")
        last = self.insert_run(count=0)
        page = self.read("?limit=1")
        self.assertEqual([r["eval_run_id"] for r in page["runs"]], [str(last)])
        self.assertEqual(page["runs"][0]["snapshot_state"], "recorded_empty")
        next_page = self.read(f"?limit=1&before={page['pagination']['next_cursor']}")
        self.assertEqual([r["eval_run_id"] for r in next_page["runs"]], [str(first)])
        self.assertEqual(next_page["runs"][0]["snapshot_state"], "legacy_unavailable")
        self.assertFalse(next_page["pagination"]["has_more"])

    def test_detail_isolation_pagination_and_raw_null_zero(self):
        selected = self.insert_run(count=2)
        other = self.insert_run(count=1)
        first = self.insert_snapshot(selected, 100)
        self.insert_snapshot(other, 200)
        last = self.insert_snapshot(selected, 101)
        page = self.read(f"/eval-run-{selected}?limit=1")
        self.assertEqual([s["snapshot_id"] for s in page["snapshots"]], [str(first)])
        self.assertEqual(page["run"]["snapshot_count"], 2)
        self.assertEqual(page["run"]["snapshot_state"], "recorded")
        self.assertIsNone(page["snapshots"][0]["snapshot_json"]["selected_outcome"])
        self.assertEqual(page["snapshots"][0]["snapshot_json"]["recommendation"]["total_score"], 0)
        page = self.read(f"/eval-run-{selected}?limit=1&after={first}")
        self.assertEqual([s["snapshot_id"] for s in page["snapshots"]], [str(last)])
        self.assertFalse(page["pagination"]["has_more"])

    def test_bigint_identity_is_preserved(self):
        self.insert_run(count=1, identifier=MAX_ID)
        self.insert_snapshot(MAX_ID, MAX_ID)
        result = self.read(f"/eval-run-{MAX_ID}")
        self.assertEqual(result["run"]["eval_run_id"], str(MAX_ID))
        self.assertEqual(result["snapshots"][0]["source_recommendation_id"], str(MAX_ID))

    def test_missing_and_wrong_family_runs_are_not_replaced(self):
        other = self.insert_run(name="another_eval")
        self.insert_run(count=0)
        for identifier in (other, 999999):
            with self.subTest(identifier=identifier), self.assertRaises(EvaluationHistoryError) as raised:
                self.read(f"/eval-run-{identifier}")
            self.assertEqual(raised.exception.code, "FrontendApiPathNotFound")

    def test_missing_children_are_not_reported_as_recorded_empty(self):
        identifier = self.insert_run(count=1)
        result = self.read(f"/eval-run-{identifier}")
        self.assertEqual(result["run"]["snapshot_state"], "count_mismatch")
        self.assertEqual(result["run"]["expected_snapshot_count"], 1)
        self.assertEqual(result["run"]["snapshot_count"], 0)

    def test_read_role_has_no_source_or_write_permissions_and_reads_do_not_mutate(self):
        identifier = self.insert_run(count=1)
        self.insert_snapshot(identifier)
        before = self.admin.execute("select row_to_json(s)::text from ai.recommendation_eval_snapshot s").fetchall()
        self.assertEqual(self.reader.execute_scalar("select current_user"), "eval_history_test_reader")
        self.assertEqual(self.reader.execute_scalar("show transaction_read_only"), "on")
        self.read(f"/eval-run-{identifier}")
        with self.assertRaises(psycopg.Error):
            self.reader.execute_scalar("select count(*) from signal.recommendation")
        with self.assertRaises(psycopg.Error):
            self.reader.execute_non_query("delete from ai.recommendation_eval_snapshot")
        after = self.admin.execute("select row_to_json(s)::text from ai.recommendation_eval_snapshot s").fetchall()
        self.assertEqual(before, after)
        self.assertEqual(self.read(f"/eval-run-{identifier}")["run"]["snapshot_state"], "recorded")

    def test_actual_mutable_recommendation_update_and_delete_do_not_rewrite_history(self):
        self.admin.execute("insert into ref.market values ('TEST','Synthetic','US','USD','UTC',true)")
        exchange = self.admin.execute("insert into ref.exchange (market_code,mic_code,name,timezone) values ('TEST','XTST','Synthetic','UTC') returning exchange_id").fetchone()[0]
        issuer = self.admin.execute("insert into ref.issuer (legal_name,display_name,country_code,issuer_type) values ('Synthetic','Synthetic','US','company') returning issuer_id").fetchone()[0]
        instrument = self.admin.execute("insert into ref.instrument (issuer_id,exchange_id,market_code,primary_symbol,instrument_type,currency_code,name) values (%s,%s,'TEST','SYNTHETIC','equity','USD','Synthetic') returning instrument_id", (issuer, exchange)).fetchone()[0]
        batch = self.admin.execute("insert into signal.recommendation_batch (as_of_date,market_code,strategy_name,horizon_type) values ('2026-01-01','TEST','synthetic','long') returning batch_id").fetchone()[0]
        recommendation = self.admin.execute("insert into signal.recommendation (batch_id,instrument_id,bucket,action,rank_position,total_score) values (%s,%s,'test','watch',1,0) returning recommendation_id", (batch, instrument)).fetchone()[0]
        identifier = self.insert_run(count=1)
        self.insert_snapshot(identifier, recommendation)
        before = self.read(f"/eval-run-{identifier}")["snapshots"]
        self.admin.execute("update signal.recommendation set total_score=99, action='changed' where recommendation_id=%s", (recommendation,))
        self.assertEqual(self.read(f"/eval-run-{identifier}")["snapshots"], before)
        self.admin.execute("delete from signal.recommendation where recommendation_id=%s", (recommendation,))
        self.assertEqual(self.read(f"/eval-run-{identifier}")["snapshots"], before)

    def test_missing_snapshot_table_is_unavailable_not_empty(self):
        self.admin.execute("alter table ai.recommendation_eval_snapshot rename to history_temporarily_unavailable")
        try:
            with self.assertRaises(EvaluationHistoryError) as raised:
                self.read()
            self.assertEqual(raised.exception.code, "FrontendLiveReadUnavailable")
        finally:
            self.admin.execute("alter table ai.history_temporarily_unavailable rename to recommendation_eval_snapshot")

    def test_explicit_comparison_hash_drift_later_horizon_and_deleted_sources(self):
        from stockanalysis.frontend.recommendation_eval_comparison import resolve_evaluation_comparison
        from stockanalysis.operations.recommendation_eval_persistence import canonical_snapshot_json
        import hashlib
        self.admin.execute("insert into ref.market values ('CMP','Comparison','US','USD','UTC',true)")
        issuer = self.admin.execute("insert into ref.issuer (legal_name,display_name,country_code,issuer_type) values ('Comparison','Comparison','US','company') returning issuer_id").fetchone()[0]
        exchange = self.admin.execute("insert into ref.exchange (market_code,mic_code,name,timezone) values ('CMP','XCMP','Comparison','UTC') returning exchange_id").fetchone()[0]
        instrument = self.admin.execute("insert into ref.instrument (issuer_id,exchange_id,market_code,primary_symbol,instrument_type,currency_code,name) values (%s,%s,'CMP','SYNTHETIC','equity','USD','Comparison') returning instrument_id", (issuer,exchange)).fetchone()[0]
        batch = self.admin.execute("insert into signal.recommendation_batch (as_of_date,market_code,strategy_name,horizon_type) values ('2026-01-01','CMP','comparison','long') returning batch_id").fetchone()[0]
        recommendation = self.admin.execute("insert into signal.recommendation (batch_id,instrument_id,bucket,action,rank_position,total_score) values (%s,%s,'test','watch',1,0) returning recommendation_id", (batch, instrument)).fetchone()[0]
        identifier = self.insert_run(count=1)
        self.admin.execute("update ai.eval_run set as_of_date='2026-01-15',horizon_days=30 where eval_run_id=%s", (identifier,))
        raw = {'recommendation': {'recommendation_id': recommendation, 'action':'watch','total_score':0,'status':'active','recommended_weight':None,'thesis_id':None}, 'thesis':None, 'selected_outcome':None}
        snapshot = self.insert_snapshot(identifier, recommendation, raw)
        digest = hashlib.sha256(canonical_snapshot_json(raw).encode()).hexdigest()
        self.admin.execute("update ai.recommendation_eval_snapshot set snapshot_sha256=%s where snapshot_id=%s", (digest,snapshot))
        self.admin.execute("create role eval_comparison_reader nologin")
        self.admin.execute("grant usage on schema ai,signal,ref,performance to eval_comparison_reader")
        self.admin.execute("grant select on ai.eval_run,ai.recommendation_eval_snapshot,signal.recommendation,signal.investment_thesis,ref.instrument,performance.recommendation_outcome to eval_comparison_reader")
        with ConnectionPool(DSN, min_size=1, max_size=1, kwargs={'options':'-c role=eval_comparison_reader -c default_transaction_read_only=on'}) as pool:
            reader = PsycopgPoolExecutor(pool)
            def compare(executor=reader):
                return resolve_evaluation_comparison(f'/api/recommendation-evaluation-comparisons/eval-run-{identifier}',source='live',executor=executor)
            before = self.read(f'/eval-run-{identifier}')
            result = compare()
            self.assertEqual(result['comparisons'][0]['integrity'], 'verified')
            self.assertEqual(result['comparisons'][0]['status'], 'unchanged')
            self.admin.execute("update signal.recommendation set total_score=99,action='buy' where recommendation_id=%s", (recommendation,))
            for end,horizon,alpha in [('2026-01-10',30,0.8),('2026-02-01',30,0),('2026-03-01',90,0.9),('2099-01-01',30,0.7)]:
                self.admin.execute("insert into performance.recommendation_outcome (recommendation_id,measurement_start_date,measurement_end_date,horizon_days,entry_price,exit_price,absolute_return_pct,alpha_pct,outcome_label) values (%s,'2026-01-01',%s,%s,100,100,0,%s,'test')",(recommendation,end,horizon,alpha))
            comparison=compare()['comparisons'][0]
            self.assertEqual(comparison['status'], 'changed')
            self.assertEqual(comparison['later_outcome']['alpha_pct'],0)
            self.assertEqual(comparison['later_outcome']['measurement_end_date'],'2026-02-01')
            self.assertEqual(self.read(f'/eval-run-{identifier}'), before)
            denied=compare(self.reader)
            self.assertEqual(denied['comparison_status'],'unavailable')
            self.assertEqual(denied['comparisons'][0]['integrity'],'verified')
            with self.assertRaises(psycopg.Error): reader.execute_non_query('delete from ai.recommendation_eval_snapshot')
            self.admin.execute('delete from signal.recommendation where recommendation_id=%s',(recommendation,))
            self.assertEqual(compare()['comparisons'][0]['status'],'source_missing')
            self.admin.execute("update ai.recommendation_eval_snapshot set snapshot_json=jsonb_set(snapshot_json,'{recommendation,total_score}','1') where snapshot_id=%s",(snapshot,))
            self.assertEqual(compare()['comparisons'][0]['integrity'],'mismatch')


if __name__ == "__main__":
    unittest.main()
