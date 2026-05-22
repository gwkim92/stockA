from __future__ import annotations

import json
import unittest
from datetime import date
from decimal import Decimal

from stockanalysis.signal.portfolio_review import (
    PortfolioReviewCandidate,
    build_portfolio_review,
    load_portfolio_review_candidates,
    render_portfolio_review_candidate_lookup_sql,
    render_portfolio_review_upsert_sql,
    run_portfolio_review_bootstrap,
)


class FakeExecutor:
    def __init__(self, *, run_id: int = 5001, review_id: int = 6001, fail_on_upsert: bool = False) -> None:
        self.run_id = run_id
        self.review_id = review_id
        self.fail_on_upsert = fail_on_upsert
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- portfolio review candidate lookup"):
            return json.dumps(
                [
                    {
                        "portfolio_id": 3001,
                        "portfolio_name": "Long Term Paper",
                        "instrument_id": 501,
                        "primary_symbol": "AAPL",
                        "quantity": "10.00000000",
                        "market_price": "222.910000",
                        "market_value": "2229.10",
                        "current_weight": "0.0500",
                        "unrealized_pnl": "120.00",
                        "linked_thesis_id": 7001,
                        "thesis_title": "AAPL watch thesis via Annual Reporting",
                        "thesis_status": "active",
                        "thesis_review_id": 8001,
                        "thesis_review_action": "watch",
                        "thesis_health_score": "0.3610",
                        "recommendation_id": 9001,
                        "recommendation_bucket": "watch",
                        "recommendation_action": "watch",
                        "recommendation_total_score": "0.3610",
                        "recommended_weight": None,
                        "allocation_policy_id": 4001,
                        "max_single_position_weight": "0.2500",
                        "min_rebalance_target_weight": "0.1000",
                        "coverage_measurement_end_date": None,
                        "coverage_status": "not_requested",
                        "outcome_id": None,
                        "outcome_status": None,
                        "outcome_success_grade": None,
                    }
                ]
            )
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if "insert into portfolio.review" in sql:
            if self.fail_on_upsert:
                raise RuntimeError("boom")
            return json.dumps(
                {
                    "portfolio_review_id": self.review_id,
                    "deleted_item_count": 0,
                    "item_count": 1,
                }
            )
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class EmptyExecutor:
    def execute_scalar(self, sql: str) -> str:
        return "[]"


class PortfolioReviewBootstrapTests(unittest.TestCase):
    def test_render_portfolio_review_candidate_lookup_sql(self) -> None:
        sql = render_portfolio_review_candidate_lookup_sql(
            portfolio_name="Long Term Paper",
            as_of_date=date(2024, 11, 1),
            market_code="US",
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            review_source="deterministic_bootstrap",
        )
        self.assertIn("portfolio.position_snapshot", sql)
        self.assertIn("signal.recommendation_batch", sql)
        self.assertIn("signal.recommendation", sql)
        self.assertIn("signal.investment_thesis", sql)
        self.assertIn("signal.thesis_review", sql)
        self.assertIn("portfolio.allocation_policy", sql)
        self.assertIn("max_single_position_weight", sql)
        self.assertIn("min_rebalance_target_weight", sql)
        self.assertIn("'not_requested'::text as coverage_status", sql)
        self.assertIn("'Long Term Paper'", sql)

    def test_render_portfolio_review_candidate_lookup_sql_with_coverage_gate(self) -> None:
        sql = render_portfolio_review_candidate_lookup_sql(
            portfolio_name="Long Term Paper",
            as_of_date=date(2024, 11, 1),
            market_code="US",
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            review_source="deterministic_bootstrap",
            coverage_measurement_end_date=date(2024, 12, 2),
        )
        self.assertIn("performance.thesis_outcome", sql)
        self.assertIn("outcome.measurement_start_date = '2024-11-01'::date", sql)
        self.assertIn("outcome.measurement_end_date = '2024-12-02'::date", sql)
        self.assertIn("then 'missing_thesis'", sql)
        self.assertIn("then 'missing_weight'", sql)
        self.assertIn("then 'missing_outcome'", sql)

    def test_load_portfolio_review_candidates(self) -> None:
        rows = load_portfolio_review_candidates(
            config=type("Config", (), {})(),
            portfolio_name="Long Term Paper",
            as_of_date=date(2024, 11, 1),
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=FakeExecutor(),
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].primary_symbol, "AAPL")
        self.assertEqual(rows[0].linked_thesis_id, 7001)
        self.assertEqual(rows[0].thesis_review_action, "watch")
        self.assertEqual(rows[0].current_weight, Decimal("0.0500"))
        self.assertEqual(rows[0].allocation_policy_id, 4001)
        self.assertEqual(rows[0].max_single_position_weight, Decimal("0.2500"))
        self.assertEqual(rows[0].min_rebalance_target_weight, Decimal("0.1000"))
        self.assertEqual(rows[0].coverage_status, "not_requested")
        self.assertEqual(rows[0].coverage_measurement_end_date, None)

    def test_load_portfolio_review_candidates_fails_when_empty(self) -> None:
        with self.assertRaises(ValueError):
            load_portfolio_review_candidates(
                config=type("Config", (), {})(),
                portfolio_name="Long Term Paper",
                as_of_date=date(2024, 11, 1),
                strategy_name="long_term_core",
                horizon_type="long_term",
                universe_version="fixture-v1",
                executor=EmptyExecutor(),
            )

    def test_build_portfolio_review_maps_watch_to_monitor(self) -> None:
        header, items = build_portfolio_review((_candidate(),), review_date=date(2024, 11, 1))
        self.assertEqual(header.portfolio_name, "Long Term Paper")
        self.assertEqual(header.cash_weight, Decimal("0.9500"))
        self.assertEqual(header.risk_level, "watch")
        self.assertEqual(items[0].action, "monitor")
        self.assertEqual(items[0].priority, 4)
        self.assertEqual(items[0].health_score, Decimal("0.3610"))
        self.assertEqual(items[0].weight_gap, None)
        self.assertIn("Thesis review action watch", items[0].reason)
        self.assertNotIn("Coverage status", header.overall_summary)

    def test_build_portfolio_review_increases_when_below_target(self) -> None:
        header, items = build_portfolio_review(
            (
                _candidate(
                    thesis_review_action="keep",
                    current_weight=Decimal("0.0200"),
                    recommended_weight=Decimal("0.0800"),
                ),
            ),
            review_date=date(2024, 11, 1),
        )
        self.assertEqual(header.risk_level, "normal")
        self.assertEqual(items[0].action, "increase_to_target")
        self.assertEqual(items[0].priority, 3)
        self.assertEqual(items[0].weight_gap, Decimal("0.0600"))

    def test_build_portfolio_review_does_not_trim_small_signal_weight_overage(self) -> None:
        header, items = build_portfolio_review(
            (
                _candidate(
                    thesis_review_action="keep",
                    current_weight=Decimal("0.1600"),
                    recommended_weight=Decimal("0.0400"),
                ),
            ),
            review_date=date(2024, 11, 1),
        )
        self.assertEqual(header.risk_level, "normal")
        self.assertEqual(items[0].action, "hold")
        self.assertEqual(items[0].priority, 4)
        self.assertEqual(items[0].weight_gap, Decimal("-0.1200"))

    def test_build_portfolio_review_trims_when_single_position_cap_is_exceeded(self) -> None:
        header, items = build_portfolio_review(
            (
                _candidate(
                    thesis_review_action="keep",
                    current_weight=Decimal("0.3100"),
                    recommended_weight=Decimal("0.0400"),
                ),
            ),
            review_date=date(2024, 11, 1),
        )
        self.assertEqual(header.risk_level, "normal")
        self.assertEqual(items[0].action, "trim_to_target")
        self.assertEqual(items[0].priority, 3)
        self.assertEqual(items[0].weight_gap, Decimal("-0.2700"))

    def test_build_portfolio_review_respects_portfolio_specific_single_position_cap(self) -> None:
        header, items = build_portfolio_review(
            (
                _candidate(
                    thesis_review_action="keep",
                    current_weight=Decimal("0.3100"),
                    recommended_weight=Decimal("0.0400"),
                    max_single_position_weight=Decimal("0.3500"),
                ),
            ),
            review_date=date(2024, 11, 1),
        )
        self.assertEqual(header.risk_level, "normal")
        self.assertEqual(items[0].action, "hold")
        self.assertIn("single position review cap 0.3500", items[0].reason)

    def test_build_portfolio_review_uses_meaningful_rebalance_target_policy(self) -> None:
        header, items = build_portfolio_review(
            (
                _candidate(
                    thesis_review_action="keep",
                    current_weight=Decimal("0.1600"),
                    recommended_weight=Decimal("0.1200"),
                    max_single_position_weight=Decimal("0.2500"),
                    min_rebalance_target_weight=Decimal("0.1000"),
                ),
            ),
            review_date=date(2024, 11, 1),
        )
        self.assertEqual(header.risk_level, "normal")
        self.assertEqual(items[0].action, "trim_to_target")
        self.assertEqual(items[0].weight_gap, Decimal("-0.0400"))

    def test_build_portfolio_review_maps_missing_thesis_coverage_to_review_action(self) -> None:
        header, items = build_portfolio_review(
            (
                _candidate(
                    linked_thesis_id=None,
                    thesis_review_action=None,
                    recommendation_id=9001,
                    coverage_measurement_end_date=date(2024, 12, 2),
                    coverage_status="missing_thesis",
                ),
            ),
            review_date=date(2024, 11, 1),
        )
        self.assertEqual(header.risk_level, "watch")
        self.assertIn("Coverage status missing_thesis:1", header.overall_summary)
        self.assertEqual(items[0].action, "needs_thesis_review")
        self.assertEqual(items[0].priority, 3)
        self.assertIn("coverage status missing_thesis", items[0].reason)

    def test_build_portfolio_review_maps_missing_outcome_to_review_action(self) -> None:
        header, items = build_portfolio_review(
            (
                _candidate(
                    thesis_review_action="watch",
                    coverage_measurement_end_date=date(2024, 12, 2),
                    coverage_status="missing_outcome",
                ),
            ),
            review_date=date(2024, 11, 1),
        )
        self.assertEqual(header.risk_level, "watch")
        self.assertEqual(items[0].action, "needs_outcome_review")
        self.assertEqual(items[0].priority, 3)
        self.assertIn("coverage status missing_outcome", items[0].reason)

    def test_build_portfolio_review_maps_missing_weight_to_review_action(self) -> None:
        header, items = build_portfolio_review(
            (
                _candidate(
                    current_weight=None,
                    coverage_measurement_end_date=date(2024, 12, 2),
                    coverage_status="missing_weight",
                ),
            ),
            review_date=date(2024, 11, 1),
        )
        self.assertEqual(header.cash_weight, None)
        self.assertEqual(items[0].action, "needs_weight_review")
        self.assertEqual(items[0].priority, 3)

    def test_render_portfolio_review_upsert_sql(self) -> None:
        header, items = build_portfolio_review((_candidate(),), review_date=date(2024, 11, 1))
        sql = render_portfolio_review_upsert_sql(header, items, source_run_id=77)
        self.assertIn("insert into portfolio.review", sql)
        self.assertIn("insert into portfolio.review_item", sql)
        self.assertIn("on conflict (portfolio_id, review_date, review_source) do update", sql)
        self.assertIn("'monitor'::text", sql)
        self.assertIn("0.0500::numeric", sql)
        self.assertIn("77::bigint", sql)

    def test_run_portfolio_review_bootstrap_records_pipeline_run_and_summary(self) -> None:
        executor = FakeExecutor(run_id=5002, review_id=6002)
        summary = run_portfolio_review_bootstrap(
            config=type("Config", (), {})(),
            portfolio_name="Long Term Paper",
            as_of_date=date(2024, 11, 1),
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=executor,
        )
        self.assertEqual(summary["run_id"], 5002)
        self.assertEqual(summary["portfolio_review_id"], 6002)
        self.assertEqual(summary["candidate_count"], 1)
        self.assertEqual(summary["review_item_count"], 1)
        self.assertEqual(summary["action_counts"], {"monitor": 1})
        self.assertEqual(summary["coverage_status_counts"], {"not_requested": 1})
        self.assertEqual(summary["risk_level"], "watch")
        self.assertEqual(summary["cash_weight"], "0.9500")
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("insert into portfolio.review", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])

    def test_run_portfolio_review_bootstrap_marks_pipeline_run_failed_when_upsert_errors(self) -> None:
        executor = FakeExecutor(run_id=5003, fail_on_upsert=True)
        with self.assertRaises(RuntimeError):
            run_portfolio_review_bootstrap(
                config=type("Config", (), {})(),
                portfolio_name="Long Term Paper",
                as_of_date=date(2024, 11, 1),
                strategy_name="long_term_core",
                horizon_type="long_term",
                universe_version="fixture-v1",
                executor=executor,
            )
        self.assertIn("status = 'failed'", executor.non_query_sql[-1])


def _candidate(
    *,
    thesis_review_action: str | None = "watch",
    current_weight: Decimal | None = Decimal("0.0500"),
    recommended_weight: Decimal | None = None,
    allocation_policy_id: int | None = 4001,
    max_single_position_weight: Decimal = Decimal("0.2500"),
    min_rebalance_target_weight: Decimal = Decimal("0.1000"),
    linked_thesis_id: int | None = 7001,
    recommendation_id: int | None = 9001,
    coverage_measurement_end_date: date | None = None,
    coverage_status: str = "not_requested",
) -> PortfolioReviewCandidate:
    return PortfolioReviewCandidate(
        portfolio_id=3001,
        portfolio_name="Long Term Paper",
        instrument_id=501,
        primary_symbol="AAPL",
        quantity=Decimal("10.00000000"),
        market_price=Decimal("222.910000"),
        market_value=Decimal("2229.10"),
        current_weight=current_weight,
        unrealized_pnl=Decimal("120.00"),
        linked_thesis_id=linked_thesis_id,
        thesis_title="AAPL watch thesis via Annual Reporting",
        thesis_status="active",
        thesis_review_id=8001,
        thesis_review_action=thesis_review_action,
        thesis_health_score=Decimal("0.3610"),
        recommendation_id=recommendation_id,
        recommendation_bucket="watch",
        recommendation_action="watch",
        recommendation_total_score=Decimal("0.3610"),
        recommended_weight=recommended_weight,
        coverage_measurement_end_date=coverage_measurement_end_date,
        coverage_status=coverage_status,
        outcome_id=None,
        outcome_status=None,
        outcome_success_grade=None,
        allocation_policy_id=allocation_policy_id,
        max_single_position_weight=max_single_position_weight,
        min_rebalance_target_weight=min_rebalance_target_weight,
    )
