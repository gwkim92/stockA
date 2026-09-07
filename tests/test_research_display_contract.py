from __future__ import annotations

from copy import deepcopy
import json
import unittest

from stockanalysis.frontend.research_display_contract import prepare_equity_display, CLAIM_FIELDS, MAX_DATABASE_ID


def artifact():
    return dict(artifact_id=42, source_run_id=17, as_of_date='2026-09-05',
                title='AAPL 검증용 리서치', korean_summary='숫자와 가정은 별도로 대조한다.',
                provider='fixture', key_points=['정상 주장'], catalysts=[], risks=[],
                invalidation_conditions=[], source_document_ids=[7001, 7002],
                valuation_sensitivity={'confidence': 0})


class ResearchDisplayContractTests(unittest.TestCase):
    def test_valid_record_and_zero_are_preserved_without_mutating_input(self):
        raw = artifact(); before = deepcopy(raw)
        safe, quality = prepare_equity_display(raw)
        self.assertEqual(safe, raw)
        self.assertEqual(raw, before)
        self.assertEqual(safe['valuation_sensitivity']['confidence'], 0)
        self.assertEqual(quality['status'], 'complete')
        self.assertIsNot(safe['key_points'], raw['key_points'])

    def test_known_empty_lists_stay_complete(self):
        raw = artifact()
        for field in (*CLAIM_FIELDS, 'source_document_ids'): raw[field] = []
        safe, quality = prepare_equity_display(raw)
        self.assertEqual(safe, raw)
        self.assertEqual(quality['status'], 'complete')

    def test_missing_and_null_fields_are_not_described_as_known_empty(self):
        for value in (None, 'missing'):
            raw = artifact()
            if value is None: raw['risks'] = None
            else: raw.pop('risks')
            safe, quality = prepare_equity_display(raw)
            self.assertEqual(safe['risks'], [])
            self.assertEqual(quality['unavailable_fields'], ['risks'])
            self.assertEqual(quality['status'], 'partial')

    def test_claim_lists_cannot_turn_numbers_booleans_or_objects_into_prose(self):
        for field in CLAIM_FIELDS:
            for invalid in (True, 7, None, {'instruction': 'not narrative'}, ['nested']):
                with self.subTest(field=field, value=invalid):
                    raw = artifact(); raw[field] = ['valid fragment', invalid]
                    safe, quality = prepare_equity_display(raw)
                    self.assertEqual(safe[field], [])
                    self.assertEqual(quality['invalid_fields'], [field])
                    self.assertEqual(quality['status'], 'invalid_fields')

    def test_wrong_collection_container_is_rejected_whole(self):
        for invalid in ('claims as text', {'claim': 'text'}, ('tuple',)):
            raw = artifact(); raw['key_points'] = invalid
            safe, quality = prepare_equity_display(raw)
            self.assertEqual(safe['key_points'], [])
            self.assertIn('key_points', quality['invalid_fields'])

    def test_titles_and_summaries_are_not_stringified_objects(self):
        raw = artifact(); raw['title'] = {'fake': 'title'}; raw['korean_summary'] = False
        safe, quality = prepare_equity_display(raw)
        self.assertEqual(safe['title'], '')
        self.assertEqual(safe['korean_summary'], '')
        self.assertEqual(quality['invalid_fields'], ['title', 'korean_summary'])

    def test_document_ids_are_exact_positive_database_identifiers(self):
        raw = artifact(); raw['source_document_ids'] = [1, '2', MAX_DATABASE_ID, str(MAX_DATABASE_ID)]
        safe, quality = prepare_equity_display(raw)
        self.assertEqual(safe['source_document_ids'], raw['source_document_ids'])
        self.assertEqual(quality['status'], 'complete')

    def test_invalid_source_inventory_does_not_emit_a_partial_trusted_list(self):
        for invalid in (True, False, -1, 0, 1.5, {}, None, '01', '-1', '1e3', '../private', 'source-document-unknown', MAX_DATABASE_ID + 1):
            raw = artifact(); raw['source_document_ids'] = [7001, invalid]
            safe, quality = prepare_equity_display(raw)
            self.assertEqual(safe['source_document_ids'], [])
            self.assertEqual(quality['invalid_fields'], ['source_document_ids'])

    def test_existing_quality_claim_is_not_trusted(self):
        raw = artifact(); raw['key_points'] = [False]; raw['data_quality'] = {'status': 'complete'}
        _, quality = prepare_equity_display(raw)
        self.assertEqual(quality['status'], 'invalid_fields')

    def test_real_producer_uses_validation_before_coercion(self):
        from stockanalysis.frontend.live_adapter import _build_stock_equity_research_payload
        raw = artifact(); raw['key_points'] = [False, {'invented': 'claim'}]; raw['source_document_ids'] = [True]
        result = _build_stock_equity_research_payload(raw)
        self.assertEqual(result['key_points'], [])
        self.assertEqual(result['source_document_ids'], [])
        self.assertEqual(result['data_quality']['status'], 'invalid_fields')
        self.assertNotIn('invented', json.dumps(result))

    def test_real_producer_keeps_valid_id_conversion_and_null_artifact_behavior(self):
        from stockanalysis.frontend.live_adapter import _build_stock_equity_research_payload
        self.assertIsNone(_build_stock_equity_research_payload({}))
        result = _build_stock_equity_research_payload(artifact())
        self.assertEqual(result['source_document_ids'], ['source-document-7001', 'source-document-7002'])
        self.assertEqual(result['key_points'], ['정상 주장'])
        self.assertEqual(result['data_quality']['status'], 'complete')


if __name__ == '__main__': unittest.main()
