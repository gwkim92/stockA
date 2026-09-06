from __future__ import annotations

from datetime import date, datetime
import copy
import json
import unittest

from stockanalysis.ai.equity_research_reporting import (
    DEFAULT_TEMPLATE_VERSION, _bounded_context_for_prompt,
    build_codex_oauth_equity_research_prompt, build_equity_research_request_hash,
    render_equity_research_context_sql,
)
from tests.test_equity_research_reporting import _context_payload


class EquityCutoffContractTests(unittest.TestCase):
    def test_renderer_rejects_datetime_and_non_date_input(self):
        for value in (datetime(2026, 9, 5), '2026-09-05', None, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                render_equity_research_context_sql(symbol='AAPL', as_of_date=value)

    def test_renderer_rejects_invalid_limit_types(self):
        for value in (True, 1.5, '8', 0, 51):
            with self.subTest(value=value), self.assertRaises(ValueError):
                render_equity_research_context_sql(symbol='AAPL', as_of_date=date(2026, 9, 5), limit=value)

    def test_explicit_utc_exclusive_bound_is_used_for_both_sources(self):
        sql = render_equity_research_context_sql(symbol='AAPL', as_of_date=date(2026, 9, 5))
        bound = "(('2026-09-05'::date + 1)::timestamp at time zone 'UTC')"
        self.assertIn(f'thesis.created_at < {bound}', sql)
        self.assertIn(f'event_row.event_at < {bound}', sql)
        self.assertNotIn('event_row.event_at <=', sql)

    def test_current_active_status_is_not_a_historical_tiebreaker(self):
        sql = render_equity_research_context_sql(symbol='AAPL', as_of_date=date(2026, 9, 5))
        thesis = sql.split('latest_thesis as (')[1].split('recent_events as (')[0]
        self.assertNotIn("case when thesis.status = 'active'", thesis)
        self.assertIn('thesis.created_at desc', thesis)
        self.assertIn('thesis.thesis_id desc', thesis)
        self.assertIn('select thesis_id from latest_recommendation', thesis)

    def test_temporal_policy_and_source_dates_are_visible(self):
        sql = render_equity_research_context_sql(symbol='AAPL', as_of_date=date(2026, 9, 5))
        self.assertIn("'point_in_time_complete', false", sql)
        self.assertIn('thesis.created_at,', sql)
        self.assertIn('then thesis.closed_at end as closed_at', sql)
        self.assertIn('utc_creation_event_cutoff_v1', sql)

    def test_query_remains_read_only_and_quotes_symbol(self):
        sql = render_equity_research_context_sql(symbol="AAPL' OR '1'='1", as_of_date=date(2026, 9, 5))
        self.assertIn("'AAPL'' OR ''1''=''1'", sql)
        for write in ('insert into ', 'update ', 'delete from '):
            self.assertNotIn(write, sql.lower())

    def test_bounded_source_retains_temporal_policy_without_mutation(self):
        context = _context_payload()
        context['query']['temporal_policy'] = 'utc_creation_event_cutoff_v1'
        context['query']['point_in_time_complete'] = False
        original = copy.deepcopy(context)
        bounded = _bounded_context_for_prompt(context, max_context_chars=16000)
        self.assertEqual(bounded['query'], context['query'])
        self.assertEqual(context, original)

    def test_prompt_has_exact_policy_and_does_not_claim_historical_versioning(self):
        context = _context_payload()
        context['query']['point_in_time_complete'] = False
        prompt = build_codex_oauth_equity_research_prompt(context, max_context_chars=16000)
        framed = prompt.split('<source_data>\n')[1].split('\n</source_data>')[0]
        self.assertIs(json.loads(framed)['query']['point_in_time_complete'], False)
        self.assertIn('not a complete knowledge-at-the-time snapshot', prompt)
        self.assertIn('current stored body/status', prompt)

    def test_temporal_policy_is_part_of_request_fingerprint(self):
        context = _context_payload()
        args = dict(provider='fixture', model_name='fixture', prompt_template_id=1, max_context_chars=16000)
        initial = build_equity_research_request_hash(context=context, **args)
        context['query']['temporal_policy'] = 'utc_creation_event_cutoff_v1'
        self.assertNotEqual(initial, build_equity_research_request_hash(context=context, **args))

    def test_prompt_template_version_changes_with_temporal_contract(self):
        self.assertEqual(DEFAULT_TEMPLATE_VERSION, '2026-09-06-equity-cutoff-v1')
