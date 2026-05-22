from __future__ import annotations

import unittest
from pathlib import Path


class PortfolioAllocationPolicyMigrationTests(unittest.TestCase):
    def test_migration_creates_policy_table_and_default_guardrail(self) -> None:
        migration = Path("db/migrations/0015_portfolio_allocation_policy.sql").read_text(encoding="utf-8")

        self.assertIn("create table if not exists portfolio.allocation_policy", migration)
        self.assertIn("max_single_position_weight numeric(8,4)", migration)
        self.assertIn("min_rebalance_target_weight numeric(8,4)", migration)
        self.assertIn("allocation_policy_identity_uidx", migration)
        self.assertIn("global_default_long_term_guardrail", migration)
        self.assertIn("0.2500", migration)
        self.assertIn("0.1000", migration)


if __name__ == "__main__":
    unittest.main()
