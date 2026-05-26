from __future__ import annotations

import tempfile
import unittest
import zipfile
from html import escape
from datetime import date
from pathlib import Path

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.benchmark_composition_provider import (
    load_ssga_spdr_holdings_xlsx,
    run_ssga_spdr_benchmark_composition_import,
    write_normalized_holdings_csv,
)


class FakeProviderImportExecutor:
    def __init__(self) -> None:
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []
        self.run_id = 1001

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class BenchmarkCompositionProviderTests(unittest.TestCase):
    def test_load_ssga_xlsx_normalizes_symbols_weights_and_skips_cash(self) -> None:
        path = _ssga_fixture_xlsx()

        holdings = load_ssga_spdr_holdings_xlsx(path, benchmark_code="spy")

        self.assertEqual(holdings.benchmark_code, "SPY")
        self.assertEqual(holdings.source_as_of_date, date(2026, 5, 21))
        self.assertEqual([row.symbol for row in holdings.rows], ["NVDA", "BRK-B"])
        self.assertEqual(str(holdings.rows[0].target_weight), "0.08348315")
        self.assertEqual(holdings.skipped_rows[0]["symbol"], "-")
        self.assertEqual(holdings.skipped_rows[1]["symbol"], "2602335D")

    def test_write_normalized_csv_uses_existing_import_contract_columns(self) -> None:
        path = _ssga_fixture_xlsx()
        holdings = load_ssga_spdr_holdings_xlsx(path, benchmark_code="SPY")
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "normalized.csv"

            write_normalized_holdings_csv(holdings, output)

            contents = output.read_text(encoding="utf-8")
        self.assertIn("symbol,target_weight,name,rationale", contents)
        self.assertIn("NVDA,0.08348315,NVIDIA CORP", contents)
        self.assertIn("BRK-B,0.01377355,BERKSHIRE HATHAWAY INC CL B", contents)

    def test_provider_import_run_reuses_import_runner_without_order_or_weight_mutation(self) -> None:
        executor = FakeProviderImportExecutor()
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_output = Path(tmpdir) / "raw.xlsx"
            csv_output = Path(tmpdir) / "normalized.csv"

            report = run_ssga_spdr_benchmark_composition_import(
                config=RuntimeConfig(psql_command="docker exec psql"),
                benchmark_code="SPY",
                source_xlsx=_ssga_fixture_xlsx(),
                raw_xlsx_output=raw_output,
                normalized_csv_output=csv_output,
                source_name="ssga_spdr_spy_daily_holdings",
                execute=True,
                create_missing_instruments=True,
                executor=executor,
            )

            self.assertFalse(raw_output.exists())
            self.assertTrue(csv_output.exists())

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["source_as_of_date"], "2026-05-21")
        self.assertEqual(report["coverage_status"], "partial_holdings_only")
        self.assertTrue(report["create_missing_instruments"])
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertFalse(report["automatic_order_allowed"])
        self.assertFalse(report["broker_submit_allowed"])
        self.assertIn("insert into ref.instrument", executor.non_query_sql[0].lower())
        self.assertNotIn("trading.order_intent", executor.non_query_sql[0].lower())


def _ssga_fixture_xlsx() -> Path:
    path = Path(tempfile.mkdtemp()) / "ssga-spy.xlsx"
    shared_strings = [
        "Fund Name:",
        "State Street® SPDR® S&P 500® ETF Trust",
        "Ticker Symbol:",
        "SPY",
        "Holdings:",
        "As of 21-May-2026",
        "Name",
        "Ticker",
        "Identifier",
        "SEDOL",
        "Weight",
        "Sector",
        "Shares Held",
        "NVIDIA CORP",
        "NVDA",
        "BERKSHIRE HATHAWAY INC CL B",
        "BRK.B",
        "US DOLLAR",
        "-",
        "CONTRA HOLOGIC INCORPO",
        "2602335D",
    ]
    sheet_rows = [
        [(1, 0), (2, 1)],
        [(1, 2), (2, 3)],
        [(1, 4), (2, 5)],
        [],
        [(1, 6), (2, 7), (3, 8), (4, 9), (5, 10), (6, 11), (7, 12)],
        [(1, 13), (2, 14), (5, "8.348315", "n")],
        [(1, 15), (2, 16), (5, "1.377355", "n")],
        [(1, 17), (2, 18), (5, "0.1068", "n")],
        [(1, 19), (2, 20), (5, "0.000003", "n")],
    ]
    with zipfile.ZipFile(path, "w") as workbook:
        workbook.writestr("[Content_Types].xml", _content_types_xml())
        workbook.writestr("xl/sharedStrings.xml", _shared_strings_xml(shared_strings))
        workbook.writestr("xl/worksheets/sheet1.xml", _sheet_xml(sheet_rows))
    return path


def _content_types_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
</Types>"""


def _shared_strings_xml(values: list[str]) -> str:
    items = "".join(f"<si><t>{escape(value)}</t></si>" for value in values)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(values)}" uniqueCount="{len(values)}">{items}</sst>"""


def _sheet_xml(rows: list[list[tuple[int, object] | tuple[int, object, str]]]) -> str:
    row_xml = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for cell in row:
            column_index, value = cell[0], cell[1]
            column = chr(ord("A") + column_index - 1)
            cell_type = cell[2] if len(cell) > 2 else "s"
            type_attr = "" if cell_type == "n" else ' t="s"'
            cells.append(f'<c r="{column}{row_index}"{type_attr}><v>{value}</v></c>')
        row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>{''.join(row_xml)}</sheetData>
</worksheet>"""


if __name__ == "__main__":
    unittest.main()
