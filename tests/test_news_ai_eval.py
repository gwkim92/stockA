from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.news.eval import (
    DEFAULT_EVAL_NAME,
    load_news_ai_eval_dataset,
    render_news_ai_eval_run_insert_sql,
    run_news_ai_eval,
    score_news_ai_eval_dataset,
)


class FakeEvalWriteExecutor:
    def __init__(self, *, fail_eval_insert: bool = False) -> None:
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []
        self.fail_eval_insert = fail_eval_insert

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("insert into ops.pipeline_run"):
            return "7201"
        if sql.startswith("insert into ai.eval_run"):
            if self.fail_eval_insert:
                raise RuntimeError("eval insert failed")
            return "8101"
        raise AssertionError(f"Unexpected SQL: {sql[:80]}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class NewsAiEvalTests(unittest.TestCase):
    def test_fixture_dataset_scores_core_quality_targets(self) -> None:
        dataset = load_news_ai_eval_dataset()

        score = score_news_ai_eval_dataset(dataset)
        metrics = score["metrics"]

        self.assertTrue(score["overall_pass"])
        self.assertEqual(metrics["case_count"], 5)
        self.assertEqual(metrics["failed_case_count"], 0)
        self.assertEqual(metrics["theme_precision"], 1.0)
        self.assertEqual(metrics["direct_ticker_grounding_precision"], 1.0)
        self.assertEqual(metrics["macro_only_false_ticker_count"], 0)
        self.assertEqual(metrics["quantum_energy_misclassification_count"], 0)
        self.assertEqual(metrics["korean_translation_availability"], 1.0)

    def test_eval_case_results_show_blocked_bad_direct_symbols(self) -> None:
        dataset = load_news_ai_eval_dataset()
        score = score_news_ai_eval_dataset(dataset)
        by_case = {str(item["case_id"]): item for item in score["case_results"]}

        macro_case = by_case["macro_fed_rates_no_direct_ticker"]
        quantum_case = by_case["quantum_policy_not_energy"]

        self.assertEqual(macro_case["accepted_direct_symbols"], [])
        self.assertEqual(macro_case["blocked_symbols_accepted"], [])
        self.assertGreaterEqual(macro_case["rejected_impact_count"], 1)
        self.assertEqual(quantum_case["accepted_theme_codes"], ["QUANTUM_COMPUTING_POLICY"])
        self.assertEqual(quantum_case["accepted_direct_symbols"], ["QUBT"])
        self.assertEqual(quantum_case["forbidden_symbol_hits"], [])

    def test_render_eval_insert_sql_uses_ai_eval_run(self) -> None:
        sql = render_news_ai_eval_run_insert_sql(
            eval_name=DEFAULT_EVAL_NAME,
            dataset_version="news-ai-eval-v1",
            provider="fixture",
            model_name="fixture-model",
            score_json={"overall_pass": True},
        )

        self.assertIn("insert into ai.eval_run", sql)
        self.assertIn("'news_ai_extraction_quality'", sql)
        self.assertIn("'news-ai-eval-v1'", sql)
        self.assertIn("'fixture-model'", sql)
        self.assertEqual(sql.count("'fixture-model'"), 1)

    def test_run_news_ai_eval_execute_records_pipeline_and_eval_run(self) -> None:
        executor = FakeEvalWriteExecutor()

        report = run_news_ai_eval(
            config=RuntimeConfig(psql_command="psql"),
            execute=True,
            executor=executor,  # type: ignore[arg-type]
            generated_at=datetime(2026, 5, 24, tzinfo=timezone.utc),
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 7201)
        self.assertEqual(report["eval_run_id"], 8101)
        self.assertTrue(report["score"]["overall_pass"])
        self.assertEqual(len(executor.scalar_sql), 2)
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[0])
        self.assertIn("'news_ai_extraction_quality'", executor.scalar_sql[0])
        self.assertIn("'ai'", executor.scalar_sql[0])
        self.assertIn("insert into ai.eval_run", executor.scalar_sql[1])
        self.assertEqual(len(executor.non_query_sql), 1)
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])
        self.assertIn("where run_id = 7201", executor.non_query_sql[0])

    def test_run_news_ai_eval_execute_marks_pipeline_failed_when_eval_insert_fails(self) -> None:
        executor = FakeEvalWriteExecutor(fail_eval_insert=True)

        with self.assertRaises(RuntimeError):
            run_news_ai_eval(
                config=RuntimeConfig(psql_command="psql"),
                execute=True,
                executor=executor,  # type: ignore[arg-type]
                generated_at=datetime(2026, 5, 24, tzinfo=timezone.utc),
            )

        self.assertEqual(len(executor.scalar_sql), 2)
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[0])
        self.assertIn("insert into ai.eval_run", executor.scalar_sql[1])
        self.assertEqual(len(executor.non_query_sql), 1)
        self.assertIn("status = 'failed'", executor.non_query_sql[0])
        self.assertIn("'eval insert failed'", executor.non_query_sql[0])
        self.assertIn("where run_id = 7201", executor.non_query_sql[0])

    def test_load_dataset_rejects_empty_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "dataset.json"
            path.write_text(json.dumps({"dataset_version": "bad", "cases": []}), encoding="utf-8")

            with self.assertRaises(ValueError):
                load_news_ai_eval_dataset(path)


if __name__ == "__main__":
    unittest.main()
