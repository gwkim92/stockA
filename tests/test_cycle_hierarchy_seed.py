from pathlib import Path
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT_DIR / "db" / "seeds" / "0004_cycle_hierarchy_seed.sql"


class CycleHierarchySeedTests(unittest.TestCase):
    def test_seed_defines_required_cycle_hierarchy_nodes(self) -> None:
        sql = SEED_PATH.read_text()

        for code in (
            "MACRO_RATES_FED",
            "MACRO_INFLATION",
            "MACRO_LIQUIDITY",
            "MACRO_GROWTH",
            "ENERGY_GEOPOLITICS",
            "TECH_DOMAIN",
            "AI_SEMICONDUCTOR_CYCLE",
            "QUANTUM_COMPUTING_POLICY",
        ):
            self.assertIn(code, sql)

    def test_seed_defines_hierarchical_edges_for_macro_domain_theme_flow(self) -> None:
        sql = SEED_PATH.read_text()

        self.assertIn("macro_to_domain", sql)
        self.assertIn("domain_to_theme", sql)
        self.assertIn("macro_to_theme", sql)
        self.assertIn("'MACRO_RATES_FED', 'TECH_DOMAIN'", sql)
        self.assertIn("'TECH_DOMAIN', 'AI_SEMICONDUCTOR_CYCLE'", sql)
        self.assertIn("'TECH_DOMAIN', 'QUANTUM_COMPUTING_POLICY'", sql)

    def test_seed_adds_starter_exposures_for_hierarchical_propagation(self) -> None:
        sql = SEED_PATH.read_text()

        self.assertIn("insert into ref.instrument_factor_exposure", sql.lower())
        self.assertIn("'QUBT', 'QUANTUM_COMPUTING_POLICY'", sql)
        self.assertIn("'QQQ', 'MACRO_LIQUIDITY'", sql)
        self.assertIn("'TLT', 'MACRO_INFLATION'", sql)
        self.assertIn("'NVDA', 'TECH_DOMAIN'", sql)

    def test_seed_is_idempotent(self) -> None:
        sql = SEED_PATH.read_text().lower()

        self.assertIn("on conflict (taxonomy_family, node_type, code) do update", sql)
        self.assertIn("on conflict (parent_node_id, child_node_id, relation_type, valid_from) do update", sql)
        self.assertIn("on conflict (instrument_id, node_id, exposure_type, valid_from) do update", sql)


if __name__ == "__main__":
    unittest.main()
