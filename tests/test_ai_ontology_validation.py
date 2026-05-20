from datetime import date
import unittest

from stockanalysis.ai.ontology_validation import render_ontology_lite_validation_sql


class AiOntologyValidationTests(unittest.TestCase):
    def test_ontology_validation_renders_read_only_consistency_checks(self) -> None:
        sql = render_ontology_lite_validation_sql(as_of_date=date(2026, 5, 19))
        lowered = sql.lower()

        self.assertIn("ref.classification_edge", sql)
        self.assertIn("left join ref.classification_node parent_node", sql)
        self.assertIn("left join ref.classification_node child_node", sql)
        self.assertIn("invalid_relation_type", sql)
        self.assertIn("overlapping_classification_edge_window", sql)
        self.assertIn("ref.instrument_classification_membership", sql)
        self.assertIn("inferred_membership_without_evidence", sql)
        self.assertIn("source_document_id is null", lowered)
        self.assertIn("confidence is null", lowered)
        self.assertIn("'2026-05-19'::date", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_ontology_validation_allows_custom_relation_types(self) -> None:
        sql = render_ontology_lite_validation_sql(
            as_of_date=date(2026, 5, 19),
            allowed_relation_types=("parent_child", "theme_contains_sector"),
        )

        self.assertIn("'parent_child'", sql)
        self.assertIn("'theme_contains_sector'", sql)
        self.assertNotIn("'same_theme'", sql)

    def test_ontology_validation_rejects_empty_relation_types(self) -> None:
        with self.assertRaises(ValueError):
            render_ontology_lite_validation_sql(as_of_date=date(2026, 5, 19), allowed_relation_types=())


if __name__ == "__main__":
    unittest.main()
