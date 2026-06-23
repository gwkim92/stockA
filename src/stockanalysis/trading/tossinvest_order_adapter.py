from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


class TossInvestOrderAdapterDisabledError(RuntimeError):
    """Raised before any TossInvest live order HTTP path can be reached."""


@dataclass(frozen=True)
class TossInvestOrderRequest:
    account_seq: str
    symbol: str
    side: str
    quantity: Decimal
    order_type: str
    limit_price: Decimal | None = None
    currency: str | None = None


@dataclass(frozen=True)
class TossInvestOrderModifyRequest:
    account_seq: str
    order_id: str
    quantity: Decimal | None = None
    limit_price: Decimal | None = None


@dataclass(frozen=True)
class TossInvestOrderCancelRequest:
    account_seq: str
    order_id: str


class TossInvestOrderAdapter:
    submit_adapter_status = "disabled_stub"
    broker_submit_allowed = False
    order_boundary = "read_only_no_order"

    def submit_order(self, request: TossInvestOrderRequest) -> dict[str, object]:
        raise TossInvestOrderAdapterDisabledError(_disabled_message("submit"))

    def modify_order(self, request: TossInvestOrderModifyRequest) -> dict[str, object]:
        raise TossInvestOrderAdapterDisabledError(_disabled_message("modify"))

    def cancel_order(self, request: TossInvestOrderCancelRequest) -> dict[str, object]:
        raise TossInvestOrderAdapterDisabledError(_disabled_message("cancel"))

    def status(self) -> dict[str, object]:
        return {
            "submit_adapter_status": self.submit_adapter_status,
            "broker_submit_allowed": self.broker_submit_allowed,
            "automatic_order_allowed": False,
            "submitted_to_broker": False,
            "order_boundary": self.order_boundary,
        }


def _disabled_message(action: str) -> str:
    return (
        f"TossInvest order {action} is disabled in readonly foundation v1; "
        "no broker HTTP request was attempted."
    )
