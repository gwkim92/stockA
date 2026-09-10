import copy
import unittest

from stockanalysis.ai import equity_research_reporting as equity
from stockanalysis.ai_agents.prompt_contract import render_source_data
from stockanalysis.frontend.live_adapter import (
    _build_recommendation_list_boundary_payload,
    _build_recommendation_professional_decision_waterfall_payload,
    _build_stock_equity_research_payload,
    _build_stock_market_data_provider_payload,
    _build_cycle_state_item_payload,
)
from tests.test_equity_research_reporting import _context_payload
from tests.test_equity_research_contract_v3 import response


class PurposeFitRecoveryTests(unittest.TestCase):
    def test_cycle_list_preserves_breadth_as_its_own_metric(self):
        row = _build_cycle_state_item_payload({'features': {'market_breadth': 0, 'valuation_score': .7}})
        self.assertEqual(row['features']['market_breadth'], 0)
        self.assertIsNone(row['features']['fundamental_quality'])
        self.assertEqual(row['features']['valuation_score'], .7)

    def test_oversized_valuation_is_omitted_whole_and_disclosed_without_losing_thesis(self):
        context = _context_payload()
        context['valuations'] = [{'method': 'sotp', 'full_evidence': 'x' * 42000}]
        original = copy.deepcopy(context)
        selected = equity._bounded_context_for_prompt(context, max_context_chars=16000)
        self.assertEqual(context, original)
        self.assertEqual(selected['thesis'], context['thesis'])
        self.assertEqual(selected['valuations'], [])
        self.assertEqual(selected['input_selection']['omitted']['valuations'], 1)
        self.assertTrue(selected['recent_events'])
        self.assertLessEqual(len(render_source_data(selected, max_chars=16000)), 16000)
        self.assertEqual(equity._bounded_context_for_prompt(selected, max_context_chars=16000), selected)
        output = equity._sanitize_output(response().output, context=selected)
        self.assertIn('valuations', output.risks[0])
        self.assertEqual(equity._sanitize_output(output, context=selected), output)

    def test_list_and_detail_share_input_eligibility_before_and_after_outcome(self):
        for thesis, component, evidence, blocked, measured, expected in (
            (True, True, True, False, False, True),
            (True, True, True, False, True, True),
            (False, True, True, False, False, False),
            (True, False, False, False, False, False),
            (True, True, False, False, False, False),
            (True, True, True, True, True, False),
        ):
            with self.subTest(thesis=thesis, component=component, evidence=evidence, blocked=blocked, measured=measured):
                outcome = {'measurement_end_date': '2026-09-10', 'label': 'positive'} if measured else {}
                components = [{'component_name': 'cycle_score' if evidence else 'momentum_score',
                               'provenance': {'source_type': 'event_or_ai_evidence' if evidence else 'market_feature'}}] if component else []
                common = dict(linked_thesis_id=1 if thesis else None, outcome=outcome)
                listing = _build_recommendation_list_boundary_payload(
                    {}, **common, source_blocked=blocked,
                    evidence={'score_component_count': len(components), 'ai_or_event_component_count': int(evidence)},
                )
                detail = _build_recommendation_professional_decision_waterfall_payload(
                    **common, score_components=components, equity_research=None,
                    industry_competitive_position=None, financial_statement_model=None,
                    valuation_target_range=None, evidence_trace={}, evidence_review={},
                    professional_source_guardrail={'blocked': blocked}, symbol='NVDA',
                    as_of_date='2026-09-10', recommendation='watch', score=None,
                )
                self.assertEqual(listing, detail['decision_boundary'])
                self.assertEqual(listing['paper_validation_input_allowed'], expected)
                self.assertFalse(listing['automatic_order_allowed'])
                self.assertFalse(listing['broker_submit_allowed'])

    def test_structurally_complete_fallback_is_never_content_reviewed(self):
        artifact = dict(artifact_id=1, provider='fixture', model_name='equity-research-fallback-v1',
                        title='NVDA', korean_summary='요약', key_points=['주장'], catalysts=['촉매'],
                        risks=['위험'], invalidation_conditions=['조건'], source_document_ids=[1])
        report = _build_stock_equity_research_payload(artifact)
        self.assertEqual(report['generation']['mode'], 'fallback')
        self.assertEqual(report['generation']['structural_status'], 'complete')
        self.assertEqual(report['generation']['content_review_status'], 'not_recorded')
        artifact.update(provider='codex_oauth', model_name='gpt-5.6-terra')
        self.assertEqual(_build_stock_equity_research_payload(artifact)['generation']['mode'], 'ai')

    def test_existing_price_without_freshness_policy_is_unknown(self):
        result = _build_stock_market_data_provider_payload({}, price_bars=[{'trade_date': '2026-09-04', 'provider': 'canonical'}])
        self.assertEqual(result['analysis_price_source']['freshness_status'], 'unknown')
        result = _build_stock_market_data_provider_payload(
            {'freshness_status': 'fresh', 'freshness_policy': 'calendar_age_within_7_days', 'freshness_age_days': 6}, price_bars=[])
        self.assertEqual(result['analysis_price_source']['freshness_age_days'], 6)


if __name__ == '__main__':
    unittest.main()
