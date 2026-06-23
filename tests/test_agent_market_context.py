from __future__ import annotations

import unittest
from datetime import date

from stockanalysis.ai.market_context import agent_market_context_contract, render_agent_market_context_sql


class AgentMarketContextTests(unittest.TestCase):
    def test_agent_market_context_is_postgres_read_model_without_toss_http(self) -> None:
        sql = render_agent_market_context_sql(
            symbols=("AAPL", "NVDA"),
            as_of_date=date(2026, 6, 23),
            include_live_account=False,
        )

        self.assertIn("market.daily_price_bar", sql)
        self.assertIn("market.tossinvest_daily_candle_snapshot", sql)
        self.assertIn("market.tossinvest_market_microdata_snapshot", sql)
        self.assertIn("portfolio.position_snapshot", sql)
        self.assertIn("'direct_tossinvest_http_allowed', false", sql)
        self.assertNotIn("openapi.tossinvest", sql.lower())
        self.assertNotIn("TossInvestSource", sql)

    def test_agent_market_context_can_include_live_account_only_when_requested(self) -> None:
        default_sql = render_agent_market_context_sql(
            symbols=("AAPL",),
            as_of_date=date(2026, 6, 23),
            include_live_account=False,
        )
        live_sql = render_agent_market_context_sql(
            symbols=("AAPL",),
            as_of_date=date(2026, 6, 23),
            include_live_account=True,
        )

        self.assertIn("where false", default_sql)
        self.assertIn("Toss Real Readonly", live_sql)
        self.assertFalse(agent_market_context_contract()["broker_submit_allowed"])


if __name__ == "__main__":
    unittest.main()
