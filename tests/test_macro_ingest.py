from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from stockanalysis.ingest.cli import main
from stockanalysis.ingest.macro.defaults import get_default_series, list_default_series
from stockanalysis.ingest.macro.fred import load_macro_sync_result
from stockanalysis.ingest.macro.sql import render_macro_sync_sql


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class MacroIngestTests(unittest.TestCase):
    def test_default_series_contains_core_ids(self) -> None:
        ids = [spec.series_id for spec in list_default_series()]
        self.assertIn("CPIAUCSL", ids)
        self.assertIn("FEDFUNDS", ids)
        self.assertIn("NASDAQQSLVO", ids)
        silver = get_default_series("NASDAQQSLVO")
        assert silver is not None
        self.assertEqual(silver.category, "commodity")
        self.assertIn("silver proxy", silver.description or "")

    def test_load_macro_sync_result_from_fixtures(self) -> None:
        spec = get_default_series("CPIAUCSL")
        assert spec is not None
        result = load_macro_sync_result(
            spec,
            config=type("Config", (), {})(),  # config is unused when fixtures are supplied
            series_json_path=str(FIXTURES_DIR / "fred_series_CPIAUCSL.json"),
            observations_json_path=str(FIXTURES_DIR / "fred_observations_CPIAUCSL.json"),
        )
        self.assertEqual(result.series.series_code, "CPIAUCSL")
        self.assertEqual(result.series.frequency, "M")
        self.assertEqual(len(result.observations), 2)
        self.assertEqual(result.skipped_count, 1)

    def test_render_macro_sync_sql(self) -> None:
        spec = get_default_series("CPIAUCSL")
        assert spec is not None
        result = load_macro_sync_result(
            spec,
            config=type("Config", (), {})(),
            series_json_path=str(FIXTURES_DIR / "fred_series_CPIAUCSL.json"),
            observations_json_path=str(FIXTURES_DIR / "fred_observations_CPIAUCSL.json"),
        )
        sql = render_macro_sync_sql(result)
        self.assertIn("insert into macro.series", sql)
        self.assertIn("insert into macro.observation", sql)
        self.assertIn("CPIAUCSL", sql)

    def test_macro_default_series_cli(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["macro-default-series"])
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        ids = [item["series_id"] for item in payload]
        self.assertIn("CPIAUCSL", ids)

    def test_macro_sync_cli_with_sql_output(self) -> None:
        stdout = io.StringIO()
        with tempfile.TemporaryDirectory() as temp_dir:
            sql_path = Path(temp_dir) / "macro.sql"
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "macro-sync",
                        "--series-id",
                        "CPIAUCSL",
                        "--series-json",
                        str(FIXTURES_DIR / "fred_series_CPIAUCSL.json"),
                        "--observations-json",
                        str(FIXTURES_DIR / "fred_observations_CPIAUCSL.json"),
                        "--sql-output",
                        str(sql_path),
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["observation_count"], 2)
            self.assertEqual(payload["skipped_count"], 1)
            self.assertTrue(sql_path.exists())
            self.assertIn("macro.series", sql_path.read_text(encoding="utf-8"))

    def test_macro_sync_cli_requires_category_for_unknown_series(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["macro-sync", "--series-id", "UNKNOWN_SERIES"])
        self.assertEqual(exit_code, 1)
        self.assertIn("Supply --category", stdout.getvalue())
