from copy import deepcopy
import unittest

from stockanalysis.frontend.live_adapter import _build_portfolio_review_feedback_item_payload


class FeedbackDisplayTests(unittest.TestCase):
    def test_existing_outcome_and_guardrails_are_preserved(self):
        for value in (0, -0.029326, '0.0', 0.04):
            source = {'feedback_status': 'needs_more_data', 'feedback_reason': 'stored reason',
                      'evidence': {'price_evidence': {'price_return_pct': value}}}
            before = deepcopy(source)
            row = _build_portfolio_review_feedback_item_payload(source)
            self.assertEqual(row['feedback_display_label'], '판단 보류')
            self.assertEqual(row['feedback_status'], 'needs_more_data')
            self.assertEqual(row['feedback_reason'], 'stored reason')
            self.assertFalse(row['automatic_order_allowed'])
            self.assertFalse(row['broker_submit_allowed'])
            self.assertEqual(source, before)

    def test_missing_invalid_and_nonfinite_values_are_not_measurements(self):
        for value in (None, '', 'invalid', 'NaN', 'Infinity', '-Infinity', True):
            row = _build_portfolio_review_feedback_item_payload({
                'feedback_status': 'needs_more_data',
                'evidence': {'price_evidence': {'price_return_pct': value}}})
            self.assertEqual(row['feedback_display_label'], '수치 근거 부족')

    def test_outcome_measurement_works_without_price(self):
        for source in ('recommendation_outcome', 'thesis_outcome'):
            row = _build_portfolio_review_feedback_item_payload({
                'feedback_status': 'needs_more_data', 'evidence': {source: {'alpha_pct': 0}}})
            self.assertEqual(row['feedback_display_label'], '판단 보류')

    def test_other_statuses_are_not_reinterpreted(self):
        for status in ('too_early', 'validated', 'contradicted', ''):
            row = _build_portfolio_review_feedback_item_payload({'feedback_status': status})
            self.assertNotIn('feedback_display_label', row)
            self.assertEqual(row['feedback_status'], status)

    def test_paper_blocker_is_not_hidden_by_numeric_price(self):
        row = _build_portfolio_review_feedback_item_payload({
            'feedback_status': 'needs_more_data', 'evidence': {
                'price_evidence': {'price_return_pct': 0}, 'paper_validation': {'symbol_blocked': True}}})
        self.assertEqual(row['feedback_display_label'], '가상 매매 검증 차단')
