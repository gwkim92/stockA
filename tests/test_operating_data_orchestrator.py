from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from stockanalysis.operations.operating_data_orchestrator import build_operating_data_run_report


class FakeOperatingDataExecutor:
    def __init__(self) -> None:
        self.scalar_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- operating data context lookup"):
            return json.dumps(
                {
                    "latest_price_date": "2026-05-19",
                    "latest_event_date": "2026-05-20",
                    "event_impacted_symbols": ["AAPL", "TSLA"],
                    "missing_event_price_symbols": ["TSLA"],
                }
            )
        if sql.startswith("-- operating data latest price lookup"):
            return json.dumps(
                [
                    {
                        "symbol": "AAPL",
                        "trade_date": "2026-05-19",
                        "adjusted_close": "200.000000",
                        "close": "200.000000",
                    },
                    {
                        "symbol": "TSLA",
                        "trade_date": "2026-05-19",
                        "adjusted_close": "400.000000",
                        "close": "400.000000",
                    },
                ]
            )
        raise AssertionError(f"Unexpected SQL: {sql}")


class FakeArtifactRunner:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def __call__(self, **kwargs: object) -> dict[str, object]:
        self.calls.append(kwargs)
        index = len(self.calls)
        return {
            "status": "succeeded",
            "exit_code": 0,
            "artifact_dir": f"/tmp/artifact-{index}",
            "metadata_path": f"/tmp/artifact-{index}/metadata.json",
            "stdout_path": f"/tmp/artifact-{index}/stdout.txt",
            "stderr_path": f"/tmp/artifact-{index}/stderr.log",
        }


class OperatingDataOrchestratorTests(unittest.TestCase):
    def test_preview_builds_secret_free_full_plan_without_running_steps(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            runtime_root, env_file = _write_runtime_files(Path(outside_root))
            runner = FakeArtifactRunner()

            report = build_operating_data_run_report(
                repo_root=repo_root,
                runtime_root=runtime_root,
                data_operations_env_file=env_file,
                execute=False,
                python_executable="/usr/bin/python3",
                executor=FakeOperatingDataExecutor(),
                runner=runner,
                generated_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
            )

        self.assertEqual(report["run_status"], "preview_not_executed")
        self.assertFalse(report["execute"])
        self.assertEqual(runner.calls, [])
        self.assertIn("TSLA", report["derived_inputs"]["missing_price_symbols"])
        step_ids = [step["step_id"] for step in report["planned_steps"]]
        self.assertEqual(step_ids[0], "missing-symbol-price-backfill")
        self.assertIn("portfolio-position-snapshot", step_ids)
        self.assertIn("paper-validation-audit", step_ids)
        self.assertNotIn("postgresql://", json.dumps(report))
        self.assertNotIn("secret-token", json.dumps(report))

    def test_execute_runs_backfill_before_signal_and_generates_position_csv(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            runtime_root, env_file = _write_runtime_files(Path(outside_root))
            runner = FakeArtifactRunner()

            report = build_operating_data_run_report(
                repo_root=repo_root,
                runtime_root=runtime_root,
                data_operations_env_file=env_file,
                execute=True,
                python_executable="/usr/bin/python3",
                executor=FakeOperatingDataExecutor(),
                runner=runner,
                generated_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
            )

            watchlist_path = Path(report["generated_files"]["missing_price_watchlist"])
            positions_path = Path(report["generated_files"]["position_snapshot_csv"])
            with watchlist_path.open(encoding="utf-8") as stream:
                watchlist_rows = list(csv.DictReader(stream))
            with positions_path.open(encoding="utf-8") as stream:
                position_rows = list(csv.DictReader(stream))

        self.assertEqual(report["run_status"], "completed")
        self.assertGreater(len(runner.calls), 8)
        rendered_commands = [" ".join(call["command_argv"]) for call in runner.calls]
        backfill_index = next(index for index, command in enumerate(rendered_commands) if "market-price-free-backfill-run" in command)
        signal_index = next(index for index, command in enumerate(rendered_commands) if "strategy-universe-slice" in command)
        self.assertLess(backfill_index, signal_index)
        self.assertEqual(watchlist_rows, [{"symbol": "TSLA"}])
        self.assertEqual([row["symbol"] for row in position_rows], ["AAPL", "TSLA"])
        self.assertEqual(position_rows[0]["market_price"], "200.000000")
        self.assertEqual(position_rows[1]["market_price"], "400.000000")
        self.assertEqual(position_rows[0]["weight"], "0.3333")
        self.assertEqual(position_rows[1]["weight"], "0.6667")


def _write_runtime_files(root: Path) -> tuple[Path, Path]:
    runtime_root = root / "runtime"
    runtime_root.mkdir()
    artifact_root = root / "artifacts"
    positions_csv = root / "portfolio-source.csv"
    positions_csv.write_text(
        "symbol,quantity,cost_basis\nAAPL,10,150\nTSLA,10,250\n",
        encoding="utf-8",
    )
    env_file = root / "data-operations.env"
    env_file.write_text(
        "\n".join(
            [
                f'STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="{artifact_root}"',
                f'STOCKANALYSIS_PORTFOLIO_POSITIONS_CSV="{positions_csv}"',
                f'STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH="{root / "ledger.json"}"',
                'STOCKANALYSIS_MARKET_PRICE_PROVIDER="twelve_data"',
                'STOCKANALYSIS_PSQL_COMMAND="psql postgresql://operator:secret-token@db.internal/stockanalysis"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return runtime_root, env_file


if __name__ == "__main__":
    unittest.main()
