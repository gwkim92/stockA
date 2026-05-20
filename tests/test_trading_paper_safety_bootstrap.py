from __future__ import annotations

import json
import unittest
from decimal import Decimal

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.trading.paper_safety_bootstrap import (
    PaperSafetyBootstrapConfig,
    render_paper_safety_bootstrap_sql,
    run_paper_safety_bootstrap_config,
)


class PaperSafetyBootstrapTests(unittest.TestCase):
    def test_bootstrap_sql_upserts_paper_only_safety_rows(self) -> None:
        sql = render_paper_safety_bootstrap_sql(PaperSafetyBootstrapConfig())
        lowered = sql.lower()

        self.assertIn("insert into trading.broker_boundary", lowered)
        self.assertIn("insert into trading.account_permission", lowered)
        self.assertIn("insert into trading.order_limit_policy", lowered)
        self.assertIn("'paper_trade'", lowered)
        self.assertIn("supports_order_preview", lowered)
        self.assertIn("supports_order_submit = false", lowered)
        self.assertIn("'submitted_to_broker_count', 0", lowered)
        self.assertNotIn("submitted_to_broker = true", lowered)
        self.assertNotIn("broker api", lowered)
        self.assertNotIn("api_key", lowered)
        self.assertNotIn("password", lowered)

    def test_bootstrap_config_validates_limits(self) -> None:
        with self.assertRaisesRegex(ValueError, "max_daily_order_notional"):
            render_paper_safety_bootstrap_sql(
                PaperSafetyBootstrapConfig(
                    max_single_order_notional=Decimal("50000"),
                    max_daily_order_notional=Decimal("1000"),
                )
            )

    def test_dry_run_returns_secret_free_report_without_executor(self) -> None:
        report = run_paper_safety_bootstrap_config(
            config=RuntimeConfig(),
            bootstrap_config=PaperSafetyBootstrapConfig(),
            dry_run=True,
        )

        self.assertEqual(report["report_name"], "paper_safety_bootstrap_config")
        self.assertEqual(report["status"], "dry_run")
        self.assertEqual(report["broker_code"], "simulated_paper")
        self.assertFalse(report["supports_order_submit"])
        self.assertFalse(report["secret_configured"])
        self.assertFalse(report["kill_switch_changed"])
        self.assertEqual(report["submitted_to_broker_count"], 0)
        self.assertNotIn("secret_ref", json.dumps(report))

    def test_live_run_executes_one_bootstrap_statement(self) -> None:
        executor = _BootstrapFakeExecutor()

        report = run_paper_safety_bootstrap_config(
            config=RuntimeConfig(psql_command="psql"),
            executor=executor,
            bootstrap_config=PaperSafetyBootstrapConfig(created_by="paper-bootstrap-test"),
            dry_run=False,
        )

        self.assertEqual(report["status"], "written")
        self.assertEqual(report["write_result"]["broker_boundary_status"], "enabled")
        self.assertFalse(report["write_result"]["supports_order_submit"])
        self.assertTrue(report["write_result"]["kill_switch_engaged"])
        self.assertEqual(len(executor.scalar_sql), 1)
        self.assertIn("trading.broker_boundary", executor.scalar_sql[0])
        self.assertNotIn("submitted_to_broker = true", executor.scalar_sql[0].lower())


class _BootstrapFakeExecutor:
    def __init__(self) -> None:
        self.scalar_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        return json.dumps(
            {
                "status": "written",
                "portfolio_name": "Long Term Paper",
                "portfolio_id": 1,
                "broker_code": "simulated_paper",
                "broker_boundary_status": "enabled",
                "supports_order_preview": True,
                "supports_order_submit": False,
                "secret_configured": False,
                "account_ref": "paper-account-long-term",
                "account_permission_scope": "paper_trade",
                "account_permission_status": "active",
                "allowed_symbols": ["*"],
                "order_limit_policy_name": "long-term-paper-default",
                "order_limit_policy_status": "active",
                "kill_switch_engaged": True,
                "submitted_to_broker_count": 0,
            }
        )


if __name__ == "__main__":
    unittest.main()
