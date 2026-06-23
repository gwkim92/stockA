from __future__ import annotations

import unittest
from decimal import Decimal

from stockanalysis.trading.tossinvest_order_adapter import (
    TossInvestOrderAdapter,
    TossInvestOrderAdapterDisabledError,
    TossInvestOrderCancelRequest,
    TossInvestOrderModifyRequest,
    TossInvestOrderRequest,
)


class TossInvestOrderAdapterTests(unittest.TestCase):
    def test_submit_modify_cancel_raise_before_http_path(self) -> None:
        adapter = TossInvestOrderAdapter()

        with self.assertRaises(TossInvestOrderAdapterDisabledError):
            adapter.submit_order(
                TossInvestOrderRequest(
                    account_seq="account-seq-secret-test",
                    symbol="AAPL",
                    side="buy",
                    quantity=Decimal("1"),
                    order_type="market",
                )
            )
        with self.assertRaises(TossInvestOrderAdapterDisabledError):
            adapter.modify_order(
                TossInvestOrderModifyRequest(
                    account_seq="account-seq-secret-test",
                    order_id="order-1",
                    quantity=Decimal("1"),
                )
            )
        with self.assertRaises(TossInvestOrderAdapterDisabledError):
            adapter.cancel_order(
                TossInvestOrderCancelRequest(
                    account_seq="account-seq-secret-test",
                    order_id="order-1",
                )
            )

        status = adapter.status()
        self.assertEqual(status["submit_adapter_status"], "disabled_stub")
        self.assertFalse(status["broker_submit_allowed"])
        self.assertFalse(status["submitted_to_broker"])
        self.assertEqual(status["order_boundary"], "read_only_no_order")


if __name__ == "__main__":
    unittest.main()
