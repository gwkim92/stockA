from __future__ import annotations
import unittest
from stockanalysis.frontend.research_display_contract import prepare_equity_display
from stockanalysis.frontend.live_adapter import _build_stock_equity_research_payload
from tests.test_research_display_contract import artifact


class ResearchDisplayAliasTests(unittest.TestCase):
    def test_existing_named_source_and_numeric_opaque_ids_are_preserved(self):
        ids = ['source-document-aapl-2024-10k-20240928', 'source-document-7002', 7003]
        data = {**artifact(), 'source_document_ids': ids}
        result = _build_stock_equity_research_payload(data)
        self.assertEqual(result['source_document_ids'], ids[:2] + ['source-document-7003'])
        self.assertEqual(result['data_quality']['status'], 'complete')

    def test_opaque_prefix_does_not_make_bad_identifiers_valid(self):
        for suffix in ('unknown', 'True', 'False', 'None', 'null', '0', '-1', '01', 'a/b', '..', 'a?x', 'a%20b', 'a b'):
            with self.subTest(suffix=suffix):
                data = {**artifact(), 'source_document_ids': ['source-document-' + suffix]}
                safe, quality = prepare_equity_display(data)
                self.assertEqual(safe['source_document_ids'], [])
                self.assertIn('source_document_ids', quality['invalid_fields'])


if __name__ == '__main__':
    unittest.main()
