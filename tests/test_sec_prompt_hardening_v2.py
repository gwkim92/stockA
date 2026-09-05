from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from stockanalysis.ingest.sec import ai_event_extract as sec
from stockanalysis.ai_agents.source_validation import probability, same_document
from tests.test_sec_ai_event_extract import _source_document_record, FakeAiEventExecutor

BAD_RATIOS = (float('nan'), float('inf'), -float('inf'), True, False, '0.8', None, -0.1, 1.1)
ROOT = Path(__file__).parent / 'fixtures'


def sec_value():
    return json.loads((ROOT / 'llm_sec_event_aapl_10k_structured.json').read_text())['event']


class SecScalarBoundaryTests(unittest.TestCase):
    def test_model_confidence_and_significance_reject_invalid_json_numbers(self):
        for field in ('confidence', 'significance_score'):
            for bad in BAD_RATIOS:
                with self.subTest(field=field, bad=bad):
                    value = sec_value(); value[field] = bad
                    with self.assertRaises(ValueError): sec.parse_structured_event_output(value)

    def test_zero_is_a_valid_value_without_changing_the_candidate_threshold(self):
        value = sec_value(); value.update(confidence=0, significance_score=0)
        parsed = sec.parse_structured_event_output(value)
        self.assertEqual((parsed.confidence, parsed.significance_score), (0, 0))
        with self.assertRaisesRegex(ValueError, 'below min_confidence'):
            sec.build_sec_event_candidate_from_structured_output(_source_document_record(), parsed, min_confidence=.8)

    def test_schema_valid_empty_optional_text_survives_canonical_revalidation(self):
        value = sec_value(); value.update(time_horizon='', impact_polarity='')
        parsed = sec.parse_structured_event_output(value)
        candidate = sec.build_sec_event_candidate_from_structured_output(
            _source_document_record(), parsed, min_confidence=.8)
        self.assertEqual((candidate.time_horizon, candidate.impact_polarity), ('', ''))
        self.assertEqual(sec.parse_structured_event_output(parsed.as_artifact_json()), parsed)

    def test_naive_invalid_and_non_timestamp_dates_are_rejected(self):
        for at in ('2026-09-05', '2026-09-05T12:00:00', '2026-02-30T12:00:00Z', '2026-09-05T12:00:00+99:00'):
            with self.subTest(at=at):
                value = sec_value(); value['event_at'] = at
                with self.assertRaises(ValueError): sec.parse_structured_event_output(value)

    def test_typed_runner_cannot_bypass_canonical_candidate_validation(self):
        valid = sec.parse_structured_event_output(sec_value())
        for bad in BAD_RATIOS:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                sec.build_sec_event_candidate_from_structured_output(_source_document_record(), replace(valid, confidence=bad), min_confidence=.8)

    def test_invalid_threshold_is_rejected_before_any_database_or_provider_io(self):
        for bad in BAD_RATIOS:
            executor = FakeAiEventExecutor()
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                sec.run_event_intelligence_llm_extract('fixture', config=object(), executor=executor,
                    llm_output_json_path=str(ROOT / 'llm_sec_event_aapl_10k_structured.json'), min_confidence=bad)
            self.assertEqual(executor.scalar_sql, [])
            self.assertEqual(executor.non_query_sql, [])

    def test_undeclared_authorization_fields_are_not_accepted(self):
        value = sec_value(); value['broker_submit_allowed'] = True
        with self.assertRaises(ValueError): sec.parse_structured_event_output(value)

    def test_invalid_runner_records_failure_without_canonical_event_insert(self):
        executor = FakeAiEventExecutor()
        good = sec.load_structured_event_provider_response(str(ROOT / 'llm_sec_event_aapl_10k_structured.json'),
            provider='fixture', model_name='fixture', reasoning_effort='low')
        bad = replace(good, event=replace(good.event, confidence=float('nan')))
        with self.assertRaises(ValueError):
            sec.run_event_intelligence_llm_extract('fixture', config=object(), executor=executor, provider='codex_oauth',
                max_input_chars=700, provider_runner=lambda *_: bad)
        self.assertFalse(any('insert into event.event' in sql for sql in executor.non_query_sql))
        self.assertTrue(any("status = 'failed'" in sql for sql in executor.non_query_sql))

    def test_invalid_chunk_budget_fails_before_io(self):
        for size in (True, False, None, -1, 0, 1.5, '700'):
            executor = FakeAiEventExecutor()
            with self.subTest(size=size), self.assertRaises(ValueError):
                sec.run_event_intelligence_llm_extract('fixture', config=object(), executor=executor,
                    llm_output_json_path=str(ROOT / 'llm_sec_event_aapl_10k_structured.json'), max_input_chars=size)
            self.assertEqual(executor.scalar_sql, [])
            self.assertEqual(executor.non_query_sql, [])
            with patch('stockanalysis.ingest.sec.ai_event_extract._load_raw_text') as raw:
                with self.assertRaises(ValueError):
                    sec.build_ai_document_chunk(_source_document_record(), max_input_chars=size)
                raw.assert_not_called()

    def test_chunk_document_mismatch_stops_before_codex(self):
        source = _source_document_record()
        chunk = replace(sec.build_ai_document_chunk(source, max_input_chars=700), document_id=999)
        with patch('stockanalysis.ingest.sec.ai_event_extract.subprocess.run') as runner:
            with self.assertRaisesRegex(ValueError, 'source_chunk_identity_mismatch'):
                sec.invoke_codex_oauth_structured_event_provider(source, chunk, 'default', 'low')
            runner.assert_not_called()

    def test_strict_decoder_rejects_ambiguous_numbers_and_duplicate_keys(self):
        for raw in ('{"confidence":0,"confidence":1}', '{"x":NaN}', '{"x":Infinity}',
                    '{"x":1e999}', '[]', '{} trailing'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                sec._loads_json_object(raw)
        self.assertEqual(sec._loads_json_object('```json\n{"confidence":0}\n```'), {'confidence': 0})

    def test_missing_declared_field_is_not_defaulted_into_a_candidate(self):
        for key in ('confidence', 'significance_score', 'event_at', 'uncertainty_notes'):
            value = sec_value(); del value[key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                sec.parse_structured_event_output(value)

    def test_safe_validation_errors_do_not_echo_model_payloads(self):
        secret = 'not-for-diagnostics-model-text'
        value = sec_value(); value['confidence'] = secret
        with self.assertRaises(ValueError) as raised:
            sec.parse_structured_event_output(value)
        self.assertNotIn(secret, str(raised.exception))

    def test_probability_and_document_ids_do_not_coerce_booleans(self):
        for value in BAD_RATIOS:
            with self.subTest(value=value), self.assertRaises(ValueError):
                probability(value)
        self.assertEqual(probability(0), 0)
        self.assertEqual(probability(1), 1)
        for value in (True, '1', 1.0, None, -1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                same_document(value, value)
        same_document(1, 1)


if __name__ == '__main__':
    unittest.main()
