from __future__ import annotations

import json
import unittest
from datetime import date
from decimal import Decimal

from stockanalysis.performance.outcome import (
    PerformanceOutcomeCandidate,
    PerformanceOutcomeScheduleCandidate,
    build_performance_outcome_rows,
    load_performance_outcome_candidates,
    load_performance_outcome_schedule_candidates,
    render_performance_outcome_candidate_lookup_sql,
    render_performance_outcome_schedule_candidate_lookup_sql,
    render_performance_outcome_upsert_sql,
    resolve_performance_measurement_dates,
    resolve_performance_schedule_horizon_days,
    run_performance_outcome_batch_bootstrap,
    run_performance_outcome_bootstrap,
    run_performance_outcome_schedule_bootstrap,
)


class FakeExecutor:
    def __init__(
        self,
        *,
        run_id: int = 8001,
        fail_on_upsert: bool = False,
        with_benchmark_prices: bool = False,
    ) -> None:
        self.run_id = run_id
        self._next_run_id = run_id
        self.fail_on_upsert = fail_on_upsert
        self.with_benchmark_prices = with_benchmark_prices
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- performance outcome schedule candidate lookup"):
            return json.dumps(
                [
                    {
                        "batch_id": 2001,
                        "as_of_date": "2024-11-01",
                        "market_code": "US",
                        "strategy_name": "long_term_core",
                        "horizon_type": "long_term",
                        "universe_version": "fixture-v1",
                        "horizon_day": 31,
                        "measurement_end_date": "2024-12-02",
                        "active_recommendation_count": 1,
                        "existing_outcome_count": 0,
                    }
                ]
            )
        if sql.startswith("-- performance outcome candidate lookup"):
            is_long_horizon = "2024-12-02" in sql
            return json.dumps(
                [
                    {
                        "batch_id": 2001,
                        "recommendation_id": 9001,
                        "thesis_id": 7001,
                        "instrument_id": 501,
                        "primary_symbol": "AAPL",
                        "recommendation_score": "0.3610",
                        "recommendation_bucket": "watch",
                        "recommendation_action": "watch",
                        "thesis_title": "AAPL watch thesis via Annual Reporting",
                        "thesis_status": "active",
                        "benchmark_code": "SPY",
                        "measurement_start_date": "2024-11-01",
                        "measurement_end_date": "2024-12-02" if is_long_horizon else "2024-11-04",
                        "entry_price": "222.910000",
                        "exit_price": "245.201000" if is_long_horizon else "225.139100",
                        "min_price": "222.910000",
                        "benchmark_entry_price": "570.000000" if self.with_benchmark_prices else None,
                        "benchmark_exit_price": (
                            "592.800000" if is_long_horizon else "572.850000"
                        )
                        if self.with_benchmark_prices
                        else None,
                    }
                ]
            )
        if "insert into ops.pipeline_run" in sql:
            run_id = self._next_run_id
            self._next_run_id += 1
            return str(run_id)
        if "insert into performance.recommendation_outcome" in sql:
            if self.fail_on_upsert:
                raise RuntimeError("boom")
            return json.dumps(
                {
                    "recommendation_outcome_count": 1,
                    "thesis_outcome_count": 1,
                }
            )
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class EmptyExecutor:
    def execute_scalar(self, sql: str) -> str:
        return "[]"


class NoScheduleCandidatesExecutor:
    def __init__(self, *, run_id: int = 8401) -> None:
        self.run_id = run_id
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- performance outcome schedule candidate lookup"):
            return "[]"
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class PerformanceOutcomeBootstrapTests(unittest.TestCase):
    def test_render_performance_outcome_candidate_lookup_sql(self) -> None:
        sql = render_performance_outcome_candidate_lookup_sql(
            as_of_date=date(2024, 11, 1),
            measurement_end_date=date(2024, 11, 4),
            market_code="US",
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
        )
        self.assertIn("signal.recommendation_batch", sql)
        self.assertIn("signal.recommendation", sql)
        self.assertIn("signal.investment_thesis", sql)
        self.assertIn("market.daily_price_bar", sql)
        self.assertIn("benchmark_instrument", sql)
        self.assertIn("2024-11-04", sql)

    def test_load_performance_outcome_candidates(self) -> None:
        rows = load_performance_outcome_candidates(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            measurement_end_date=date(2024, 11, 4),
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=FakeExecutor(),
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].primary_symbol, "AAPL")
        self.assertEqual(rows[0].entry_price, Decimal("222.910000"))
        self.assertEqual(rows[0].exit_price, Decimal("225.139100"))

    def test_load_performance_outcome_candidates_fails_when_empty(self) -> None:
        with self.assertRaises(ValueError):
            load_performance_outcome_candidates(
                config=type("Config", (), {})(),
                as_of_date=date(2024, 11, 1),
                measurement_end_date=date(2024, 11, 4),
                strategy_name="long_term_core",
                horizon_type="long_term",
                universe_version="fixture-v1",
                executor=EmptyExecutor(),
            )

    def test_build_performance_outcome_rows(self) -> None:
        recommendation_rows, thesis_rows = build_performance_outcome_rows((_candidate(),))
        self.assertEqual(len(recommendation_rows), 1)
        self.assertEqual(len(thesis_rows), 1)
        self.assertEqual(recommendation_rows[0].absolute_return_pct, Decimal("0.010000"))
        self.assertEqual(recommendation_rows[0].max_drawdown_pct, Decimal("0.000000"))
        self.assertEqual(recommendation_rows[0].benchmark_return_pct, None)
        self.assertEqual(recommendation_rows[0].alpha_pct, None)
        self.assertEqual(recommendation_rows[0].outcome_label, "positive")
        self.assertEqual(recommendation_rows[0].horizon_days, 3)
        self.assertEqual(thesis_rows[0].success_grade, "pass")
        self.assertIn("AAPL thesis outcome positive", thesis_rows[0].summary)

    def test_build_performance_outcome_rows_with_benchmark_alpha(self) -> None:
        recommendation_rows, thesis_rows = build_performance_outcome_rows((_candidate_with_benchmark(),))
        self.assertEqual(recommendation_rows[0].absolute_return_pct, Decimal("0.010000"))
        self.assertEqual(recommendation_rows[0].benchmark_return_pct, Decimal("0.005000"))
        self.assertEqual(recommendation_rows[0].alpha_pct, Decimal("0.005000"))
        self.assertEqual(recommendation_rows[0].outcome_label, "outperform")
        self.assertEqual(thesis_rows[0].status, "working")
        self.assertEqual(thesis_rows[0].success_grade, "pass")
        self.assertIn("AAPL thesis outcome outperform", thesis_rows[0].summary)

    def test_resolve_performance_measurement_dates_combines_dates_and_horizon_days(self) -> None:
        measurement_dates = resolve_performance_measurement_dates(
            as_of_date=date(2024, 11, 1),
            measurement_end_dates=(date(2024, 11, 4),),
            horizon_days=(3, 31),
        )
        self.assertEqual(measurement_dates, (date(2024, 11, 4), date(2024, 12, 2)))

    def test_resolve_performance_measurement_dates_rejects_empty_input(self) -> None:
        with self.assertRaises(ValueError):
            resolve_performance_measurement_dates(as_of_date=date(2024, 11, 1))

    def test_resolve_performance_measurement_dates_rejects_invalid_values(self) -> None:
        with self.assertRaises(ValueError):
            resolve_performance_measurement_dates(
                as_of_date=date(2024, 11, 1),
                horizon_days=(0,),
            )
        with self.assertRaises(ValueError):
            resolve_performance_measurement_dates(
                as_of_date=date(2024, 11, 1),
                measurement_end_dates=(date(2024, 10, 31),),
            )

    def test_resolve_performance_schedule_horizon_days_defaults_and_dedupes(self) -> None:
        self.assertEqual(resolve_performance_schedule_horizon_days(), (30, 90, 180, 365))
        self.assertEqual(resolve_performance_schedule_horizon_days((31, 3, 31)), (3, 31))

    def test_resolve_performance_schedule_horizon_days_rejects_invalid_values(self) -> None:
        with self.assertRaises(ValueError):
            resolve_performance_schedule_horizon_days((0,))

    def test_render_performance_outcome_schedule_candidate_lookup_sql(self) -> None:
        sql = render_performance_outcome_schedule_candidate_lookup_sql(
            due_on_date=date(2024, 12, 2),
            horizon_days=(3, 31),
            market_code="US",
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            limit=10,
        )
        self.assertIn("horizon_days(horizon_day)", sql)
        self.assertIn("signal.recommendation_batch", sql)
        self.assertIn("performance.recommendation_outcome", sql)
        self.assertIn("existing_outcome_count < active_recommendation_count", sql)
        self.assertIn("2024-12-02", sql)
        self.assertIn("limit 10", sql)

    def test_load_performance_outcome_schedule_candidates(self) -> None:
        rows = load_performance_outcome_schedule_candidates(
            config=type("Config", (), {})(),
            due_on_date=date(2024, 12, 2),
            horizon_days=(31,),
            executor=FakeExecutor(),
        )
        self.assertEqual(
            rows,
            (
                PerformanceOutcomeScheduleCandidate(
                    batch_id=2001,
                    as_of_date=date(2024, 11, 1),
                    market_code="US",
                    strategy_name="long_term_core",
                    horizon_type="long_term",
                    universe_version="fixture-v1",
                    horizon_day=31,
                    measurement_end_date=date(2024, 12, 2),
                    active_recommendation_count=1,
                    existing_outcome_count=0,
                ),
            ),
        )

    def test_render_performance_outcome_upsert_sql(self) -> None:
        recommendation_rows, thesis_rows = build_performance_outcome_rows((_candidate(),))
        sql = render_performance_outcome_upsert_sql(recommendation_rows, thesis_rows, source_run_id=77)
        self.assertIn("insert into performance.recommendation_outcome", sql)
        self.assertIn("insert into performance.thesis_outcome", sql)
        self.assertIn("on conflict (recommendation_id, measurement_end_date) do update", sql)
        self.assertIn("on conflict (thesis_id, measurement_end_date) do update", sql)
        self.assertIn("0.010000::numeric", sql)
        self.assertIn("'positive'::text", sql)
        self.assertIn("77::bigint", sql)

    def test_render_performance_outcome_upsert_sql_with_benchmark_alpha(self) -> None:
        recommendation_rows, thesis_rows = build_performance_outcome_rows((_candidate_with_benchmark(),))
        sql = render_performance_outcome_upsert_sql(recommendation_rows, thesis_rows, source_run_id=77)
        self.assertIn("0.005000::numeric", sql)
        self.assertIn("'SPY'::text", sql)
        self.assertIn("'outperform'::text", sql)

    def test_run_performance_outcome_bootstrap_records_pipeline_run_and_summary(self) -> None:
        executor = FakeExecutor(run_id=8002)
        summary = run_performance_outcome_bootstrap(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            measurement_end_date=date(2024, 11, 4),
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=executor,
        )
        self.assertEqual(summary["run_id"], 8002)
        self.assertEqual(summary["batch_id"], 2001)
        self.assertEqual(summary["candidate_count"], 1)
        self.assertEqual(summary["recommendation_outcome_count"], 1)
        self.assertEqual(summary["thesis_outcome_count"], 1)
        self.assertEqual(summary["label_counts"], {"positive": 1})
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("insert into performance.recommendation_outcome", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])

    def test_run_performance_outcome_bootstrap_summarizes_outperform_when_benchmark_exists(self) -> None:
        executor = FakeExecutor(run_id=8004, with_benchmark_prices=True)
        summary = run_performance_outcome_bootstrap(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            measurement_end_date=date(2024, 11, 4),
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=executor,
        )
        self.assertEqual(summary["label_counts"], {"outperform": 1})
        self.assertIn("0.005000::numeric", executor.scalar_sql[2])
        self.assertIn("'outperform'::text", executor.scalar_sql[2])

    def test_run_performance_outcome_batch_bootstrap_runs_multiple_measurement_dates(self) -> None:
        executor = FakeExecutor(run_id=8100, with_benchmark_prices=True)
        summary = run_performance_outcome_batch_bootstrap(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            measurement_end_dates=(date(2024, 11, 4), date(2024, 12, 2)),
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=executor,
        )
        self.assertEqual(summary["measurement_end_dates"], ["2024-11-04", "2024-12-02"])
        self.assertEqual(summary["requested_measurement_count"], 2)
        self.assertEqual(summary["succeeded_measurement_count"], 2)
        self.assertEqual(summary["recommendation_outcome_count"], 2)
        self.assertEqual(summary["thesis_outcome_count"], 2)
        self.assertEqual(summary["label_counts"], {"outperform": 2})
        self.assertEqual([item["run_id"] for item in summary["results"]], [8100, 8101])
        self.assertIn("0.060000::numeric", executor.scalar_sql[-1])

    def test_run_performance_outcome_schedule_bootstrap_runs_due_candidates(self) -> None:
        executor = FakeExecutor(run_id=8300, with_benchmark_prices=True)
        summary = run_performance_outcome_schedule_bootstrap(
            config=type("Config", (), {})(),
            due_on_date=date(2024, 12, 2),
            horizon_days=(31,),
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=executor,
        )
        self.assertEqual(summary["run_id"], 8300)
        self.assertEqual(summary["candidate_count"], 1)
        self.assertEqual(summary["succeeded_candidate_count"], 1)
        self.assertEqual(summary["failed_candidate_count"], 0)
        self.assertEqual(summary["recommendation_outcome_count"], 1)
        self.assertEqual(summary["thesis_outcome_count"], 1)
        self.assertEqual(summary["label_counts"], {"outperform": 1})
        self.assertEqual(summary["results"][0]["run_id"], 8301)
        self.assertIn("performance_outcome_schedule_bootstrap", executor.scalar_sql[1])
        self.assertIn("performance_outcome_bootstrap", executor.scalar_sql[3])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])

    def test_run_performance_outcome_schedule_bootstrap_noops_when_no_candidates(self) -> None:
        executor = NoScheduleCandidatesExecutor(run_id=8402)
        summary = run_performance_outcome_schedule_bootstrap(
            config=type("Config", (), {})(),
            due_on_date=date(2024, 12, 2),
            horizon_days=(31,),
            executor=executor,
        )
        self.assertEqual(summary["candidate_count"], 0)
        self.assertEqual(summary["succeeded_candidate_count"], 0)
        self.assertEqual(summary["failed_candidate_count"], 0)
        self.assertEqual(summary["results"], [])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])

    def test_run_performance_outcome_schedule_bootstrap_marks_parent_failed_when_candidate_fails(self) -> None:
        executor = FakeExecutor(run_id=8500, fail_on_upsert=True)
        summary = run_performance_outcome_schedule_bootstrap(
            config=type("Config", (), {})(),
            due_on_date=date(2024, 12, 2),
            horizon_days=(31,),
            executor=executor,
        )
        self.assertEqual(summary["candidate_count"], 1)
        self.assertEqual(summary["succeeded_candidate_count"], 0)
        self.assertEqual(summary["failed_candidate_count"], 1)
        self.assertEqual(summary["results"][0]["status"], "failed")
        self.assertIn("boom", summary["results"][0]["error"])
        self.assertIn("status = 'failed'", executor.non_query_sql[-1])

    def test_run_performance_outcome_bootstrap_marks_pipeline_run_failed_when_upsert_errors(self) -> None:
        executor = FakeExecutor(run_id=8003, fail_on_upsert=True)
        with self.assertRaises(RuntimeError):
            run_performance_outcome_bootstrap(
                config=type("Config", (), {})(),
                as_of_date=date(2024, 11, 1),
                measurement_end_date=date(2024, 11, 4),
                strategy_name="long_term_core",
                horizon_type="long_term",
                universe_version="fixture-v1",
                executor=executor,
            )
        self.assertIn("status = 'failed'", executor.non_query_sql[-1])


def _candidate() -> PerformanceOutcomeCandidate:
    return PerformanceOutcomeCandidate(
        batch_id=2001,
        recommendation_id=9001,
        thesis_id=7001,
        instrument_id=501,
        primary_symbol="AAPL",
        recommendation_score=Decimal("0.3610"),
        recommendation_bucket="watch",
        recommendation_action="watch",
        thesis_title="AAPL watch thesis via Annual Reporting",
        thesis_status="active",
        benchmark_code="SPY",
        measurement_start_date=date(2024, 11, 1),
        measurement_end_date=date(2024, 11, 4),
        entry_price=Decimal("222.910000"),
        exit_price=Decimal("225.139100"),
        min_price=Decimal("222.910000"),
        benchmark_entry_price=None,
        benchmark_exit_price=None,
    )


def _candidate_with_benchmark() -> PerformanceOutcomeCandidate:
    return PerformanceOutcomeCandidate(
        batch_id=2001,
        recommendation_id=9001,
        thesis_id=7001,
        instrument_id=501,
        primary_symbol="AAPL",
        recommendation_score=Decimal("0.3610"),
        recommendation_bucket="watch",
        recommendation_action="watch",
        thesis_title="AAPL watch thesis via Annual Reporting",
        thesis_status="active",
        benchmark_code="SPY",
        measurement_start_date=date(2024, 11, 1),
        measurement_end_date=date(2024, 11, 4),
        entry_price=Decimal("222.910000"),
        exit_price=Decimal("225.139100"),
        min_price=Decimal("222.910000"),
        benchmark_entry_price=Decimal("570.000000"),
        benchmark_exit_price=Decimal("572.850000"),
    )
