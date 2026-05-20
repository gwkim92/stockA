from __future__ import annotations

import json
import unittest
from decimal import Decimal
from pathlib import Path

from stockanalysis.trading.safety import (
    AccountPermission,
    BrokerBoundary,
    KillSwitchState,
    OrderIntent,
    OrderLimitPolicy,
    PaperValidationState,
    evaluate_order_intent,
    render_order_intent_audit_insert_sql,
)


class TradingSafetyTests(unittest.TestCase):
    def test_order_intent_is_blocked_by_default_safety_gates(self) -> None:
        decision = evaluate_order_intent(
            _sell_intent(execution_mode="live"),
            broker_boundary=BrokerBoundary(
                broker_code="not_configured",
                environment="live",
                status="not_configured",
                supports_order_preview=False,
                supports_order_submit=False,
            ),
            account_permission=AccountPermission(
                account_ref="acct-paper-1",
                permission_scope="read_only",
                status="inactive",
                allowed_symbols=(),
            ),
            order_limit_policy=_limit_policy(status="inactive"),
            kill_switch=KillSwitchState(is_engaged=True, reason="operator lock"),
            paper_validation=PaperValidationState(
                status="missing",
                validated_symbols=(),
                conflict_count=1,
            ),
            human_approved=False,
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.decision, "blocked")
        self.assertIn("broker_boundary_not_enabled", decision.reasons)
        self.assertIn("account_permission_not_active", decision.reasons)
        self.assertIn("kill_switch_engaged", decision.reasons)
        self.assertIn("human_approval_required", decision.reasons)
        self.assertIn("paper_validation_not_passed", decision.reasons)
        self.assertFalse(decision.audit_payload["decision"]["submitted_to_broker"])

    def test_paper_order_can_be_approved_when_all_paper_gates_pass(self) -> None:
        decision = evaluate_order_intent(
            _sell_intent(execution_mode="paper"),
            broker_boundary=BrokerBoundary(
                broker_code="simulated_broker",
                environment="paper",
                status="enabled",
                supports_order_preview=True,
                supports_order_submit=False,
            ),
            account_permission=AccountPermission(
                account_ref="paper-account-1",
                permission_scope="paper_trade",
                status="active",
                allowed_symbols=("AAPL",),
                max_order_notional=Decimal("50000"),
                max_daily_notional=Decimal("100000"),
            ),
            order_limit_policy=_limit_policy(),
            kill_switch=KillSwitchState(is_engaged=False, reason="operator enabled paper mode"),
            paper_validation=PaperValidationState(
                status="missing",
                validated_symbols=(),
                conflict_count=0,
            ),
            human_approved=True,
        )

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.decision, "approved_for_paper")
        self.assertEqual(decision.estimated_notional, Decimal("30023.00"))
        self.assertEqual(decision.reasons, ())

    def test_live_order_requires_live_scope_and_passed_paper_validation(self) -> None:
        decision = evaluate_order_intent(
            _sell_intent(execution_mode="live"),
            broker_boundary=BrokerBoundary(
                broker_code="future_live_broker",
                environment="live",
                status="enabled",
                supports_order_preview=True,
                supports_order_submit=True,
            ),
            account_permission=AccountPermission(
                account_ref="live-account-1",
                permission_scope="live_trade",
                status="active",
                allowed_symbols=("AAPL",),
                max_order_notional=Decimal("50000"),
                max_daily_notional=Decimal("100000"),
            ),
            order_limit_policy=_limit_policy(),
            kill_switch=KillSwitchState(is_engaged=False, reason="operator enabled live mode"),
            paper_validation=PaperValidationState(
                status="passed",
                validated_symbols=("AAPL",),
                conflict_count=0,
            ),
            human_approved=True,
        )

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.decision, "approved_for_live")
        self.assertEqual(decision.reasons, ())

    def test_live_order_is_blocked_when_paper_validation_has_remaining_conflicts(self) -> None:
        decision = evaluate_order_intent(
            _sell_intent(execution_mode="live"),
            broker_boundary=BrokerBoundary(
                broker_code="future_live_broker",
                environment="live",
                status="enabled",
                supports_order_preview=True,
                supports_order_submit=True,
            ),
            account_permission=AccountPermission(
                account_ref="live-account-1",
                permission_scope="live_trade",
                status="active",
                allowed_symbols=("AAPL",),
            ),
            order_limit_policy=OrderLimitPolicy(
                status="active",
                max_single_order_notional=Decimal("50000"),
                max_daily_order_notional=Decimal("100000"),
                max_single_order_weight_delta=Decimal("0.20"),
                max_post_trade_symbol_weight=Decimal("0.40"),
                min_cash_buffer_weight=Decimal("0.02"),
            ),
            kill_switch=KillSwitchState(is_engaged=False, reason="operator enabled live mode"),
            paper_validation=PaperValidationState(
                status="passed",
                validated_symbols=("AAPL",),
                conflict_count=1,
            ),
            human_approved=True,
        )

        self.assertFalse(decision.allowed)
        self.assertIn("paper_validation_conflicts_remaining", decision.reasons)

    def test_order_limits_block_oversized_notional_and_weight_delta(self) -> None:
        decision = evaluate_order_intent(
            OrderIntent(
                symbol="AAPL",
                side="buy",
                quantity=Decimal("1000"),
                estimated_price=Decimal("300.23"),
                order_type="market",
                execution_mode="paper",
                current_weight=Decimal("0"),
                target_weight=Decimal("0.75"),
                projected_cash_weight=Decimal("0.01"),
            ),
            broker_boundary=BrokerBoundary(
                broker_code="simulated_broker",
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
            ),
            order_limit_policy=OrderLimitPolicy(
                status="active",
                max_single_order_notional=Decimal("50000"),
                max_daily_order_notional=Decimal("100000"),
                max_single_order_weight_delta=Decimal("0.20"),
                max_post_trade_symbol_weight=Decimal("0.40"),
                min_cash_buffer_weight=Decimal("0.02"),
            ),
            kill_switch=KillSwitchState(is_engaged=False, reason="operator enabled paper mode"),
            paper_validation=PaperValidationState(status="missing", validated_symbols=(), conflict_count=0),
            human_approved=True,
        )

        self.assertFalse(decision.allowed)
        self.assertIn("single_order_notional_limit_exceeded", decision.reasons)
        self.assertIn("single_order_weight_delta_limit_exceeded", decision.reasons)
        self.assertIn("post_trade_symbol_weight_limit_exceeded", decision.reasons)
        self.assertIn("cash_buffer_limit_exceeded", decision.reasons)

    def test_audit_insert_sql_is_audit_only_and_secret_free(self) -> None:
        decision = evaluate_order_intent(
            _sell_intent(execution_mode="paper"),
            broker_boundary=BrokerBoundary(
                broker_code="simulated_broker",
                environment="paper",
                status="enabled",
                supports_order_preview=True,
                supports_order_submit=False,
            ),
            account_permission=AccountPermission(
                account_ref="paper-account-1",
                permission_scope="paper_trade",
                status="active",
                allowed_symbols=("AAPL",),
            ),
            order_limit_policy=_limit_policy(),
            kill_switch=KillSwitchState(is_engaged=False, reason="operator enabled paper mode"),
            paper_validation=PaperValidationState(status="missing", validated_symbols=(), conflict_count=0),
            human_approved=True,
        )

        sql = render_order_intent_audit_insert_sql(
            decision,
            idempotency_key="paper-aapl-20260519-0001",
            created_by="operator",
            portfolio_id=1,
            broker_boundary_id=2,
            account_permission_id=3,
        )

        self.assertIn("insert into trading.order_intent_audit", sql)
        self.assertIn("submitted_to_broker", sql)
        self.assertIn("false", sql)
        self.assertNotIn("api_key", sql.lower())
        self.assertNotIn("secret", sql.lower())
        self.assertNotIn("password", sql.lower())
        json.dumps(decision.audit_payload)

    def test_trading_safety_migration_contains_required_boundaries(self) -> None:
        migration = Path("db/migrations/0013_trading_safety_boundary.sql").read_text(encoding="utf-8")

        for table in (
            "trading.broker_boundary",
            "trading.account_permission",
            "trading.order_limit_policy",
            "trading.kill_switch_state",
            "trading.paper_validation_run",
            "trading.order_intent_audit",
        ):
            self.assertIn(table, migration)

        self.assertIn("default locked until explicit operator approval", migration)
        self.assertIn("submitted_to_broker boolean not null default false", migration)
        self.assertIn("permission_scope in ('read_only', 'paper_trade', 'live_trade')", migration)
        self.assertIn("decision in ('blocked', 'approved_for_paper', 'approved_for_live')", migration)


def _sell_intent(*, execution_mode: str) -> OrderIntent:
    return OrderIntent(
        symbol="AAPL",
        side="sell",
        quantity=Decimal("100"),
        estimated_price=Decimal("300.23"),
        order_type="market",
        execution_mode=execution_mode,
        current_weight=Decimal("1.0"),
        target_weight=Decimal("0.0"),
        projected_cash_weight=Decimal("1.0"),
    )


def _limit_policy(*, status: str = "active") -> OrderLimitPolicy:
    return OrderLimitPolicy(
        status=status,
        max_single_order_notional=Decimal("50000"),
        max_daily_order_notional=Decimal("100000"),
        max_single_order_weight_delta=Decimal("1.0"),
        max_post_trade_symbol_weight=Decimal("1.0"),
        min_cash_buffer_weight=Decimal("0.02"),
    )


if __name__ == "__main__":
    unittest.main()
