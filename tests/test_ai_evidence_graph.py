from datetime import date
import unittest

from stockanalysis.ai.evidence_graph import render_instrument_evidence_neighborhood_sql


class AiEvidenceGraphTests(unittest.TestCase):
    def test_evidence_neighborhood_uses_existing_postgres_graph_tables(self) -> None:
        sql = render_instrument_evidence_neighborhood_sql(primary_symbol="AAPL", as_of_date=date(2024, 11, 1))

        self.assertIn("ref.instrument", sql)
        self.assertIn("ref.classification_node", sql)
        self.assertIn("ref.instrument_classification_membership", sql)
        self.assertIn("event.event_classification_impact", sql)
        self.assertIn("event.event_instrument_impact", sql)
        self.assertIn("signal.investment_thesis", sql)
        self.assertIn("signal.recommendation", sql)
        self.assertIn("portfolio.position_snapshot", sql)
        self.assertIn("ai.extraction_artifact", sql)
        self.assertIn("ai.document_chunk", sql)
        self.assertIn("ai.embedding_index", sql)
        self.assertIn("ingest.source_document", sql)
        self.assertIn("document.korean_title", sql)
        self.assertIn("document.korean_summary", sql)
        self.assertIn("document.translation_confidence", sql)
        self.assertIn("chunk.chunk_metadata", sql)
        self.assertIn("raw_recent_events as", sql)
        self.assertIn("distinct on (coalesce(nullif(lower(title), ''), source_checksum, 'event:' || event_id::text))", sql)

    def test_evidence_neighborhood_is_read_only_and_bounded(self) -> None:
        sql = render_instrument_evidence_neighborhood_sql(primary_symbol="NVDA", as_of_date=date(2026, 5, 19), limit=12)
        lowered = sql.lower()

        self.assertIn("'NVDA'", sql)
        self.assertIn("'2026-05-19'::date", sql)
        self.assertIn("limit 12", lowered)
        self.assertIn("https://news.google.com/%", sql)
        self.assertIn("chunk.chunk_metadata ->> 'source_text_kind'", sql)
        self.assertIn("source_checksum", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)
        self.assertNotIn("create table", lowered)

    def test_evidence_neighborhood_rejects_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            render_instrument_evidence_neighborhood_sql(primary_symbol="", as_of_date=date(2024, 11, 1))
        with self.assertRaises(ValueError):
            render_instrument_evidence_neighborhood_sql(primary_symbol="AAPL", as_of_date=date(2024, 11, 1), limit=0)


if __name__ == "__main__":
    unittest.main()
