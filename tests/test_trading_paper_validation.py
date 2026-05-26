from __future__ import annotations

import json
import unittest
from datetime import date
from decimal import Decimal

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.trading.paper_validation import (
    PortfolioRiskBudgetGuardrailSnapshot,
    SafetyConfigSnapshot,
    build_paper_validation_audit_plan,
    default_blocking_safety_config,
    render_portfolio_risk_budget_guardrail_snapshot_sql,
    render_paper_validation_audit_sql,
    render_paper_validation_safety_config_sql,
    run_paper_validation_audit,
    risk_budget_guardrail_from_payload,
    safety_config_from_payload,
)
from stockanalysis.trading.safety import (
    AccountPermission,
    BrokerBoundary,
    KillSwitchState,
    OrderLimitPolicy,
)


class PaperValidationAuditTests(unittest.TestCase):
    def test_plan_approves_paper_actions_when_safety_gates_pass(self) -> None:
        plan = build_paper_validation_audit_plan(
            preview_payload=_preview_payload(conflict=False),
            safety_config=_passing_safety_config(),
            validation_date=date(2026, 5, 18),
            portfolio_notional=Decimal("100000"),
            human_approved=True,
        )

        self.assertEqual(plan.validation_status, "passed")
        self.assertEqual(plan.recommendation_count, 2)
        self.assertEqual(plan.conflict_count, 0)
        self.assertEqual(plan.actionable_action_count, 2)
        self.assertEqual(plan.approved_action_count, 2)
        self.assertEqual(plan.validated_symbols, ("AAPL", "MSFT"))
        self.assertTrue(plan.source_preview_hash.startswith("sha256:"))
        for item in plan.audit_decisions:
            self.assertTrue(item.decision.allowed)
            self.assertFalse(item.decision.audit_payload["decision"]["submitted_to_broker"])

    def test_blocked_plan_renders_secret_free_audit_only_sql(self) -> None:
        plan = build_paper_validation_audit_plan(
            preview_payload=_preview_payload(conflict=True),
            safety_config=default_blocking_safety_config(),
            validation_date=date(2026, 5, 18),
            human_approved=False,
        )

        self.assertEqual(plan.validation_status, "failed")
        self.assertIn("position_recommendation_conflict:AAPL", plan.blocked_reasons)
        self.assertTrue(any(reason.endswith(":kill_switch_engaged") for reason in plan.blocked_reasons))
        self.assertTrue(any(reason.endswith(":human_approval_required") for reason in plan.blocked_reasons))

        sql = render_paper_validation_audit_sql(plan, created_by="paper-validation-audit-run")
        lowered = sql.lower()

        self.assertIn("trading.paper_validation_run", sql)
        self.assertIn("trading.order_intent_audit", sql)
        self.assertIn("submitted_to_broker", lowered)
        self.assertIn("submitted_to_broker = false", lowered)
        self.assertIn("false", lowered)
        self.assertNotIn("submitted_to_broker = true", lowered)
        self.assertNotIn("secret_ref", lowered)
        self.assertNotIn("api_key", lowered)
        self.assertNotIn("password", lowered)

    def test_plan_blocks_when_portfolio_risk_budget_guardrail_blocks_input(self) -> None:
        plan = build_paper_validation_audit_plan(
            preview_payload=_preview_payload(conflict=False),
            safety_config=_passing_safety_config(),
            risk_budget_guardrail=PortfolioRiskBudgetGuardrailSnapshot(
                status="loaded",
                eval_run_id=19,
                risk_gate_decision="blocked_by_risk_budget_review",
                paper_validation_input_allowed=False,
                blocking_reasons=("over_single_position_limit", "sector_over_limit"),
                effective_snapshot_date="2026-05-25",
            ),
            validation_date=date(2026, 5, 25),
            portfolio_notional=Decimal("100000"),
            human_approved=True,
        )

        self.assertEqual(plan.validation_status, "failed")
        self.assertIn("portfolio_risk_budget_guardrail:blocked_by_risk_budget_review", plan.blocked_reasons)
        self.assertIn("portfolio_risk_budget_guardrail_blocker:over_single_position_limit", plan.blocked_reasons)

    def test_risk_budget_guardrail_lookup_is_read_only_and_bounded_by_date(self) -> None:
        sql = render_portfolio_risk_budget_guardrail_snapshot_sql(
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 25),
        )
        lowered = sql.lower()

        self.assertIn("-- paper validation portfolio risk budget guardrail lookup", sql)
        self.assertIn("ai.eval_run", sql)
        self.assertIn("portfolio_risk_budget_guardrail", sql)
        self.assertIn("portfolio-risk-budget-guardrail-v1", sql)
        self.assertIn("::date <= '2026-05-25'::date", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_risk_budget_guardrail_payload_maps_blockers_without_order_unlock(self) -> None:
        snapshot = risk_budget_guardrail_from_payload(
            {
                "status": "loaded",
                "eval_run_id": 19,
                "risk_gate_decision": "blocked_by_risk_budget_review",
                "paper_validation_input_allowed": False,
                "effective_snapshot_date": "2026-05-25",
                "blocking_reasons": [{"code": "theme_over_limit"}],
                "warning_reasons": [{"code": "insufficient_benchmark_composition"}],
            }
        )

        self.assertEqual(snapshot.eval_run_id, 19)
        self.assertEqual(snapshot.risk_gate_decision, "blocked_by_risk_budget_review")
        self.assertFalse(snapshot.paper_validation_input_allowed)
        self.assertEqual(snapshot.blocking_reasons, ("theme_over_limit",))
        self.assertEqual(snapshot.warning_reasons, ("insufficient_benchmark_composition",))

    def test_safety_config_lookup_does_not_project_broker_secret(self) -> None:
        sql = render_paper_validation_safety_config_sql(portfolio_name="Long Term Paper")
        lowered = sql.lower()

        self.assertIn("trading.broker_boundary", lowered)
        self.assertIn("trading.account_permission", lowered)
        self.assertIn("trading.order_limit_policy", lowered)
        self.assertIn("trading.kill_switch_state", lowered)
        self.assertNotIn("secret_ref", lowered)

    def test_safety_config_payload_maps_only_non_secret_fields(self) -> None:
        snapshot = safety_config_from_payload(
            {
                "broker_boundary": {
                    "broker_boundary_id": 10,
                    "broker_code": "simulated_paper",
                    "environment": "paper",
                    "status": "enabled",
                    "supports_order_preview": True,
                    "supports_order_submit": False,
                    "secret_ref": "must-not-be-propagated",
                },
                "account_permission": {
                    "account_permission_id": 11,
                    "account_ref": "paper-account-1",
                    "permission_scope": "paper_trade",
                    "status": "active",
                    "allowed_symbols": ["AAPL", "MSFT"],
                    "max_order_notional": "50000",
                    "max_daily_notional": "100000",
                },
                "order_limit_policy": {
                    "status": "active",
                    "max_single_order_notional": "50000",
                    "max_daily_order_notional": "100000",
                    "max_single_order_weight_delta": "0.20",
                    "max_post_trade_symbol_weight": "0.40",
                    "min_cash_buffer_weight": "0.02",
                },
                "kill_switch": {"is_engaged": False, "reason": "paper mode enabled"},
            }
        )

        self.assertEqual(snapshot.broker_boundary_id, 10)
        self.assertEqual(snapshot.account_permission_id, 11)
        self.assertEqual(snapshot.broker_boundary.broker_code, "simulated_paper")
        self.assertEqual(snapshot.account_permission.allowed_symbols, ("AAPL", "MSFT"))
        self.assertFalse(snapshot.kill_switch.is_engaged)
        self.assertNotIn("must-not-be-propagated", repr(snapshot))

    def test_dry_run_fixture_source_can_use_default_blocking_config_without_db(self) -> None:
        report = run_paper_validation_audit(
            config=RuntimeConfig(),
            source="fixture",
            as_of_date=date(2026, 5, 18),
            dry_run=True,
        )

        self.assertEqual(report["report_name"], "paper_validation_audit_writer")
        self.assertEqual(report["status"], "dry_run")
        self.assertEqual(report["validation_status"], "failed")
        self.assertEqual(report["submitted_to_broker_count"], 0)
        self.assertEqual(report["safety_config"]["broker_boundary_status"], "not_configured")

    def test_live_run_writes_validation_and_audit_cte_with_fake_executor(self) -> None:
        executor = _PaperValidationFakeExecutor()

        report = run_paper_validation_audit(
            config=RuntimeConfig(psql_command="psql"),
            executor=executor,
            source="live",
            as_of_date=date(2026, 5, 18),
            portfolio_notional=Decimal("100000"),
            created_by="paper-validation-test",
            human_approved=True,
            dry_run=False,
        )

        self.assertEqual(report["status"], "written")
        self.assertEqual(report["validation_status"], "failed")
        self.assertEqual(report["write_result"]["audit_insert_count"], 2)
        self.assertEqual(report["write_result"]["submitted_to_broker_count"], 0)
        self.assertEqual(
            report["portfolio_risk_budget_guardrail"]["risk_gate_decision"],
            "blocked_by_risk_budget_review",
        )
        self.assertIn("portfolio_risk_budget_guardrail", report["blocked_reasons"][0])
        self.assertEqual(len(executor.write_sql), 1)
        self.assertIn("insert into trading.paper_validation_run", executor.write_sql[0])
        self.assertIn("insert into trading.order_intent_audit", executor.write_sql[0])
        self.assertNotIn("secret_ref", executor.write_sql[0].lower())


def _passing_safety_config() -> SafetyConfigSnapshot:
    return SafetyConfigSnapshot(
        broker_boundary=BrokerBoundary(
            broker_code="simulated_paper",
            environment="paper",
            status="enabled",
            supports_order_preview=True,
            supports_order_submit=False,
        ),
        account_permission=AccountPermission(
            account_ref="paper-account-1",
            permission_scope="paper_trade",
            status="active",
            allowed_symbols=("*",),
            max_order_notional=Decimal("50000"),
            max_daily_notional=Decimal("100000"),
        ),
        order_limit_policy=OrderLimitPolicy(
            status="active",
            max_single_order_notional=Decimal("50000"),
            max_daily_order_notional=Decimal("100000"),
            max_single_order_weight_delta=Decimal("0.20"),
            max_post_trade_symbol_weight=Decimal("0.40"),
            min_cash_buffer_weight=Decimal("0.02"),
        ),
        kill_switch=KillSwitchState(is_engaged=False, reason="paper mode enabled"),
        broker_boundary_id=10,
        account_permission_id=11,
    )


def _preview_payload(*, conflict: bool) -> dict[str, object]:
    return {
        "contract_version": "frontend-api-v0.1",
        "generated_at": "2026-05-19T00:00:00Z",
        "data": {
            "as_of_date": "2026-05-18",
            "portfolio_name": "Long Term Paper",
            "strategy_name": "long_term_core",
            "quality_summary": {
                "recommendation_count": 2,
                "position_recommendation_conflict_count": 1 if conflict else 0,
            },
            "paper_actions": [
                {
                    "symbol": "AAPL",
                    "latest_price": "240.0000",
                    "current_weight": "0.0500",
                    "target_weight": "0.0000",
                    "paper_action": "paper_sell_to_zero",
                    "conflict": conflict,
                },
                {
                    "symbol": "MSFT",
                    "latest_price": "426.8000",
                    "current_weight": "0.0000",
                    "target_weight": "0.0300",
                    "paper_action": "paper_buy_to_target",
                    "conflict": False,
                },
            ],
        },
    }


class _PaperValidationFakeExecutor:
    def __init__(self) -> None:
        self.scalar_sql: list[str] = []
        self.write_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- frontend paper trading preview state lookup"):
            return json.dumps(_preview_payload(conflict=True)["data"])
        if sql.startswith("-- paper validation safety config lookup"):
            return json.dumps(
                {
                    "broker_boundary": {
                        "broker_boundary_id": 10,
                        "broker_code": "simulated_paper",
                        "environment": "paper",
                        "status": "enabled",
                        "supports_order_preview": True,
                        "supports_order_submit": False,
                    },
                    "account_permission": {
                        "account_permission_id": 11,
                        "account_ref": "paper-account-1",
                        "permission_scope": "paper_trade",
                        "status": "active",
                        "allowed_symbols": ["AAPL", "MSFT"],
                        "max_order_notional": "50000",
                        "max_daily_notional": "100000",
                    },
                    "order_limit_policy": {
                        "status": "active",
                        "max_single_order_notional": "50000",
                        "max_daily_order_notional": "100000",
                        "max_single_order_weight_delta": "0.20",
                        "max_post_trade_symbol_weight": "0.40",
                        "min_cash_buffer_weight": "0.02",
                    },
                    "kill_switch": {"is_engaged": False, "reason": "paper mode enabled"},
                }
            )
        if sql.startswith("-- paper validation portfolio risk budget guardrail lookup"):
            return json.dumps(
                {
                    "status": "loaded",
                    "eval_run_id": 19,
                    "risk_gate_decision": "blocked_by_risk_budget_review",
                    "paper_validation_input_allowed": False,
                    "effective_snapshot_date": "2026-05-25",
                    "blocking_reasons": [{"code": "over_single_position_limit"}],
                    "warning_reasons": [{"code": "insufficient_benchmark_composition"}],
                }
            )
        if "insert into trading.paper_validation_run" in sql:
            self.write_sql.append(sql)
            return json.dumps(
                {
                    "paper_validation_run_id": 1001,
                    "audit_insert_count": 2,
                    "submitted_to_broker_count": 0,
                }
            )
        raise AssertionError(f"Unexpected SQL: {sql[:120]}")


if __name__ == "__main__":
    unittest.main()
