import unittest
from copy import deepcopy
from datetime import datetime, timezone
from unittest.mock import patch
from stockanalysis.frontend.live_adapter import resolve_live_frontend_response


class SourceIntegrityVisibilityTests(unittest.TestCase):
    def test_conflict_is_visible_without_exposing_mixed_translation_or_excerpt(self):
        source = {"document_id": "source-document-22", "title": "Drone earnings", "source_type": "news_rss_identity_conflict",
                  "korean_title": "Old unrelated title", "korean_summary": "Old summary", "translation_confidence": .9,
                  "symbol": "AAPL", "excerpts": [{"chunk_id": 1, "summary": "Old chunk"}], "linked_evidence": []}
        before = deepcopy(source)
        with patch("stockanalysis.frontend.live_adapter.load_frontend_source_document_detail_state", return_value=source):
            payload = resolve_live_frontend_response("/api/source-documents/source-document-22", config=None, executor=object(),
                generated_at=datetime(2026,9,11,tzinfo=timezone.utc))["data"]
        self.assertEqual(payload["integrity_status"], "quarantined_identity_conflict")
        self.assertEqual(payload["title"], "Drone earnings")
        self.assertIsNone(payload["korean_title"])
        self.assertIsNone(payload["korean_summary"])
        self.assertIsNone(payload["translation_confidence"])
        self.assertEqual(payload["excerpts"], [])
        self.assertEqual(payload["symbol"], "UNKNOWN")
        self.assertEqual(source, before)
