from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT_DIR / "db" / "seeds" / "0005_sector_classification_seed.sql"


class SectorClassificationSeedTests(unittest.TestCase):
    def test_sector_seed_defines_nodes_and_memberships(self) -> None:
        sql = SEED_PATH.read_text(encoding="utf-8")

        self.assertIn("node_type", sql)
        self.assertIn("'sector'", sql)
        self.assertIn("'TECHNOLOGY'", sql)
        self.assertIn("'CONSUMER_DISCRETIONARY'", sql)
        self.assertIn("'ENERGY'", sql)
        self.assertIn("'FINANCIALS'", sql)
        self.assertIn("'FIXED_INCOME'", sql)
        self.assertIn("'BROAD_US_EQUITY'", sql)
        self.assertIn("'sector_membership'", sql)
        self.assertIn("insert into ref.instrument", sql)
        self.assertIn("'Apple Inc.'", sql)
        self.assertIn("'Alibaba Group Holding Limited'", sql)
        self.assertIn("delete from ref.instrument_classification_membership", sql)
        self.assertIn("insert into ref.instrument_classification_membership", sql)

    def test_sector_seed_covers_current_core_symbols(self) -> None:
        sql = SEED_PATH.read_text(encoding="utf-8")

        for symbol in ("AAPL", "MSFT", "NVDA", "TSLA", "XOM", "SPY", "QQQ", "TLT", "XLF", "XLE", "QUBT", "BABA"):
            self.assertIn(f"'{symbol}'", sql)

    def test_sector_seed_links_sectors_to_theme_graph(self) -> None:
        sql = SEED_PATH.read_text(encoding="utf-8")

        self.assertIn("'domain_to_sector'", sql)
        self.assertIn("'sector_to_theme'", sql)
        self.assertIn("'TECHNOLOGY', 'AI_SEMICONDUCTOR_CYCLE'", sql)
        self.assertIn("'ENERGY', 'ENERGY_GEOPOLITICS'", sql)


if __name__ == "__main__":
    unittest.main()
