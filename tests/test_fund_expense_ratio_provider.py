from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.fund_expense_ratio_provider import (
    DEFAULT_PIPELINE_NAME,
    parse_ssga_spdr_expense_ratio_page,
    render_fund_expense_ratio_upsert_sql,
    run_ssga_spdr_fund_expense_ratio_import,
)


class FakeExecutor:
    def __init__(self) -> None:
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "insert into ops.pipeline_run" in sql:
            return "701"
        if "insert into market.fund_metric_snapshot" in sql:
            return "991"
        return "1"

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class FundExpenseRatioProviderTests(unittest.TestCase):
    def test_parse_ssga_page_extracts_source_backed_gross_expense_ratio(self) -> None:
        snapshot = parse_ssga_spdr_expense_ratio_page(
            _ssga_fixture_html(),
            symbol="spy",
            source_url="https://www.ssga.com/example/spy",
            source_name="ssga_spdr_product_page",
        )

        self.assertEqual(snapshot.symbol, "SPY")
        self.assertEqual(snapshot.metric_code, "gross_expense_ratio")
        self.assertEqual(str(snapshot.metric_value), "0.000945")
        self.assertEqual(str(snapshot.percent_value), "0.094500")
        self.assertEqual(snapshot.source_as_of_date.isoformat(), "2026-05-26")
        self.assertEqual(snapshot.source_url, "https://www.ssga.com/example/spy")

    def test_parse_ssga_page_rejects_missing_expense_ratio(self) -> None:
        with self.assertRaisesRegex(ValueError, "Gross Expense Ratio"):
            parse_ssga_spdr_expense_ratio_page("<html>Fund Information as of May 26 2026</html>")

    def test_render_upsert_sql_uses_fund_metric_snapshot_without_scoring_mutation(self) -> None:
        snapshot = parse_ssga_spdr_expense_ratio_page(_ssga_fixture_html())
        sql = render_fund_expense_ratio_upsert_sql(snapshot, source_run_id=701)
        lowered = sql.lower()

        self.assertIn("insert into market.fund_metric_snapshot", lowered)
        self.assertIn("gross_expense_ratio", lowered)
        self.assertIn("ssga_spdr_product_page", lowered)
        self.assertIn("0.000945::numeric", lowered)
        self.assertIn("source_run_id", lowered)
        self.assertNotIn("signal.recommendation", lowered)
        self.assertNotIn("broker", lowered)

    def test_run_execute_records_pipeline_and_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = Path(tmpdir) / "spy.html"
            fixture_path.write_text(_ssga_fixture_html(), encoding="utf-8")
            executor = FakeExecutor()
            report = run_ssga_spdr_fund_expense_ratio_import(
                config=RuntimeConfig(),
                symbol="SPY",
                source_html=fixture_path,
                source_url="https://www.ssga.com/example/spy",
                execute=True,
                executor=executor,  # type: ignore[arg-type]
            )

        self.assertEqual(report["report_name"], DEFAULT_PIPELINE_NAME)
        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 701)
        self.assertEqual(report["fund_metric_snapshot_id"], 991)
        self.assertEqual(report["metric_value"], "0.000945")
        self.assertEqual(report["percent_value"], "0.094500")
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertFalse(report["automatic_order_allowed"])
        self.assertFalse(report["broker_submit_allowed"])
        self.assertTrue(any("insert into ops.pipeline_run" in sql for sql in executor.scalar_sql))
        self.assertTrue(any("insert into market.fund_metric_snapshot" in sql for sql in executor.scalar_sql))
        self.assertTrue(any("status = 'succeeded'" in sql for sql in executor.non_query_sql))

    def test_migration_creates_source_backed_fund_metric_table(self) -> None:
        migration = Path("db/migrations/0027_fund_metric_snapshot.sql").read_text(encoding="utf-8")
        self.assertIn("create table if not exists market.fund_metric_snapshot", migration)
        self.assertIn("source_url text not null", migration)
        self.assertIn("source_as_of_date date not null", migration)
        self.assertIn("gross_expense_ratio", migration)


def _ssga_fixture_html() -> str:
    return """
    <input type="hidden" id="fund-quick-info" value="{&#34;asOfDate&#34;:&#34;as of May 26 2026&#34;,&#34;asOfDateSimple&#34;:&#34;May 26 2026&#34;,&#34;attrs&#34;:{&#34;gross-expense-ratio&#34;:{&#34;label&#34;:&#34;Gross Expense Ratio&#34;,&#34;value&#34;:&#34;0.0945%&#34;,&#34;originalValue&#34;:&#34;0.0945&#34;}}}">
    <h2>Fund Information <span class="date">as of May 26 2026</span></h2>
    """


if __name__ == "__main__":
    unittest.main()
