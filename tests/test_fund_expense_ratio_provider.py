from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.fund_expense_ratio_provider import (
    DEFAULT_NAV_PREMIUM_DISCOUNT_PIPELINE_NAME,
    DEFAULT_PIPELINE_NAME,
    DEFAULT_TRACKING_DIFFERENCE_PIPELINE_NAME,
    parse_invesco_qqq_expense_ratio_json,
    parse_invesco_qqq_nav_premium_discount_json,
    parse_invesco_qqq_tracking_difference_json,
    parse_ssga_spdr_expense_ratio_page,
    parse_ssga_spdr_nav_premium_discount_page,
    parse_ssga_spdr_tracking_difference_page,
    render_fund_expense_ratio_upsert_sql,
    run_invesco_qqq_fund_expense_ratio_import,
    run_invesco_qqq_fund_nav_premium_discount_import,
    run_invesco_qqq_fund_tracking_difference_import,
    run_ssga_spdr_fund_expense_ratio_import,
    run_ssga_spdr_fund_nav_premium_discount_import,
    run_ssga_spdr_fund_tracking_difference_import,
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

    def test_parse_ssga_page_extracts_nav_market_price_and_premium_discount(self) -> None:
        snapshots = parse_ssga_spdr_nav_premium_discount_page(
            _ssga_fixture_html(),
            symbol="spy",
            source_url="https://www.ssga.com/example/spy",
            source_name="ssga_spdr_product_page",
        )
        by_code = {snapshot.metric_code: snapshot for snapshot in snapshots}

        self.assertEqual(set(by_code), {"nav_per_share", "bid_ask_midpoint", "closing_price", "premium_discount_to_nav"})
        self.assertEqual(str(by_code["nav_per_share"].metric_value), "745.571145")
        self.assertEqual(by_code["nav_per_share"].metric_unit, "USD")
        self.assertEqual(by_code["nav_per_share"].source_as_of_date.isoformat(), "2026-05-22")
        self.assertEqual(str(by_code["bid_ask_midpoint"].metric_value), "745.60")
        self.assertEqual(str(by_code["closing_price"].metric_value), "745.64")
        self.assertEqual(str(by_code["premium_discount_to_nav"].metric_value), "0.00")
        self.assertEqual(by_code["premium_discount_to_nav"].metric_unit, "ratio")

    def test_parse_ssga_page_extracts_tracking_difference_not_tracking_error(self) -> None:
        snapshots = parse_ssga_spdr_tracking_difference_page(
            _ssga_fixture_html(),
            symbol="spy",
            source_url="https://www.ssga.com/example/spy",
            source_name="ssga_spdr_product_page",
        )
        by_code = {snapshot.metric_code: snapshot for snapshot in snapshots}

        self.assertIn("tracking_difference_nav_1_year", by_code)
        one_year = by_code["tracking_difference_nav_1_year"]
        self.assertEqual(one_year.metric_unit, "ratio")
        self.assertEqual(str(one_year.metric_value), "-0.0021")
        self.assertEqual(one_year.source_as_of_date.isoformat(), "2026-04-30")
        self.assertEqual(one_year.measurement_window, "1 Year")
        self.assertEqual(one_year.measurement_basis, "nav_total_return_before_tax")
        self.assertEqual(one_year.benchmark_name, "S&P 500 Index")
        self.assertEqual(str(one_year.fund_return), "0.3084")
        self.assertEqual(str(one_year.benchmark_return), "0.3105")
        self.assertIn("not tracking error", one_year.rationale)

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

    def test_run_nav_execute_records_pipeline_and_all_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = Path(tmpdir) / "spy.html"
            fixture_path.write_text(_ssga_fixture_html(), encoding="utf-8")
            executor = FakeExecutor()
            report = run_ssga_spdr_fund_nav_premium_discount_import(
                config=RuntimeConfig(),
                symbol="SPY",
                source_html=fixture_path,
                source_url="https://www.ssga.com/example/spy",
                execute=True,
                executor=executor,  # type: ignore[arg-type]
            )

        self.assertEqual(report["report_name"], DEFAULT_NAV_PREMIUM_DISCOUNT_PIPELINE_NAME)
        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 701)
        self.assertEqual(report["metric_count"], 4)
        self.assertEqual(report["fund_metric_snapshot_ids"], [991, 991, 991, 991])
        metric_codes = {item["metric_code"] for item in report["metrics"]}  # type: ignore[index]
        self.assertEqual(metric_codes, {"nav_per_share", "bid_ask_midpoint", "closing_price", "premium_discount_to_nav"})
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertFalse(report["automatic_order_allowed"])
        self.assertFalse(report["broker_submit_allowed"])
        self.assertEqual(sum("insert into market.fund_metric_snapshot" in sql for sql in executor.scalar_sql), 4)
        self.assertTrue(any("status = 'succeeded'" in sql for sql in executor.non_query_sql))

    def test_run_tracking_difference_execute_records_pipeline_and_all_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = Path(tmpdir) / "spy.html"
            fixture_path.write_text(_ssga_fixture_html(), encoding="utf-8")
            executor = FakeExecutor()
            report = run_ssga_spdr_fund_tracking_difference_import(
                config=RuntimeConfig(),
                symbol="SPY",
                source_html=fixture_path,
                source_url="https://www.ssga.com/example/spy",
                execute=True,
                executor=executor,  # type: ignore[arg-type]
            )

        self.assertEqual(report["report_name"], DEFAULT_TRACKING_DIFFERENCE_PIPELINE_NAME)
        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 701)
        self.assertEqual(report["metric_count"], 8)
        self.assertEqual(report["fund_metric_snapshot_ids"], [991] * 8)
        metric_codes = {item["metric_code"] for item in report["metrics"]}  # type: ignore[index]
        self.assertIn("tracking_difference_nav_1_year", metric_codes)
        one_year = next(
            item for item in report["metrics"] if item["metric_code"] == "tracking_difference_nav_1_year"  # type: ignore[index]
        )
        self.assertEqual(one_year["metric_value"], "-0.0021")  # type: ignore[index]
        self.assertEqual(one_year["measurement_window"], "1 Year")  # type: ignore[index]
        self.assertEqual(one_year["benchmark_name"], "S&P 500 Index")  # type: ignore[index]
        self.assertEqual(report["metric_interpretation"], "tracking_difference_not_tracking_error")
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertFalse(report["automatic_order_allowed"])
        self.assertFalse(report["broker_submit_allowed"])
        self.assertEqual(sum("insert into market.fund_metric_snapshot" in sql for sql in executor.scalar_sql), 8)
        self.assertTrue(any("status = 'succeeded'" in sql for sql in executor.non_query_sql))

    def test_migration_creates_source_backed_fund_metric_table(self) -> None:
        migration = Path("db/migrations/0027_fund_metric_snapshot.sql").read_text(encoding="utf-8")
        nav_migration = Path("db/migrations/0028_fund_nav_premium_discount_metrics.sql").read_text(encoding="utf-8")
        tracking_migration = Path("db/migrations/0029_fund_tracking_difference_metrics.sql").read_text(encoding="utf-8")
        self.assertIn("create table if not exists market.fund_metric_snapshot", migration)
        self.assertIn("source_url text not null", migration)
        self.assertIn("source_as_of_date date not null", migration)
        self.assertIn("gross_expense_ratio", migration)
        self.assertIn("nav_per_share", nav_migration)
        self.assertIn("premium_discount_to_nav", nav_migration)
        self.assertIn("metric_unit = 'USD'", nav_migration)
        self.assertIn("tracking_difference_nav_1_year", tracking_migration)
        self.assertIn("measurement_window", tracking_migration)
        self.assertIn("benchmark_return", tracking_migration)

    def test_parse_invesco_qqq_details_extracts_expense_ratio_and_nav(self) -> None:
        expense = parse_invesco_qqq_expense_ratio_json(
            _invesco_qqq_details_json(),
            source_url="https://dng-api.invesco.com/qqq/details",
        )
        nav_metrics = parse_invesco_qqq_nav_premium_discount_json(
            _invesco_qqq_details_json(),
            source_url="https://dng-api.invesco.com/qqq/details",
        )

        self.assertEqual(expense.symbol, "QQQ")
        self.assertEqual(expense.metric_code, "net_expense_ratio")
        self.assertEqual(str(expense.metric_value), "0.0018")
        self.assertEqual(str(expense.percent_value), "0.1800")
        self.assertEqual(expense.source_as_of_date.isoformat(), "2026-06-06")
        self.assertEqual(nav_metrics[0].metric_code, "nav_per_share")
        self.assertEqual(str(nav_metrics[0].metric_value), "705.040931")
        self.assertEqual(nav_metrics[0].source_as_of_date.isoformat(), "2026-06-05")

    def test_parse_invesco_qqq_performance_extracts_tracking_difference(self) -> None:
        snapshots = parse_invesco_qqq_tracking_difference_json(_invesco_qqq_performance_json())
        by_code = {snapshot.metric_code: snapshot for snapshot in snapshots}

        self.assertEqual(
            set(by_code),
            {
                "tracking_difference_nav_1_year",
                "tracking_difference_nav_3_year",
                "tracking_difference_nav_5_year",
                "tracking_difference_nav_10_year",
            },
        )
        one_year = by_code["tracking_difference_nav_1_year"]
        self.assertEqual(str(one_year.metric_value), "-0.00317307")
        self.assertEqual(one_year.source_as_of_date.isoformat(), "2026-05-31")
        self.assertEqual(one_year.measurement_window, "1 Year")
        self.assertEqual(one_year.measurement_basis, "nav_total_return_growth_of_10k")
        self.assertEqual(one_year.benchmark_name, "NASDAQ-100 Index")
        self.assertEqual(str(one_year.fund_return), "0.4276845")
        self.assertEqual(str(one_year.benchmark_return), "0.43085757")
        self.assertIn("not tracking error", one_year.rationale)

    def test_run_invesco_qqq_metric_imports_record_pipeline_without_order_or_weight_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            details = Path(tmpdir) / "qqq-details.json"
            performance = Path(tmpdir) / "qqq-performance.json"
            details.write_text(_invesco_qqq_details_json(), encoding="utf-8")
            performance.write_text(_invesco_qqq_performance_json(), encoding="utf-8")
            executor = FakeExecutor()

            expense = run_invesco_qqq_fund_expense_ratio_import(
                config=RuntimeConfig(),
                symbol="QQQ",
                source_json=details,
                source_url="https://dng-api.invesco.com/qqq/details",
                execute=True,
                executor=executor,  # type: ignore[arg-type]
            )
            nav = run_invesco_qqq_fund_nav_premium_discount_import(
                config=RuntimeConfig(),
                symbol="QQQ",
                source_json=details,
                source_url="https://dng-api.invesco.com/qqq/details",
                execute=True,
                executor=executor,  # type: ignore[arg-type]
            )
            tracking = run_invesco_qqq_fund_tracking_difference_import(
                config=RuntimeConfig(),
                symbol="QQQ",
                source_json=performance,
                source_url="https://dng-api.invesco.com/qqq/performance",
                execute=True,
                executor=executor,  # type: ignore[arg-type]
            )

        self.assertEqual(expense["report_name"], "fund_expense_ratio_invesco_qqq_import")
        self.assertEqual(expense["metric_code"], "net_expense_ratio")
        self.assertEqual(expense["fund_metric_snapshot_id"], 991)
        self.assertEqual(nav["report_name"], "fund_nav_premium_discount_invesco_qqq_import")
        self.assertEqual(nav["metric_count"], 1)
        self.assertEqual(tracking["report_name"], "fund_tracking_difference_invesco_qqq_import")
        self.assertEqual(tracking["metric_count"], 4)
        self.assertEqual(tracking["metric_interpretation"], "tracking_difference_not_tracking_error")
        self.assertFalse(tracking["recommendation_scoring_mutated"])
        self.assertFalse(tracking["automatic_order_allowed"])
        self.assertFalse(tracking["broker_submit_allowed"])
        self.assertEqual(sum("insert into market.fund_metric_snapshot" in sql for sql in executor.scalar_sql), 6)


def _ssga_fixture_html() -> str:
    return """
    <input type="hidden" id="fund-quick-info" value="{&#34;asOfDate&#34;:&#34;as of May 26 2026&#34;,&#34;asOfDateSimple&#34;:&#34;May 26 2026&#34;,&#34;attrs&#34;:{&#34;gross-expense-ratio&#34;:{&#34;label&#34;:&#34;Gross Expense Ratio&#34;,&#34;value&#34;:&#34;0.0945%&#34;,&#34;originalValue&#34;:&#34;0.0945&#34;}}}">
    <input type="hidden" id="fund-quick-info-2" value="{&#34;attrs&#34;:{&#34;nav&#34;:{&#34;label&#34;:&#34;NAV&#34;,&#34;value&#34;:&#34;$745.57&#34;,&#34;asOfDate&#34;:&#34;as of May 22 2026&#34;,&#34;asOfDateSimple&#34;:&#34;May 22 2026&#34;,&#34;originalValue&#34;:&#34;745.571145&#34;}}}">
    <h2>Fund Information <span class="date">as of May 26 2026</span></h2>
    <h2 class="comp-title">Fund Market Price <span class="date">as of May 22 2026</span></h2>
    <table>
      <tr><th class="label" scope="row">Bid/Ask Midpoint</th><td class="data">$745.60</td></tr>
      <tr><th class="label" scope="row">Closing Price</th><td class="data">$745.64</td></tr>
      <tr><th class="label" scope="row">Premium/Discount</th><td class="data">0.00%</td></tr>
    </table>
    <div id="fund-ann-mon-panel">
      <table>
        <thead>
          <tr>
            <th class="label" scope="col">Name</th>
            <th class="date-col" scope="col">Date</th>
            <th class="data" scope="col">1 Month</th>
            <th class="data" scope="col">QTD</th>
            <th class="data" scope="col">YTD</th>
            <th class="data" scope="col">1 Year</th>
            <th class="data" scope="col">3 Year</th>
            <th class="data" scope="col">5 Year</th>
            <th class="data" scope="col">10 Year</th>
            <th class="data" scope="col">Since Inception<br />Jan 22 1993</th>
          </tr>
        </thead>
        <tbody>
          <tr class="sub-head"><th colspan="2" scope="rowgroup">Fund Before Tax</th><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
          <tr>
            <td>NAV</td><td class="date-col">Apr 30 2026</td>
            <td class="data">10.48%</td><td class="data">10.48%</td><td class="data">5.65%</td><td class="data">30.84%</td>
            <td class="data">21.52%</td><td class="data">13.00%</td><td class="data">15.10%</td><td class="data">10.75%</td>
          </tr>
          <tr>
            <td>Market Value</td><td class="date-col">Apr 30 2026</td>
            <td class="data">10.48%</td><td class="data">10.48%</td><td class="data">5.63%</td><td class="data">31.01%</td>
            <td class="data">21.51%</td><td class="data">12.98%</td><td class="data">15.10%</td><td class="data">10.75%</td>
          </tr>
          <tr>
            <td>Benchmark <span class="info"><div class="info-data">S&amp;P 500 Index</div></span></td><td class="date-col">Apr 30 2026</td>
            <td class="data">10.49%</td><td class="data">10.49%</td><td class="data">5.70%</td><td class="data">31.05%</td>
            <td class="data">21.69%</td><td class="data">13.14%</td><td class="data">15.26%</td><td class="data">10.89%</td>
          </tr>
        </tbody>
      </table>
    </div>
    """


def _invesco_qqq_details_json() -> str:
    return """
    {
      "cusip": "QQQ",
      "effectiveDate": "2026-06-06",
      "effectiveBusinessDate": "2026-06-05",
      "currencyCode": "USD",
      "totalNoOfHoldings": 102,
      "nav": 705.040931,
      "marketValue": 471178854307,
      "sharesOutstanding": 668300000,
      "feeValue": 0.18,
      "exchange": "Nasdaq/NMS (Global Market)",
      "inceptionDate": "1999-03-10",
      "ticker": "QQQ"
    }
    """


def _invesco_qqq_performance_json() -> str:
    return """
    {
      "effectiveDate": "2026-05-31",
      "ticker": "QQQ",
      "lineChart1YData": [
        {
          "type": "Shareclass",
          "label": "Invesco QQQ Trust, Series 1",
          "data": [{"date": "2026-05-31", "returnPercent": 42.76845}]
        },
        {
          "type": "Index2",
          "label": "NASDAQ-100 Index (USD)",
          "data": [{"date": "2026-05-31", "returnPercent": 43.085757}]
        }
      ],
      "lineChart3YData": [
        {
          "type": "Shareclass",
          "label": "Invesco QQQ Trust, Series 1",
          "data": [{"date": "2026-05-31", "returnPercent": 116.31897}]
        },
        {
          "type": "Index2",
          "label": "NASDAQ-100 Index (USD)",
          "data": [{"date": "2026-05-31", "returnPercent": 117.66369}]
        }
      ],
      "lineChart5YData": [
        {
          "type": "Shareclass",
          "label": "Invesco QQQ Trust, Series 1",
          "data": [{"date": "2026-05-31", "returnPercent": 127.983952}]
        },
        {
          "type": "Index2",
          "label": "NASDAQ-100 Index (USD)",
          "data": [{"date": "2026-05-31", "returnPercent": 130.405171}]
        }
      ],
      "lineChart10YData": [
        {
          "type": "Shareclass",
          "label": "Invesco QQQ Trust, Series 1",
          "data": [{"date": "2026-05-31", "returnPercent": 618.725315}]
        },
        {
          "type": "Index2",
          "label": "NASDAQ-100 Index (USD)",
          "data": [{"date": "2026-05-31", "returnPercent": 633.799144}]
        }
      ]
    }
    """


if __name__ == "__main__":
    unittest.main()
