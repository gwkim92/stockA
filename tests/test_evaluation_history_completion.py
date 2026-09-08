import copy
import hashlib
import unittest
from unittest.mock import patch

from stockanalysis.frontend.recommendation_eval_comparison import (
    verify_snapshot, compare_snapshot, parse_comparison_request, render_comparison_sql,
)
from stockanalysis.frontend.recommendation_eval_history import EvaluationHistoryError, HistoryRequest
from stockanalysis.operations.recommendation_eval_persistence import canonical_snapshot_json


def frozen():
    raw = {'recommendation': {'action': 'watch', 'total_score': 0, 'status': 'active', 'thesis_id': 3},
           'thesis': {'summary': '평가 당시 근거', 'invalidation_conditions': ['수요 감소']},
           'selected_outcome': None}
    return {'snapshot_json': raw, 'snapshot_sha256': hashlib.sha256(canonical_snapshot_json(raw).encode()).hexdigest(),
            'primary_symbol': 'AAPL', 'source_recommendation_id': '1'}


class CompletionTests(unittest.TestCase):
    def test_hash_and_source_mutation_do_not_rewrite_history(self):
        row = frozen(); before = copy.deepcopy(row)
        self.assertEqual(verify_snapshot(row), 'verified')
        current = {'recommendation': {'action': 'buy', 'total_score': 0, 'status': 'active', 'thesis_id': 3},
                   'thesis': None, 'primary_symbol': 'AAPL', 'later_outcome': {'alpha_pct': 0}}
        result = compare_snapshot(row, current)
        self.assertEqual(result['status'], 'changed')
        self.assertEqual([x['field'] for x in result['changes']], ['recommendation.action', 'thesis.summary', 'thesis.invalidation_conditions'])
        self.assertEqual(result['later_outcome']['alpha_pct'], 0)
        self.assertEqual(row, before)

    def test_corrupt_missing_and_unavailable_are_distinct(self):
        row = frozen()
        self.assertEqual(compare_snapshot(row, None)['status'], 'source_missing')
        row['snapshot_json']['recommendation']['total_score'] = 2
        self.assertEqual(verify_snapshot(row), 'mismatch')
        self.assertEqual(compare_snapshot(row, {})['status'], 'untrusted_history')
        row['snapshot_json'] = None
        self.assertEqual(verify_snapshot(row), 'unverifiable')

    def test_bigint_and_pagination_boundaries(self):
        self.assertEqual(parse_comparison_request('/api/recommendation-evaluation-comparisons/eval-run-9?limit=2&after=1'), HistoryRequest(9, 2, 1))
        for suffix in ['', '/eval-run-01', '/eval-run-1?before=2', '/eval-run-1?after=0', '/eval-run-1?limit=101']:
            with self.subTest(suffix=suffix), self.assertRaises(EvaluationHistoryError):
                parse_comparison_request('/api/recommendation-evaluation-comparisons' + suffix)

    def test_sql_limits_later_outcomes_to_comparable_dates_and_horizon(self):
        sql = render_comparison_sql(9, ['1', '2'])
        self.assertIn('o.horizon_days =', sql)
        self.assertIn('o.measurement_end_date > e.as_of_date', sql)
        self.assertIn('o.measurement_end_date <= current_date', sql)
        self.assertIn('s.eval_run_id = 9', sql)
        self.assertIn('s.snapshot_id in (1,2)', sql)
        for bad in ['0', '01', '1;delete', '9223372036854775808']:
            with self.assertRaises(EvaluationHistoryError): render_comparison_sql(9, [bad])

    def test_symbol_identity_mismatch_is_not_a_new_recommendation(self):
        self.assertEqual(compare_snapshot(frozen(), {'recommendation': {}, 'primary_symbol': 'OTHER'})['status'], 'source_identity_mismatch')

    def test_copied_display_fields_cannot_disagree_with_hashed_content(self):
        row=frozen(); row['recommendation_action']='buy'
        self.assertEqual(verify_snapshot(row),'mismatch')

    def test_comparison_failure_preserves_history_and_integrity(self):
        from stockanalysis.frontend.recommendation_eval_comparison import resolve_evaluation_comparison
        row = {**frozen(), 'snapshot_id':'1'}
        history = {'run': {'eval_run_id':'9'}, 'snapshots':[row], 'pagination':{}}
        class Denied:
            def execute_scalar(self, sql): raise RuntimeError('synthetic denial')
        with patch('stockanalysis.frontend.recommendation_eval_comparison.resolve_evaluation_history', return_value=history):
            result=resolve_evaluation_comparison('/api/recommendation-evaluation-comparisons/eval-run-9',source='live',executor=Denied())
        self.assertEqual(result['history'],history)
        self.assertEqual(result['comparison_status'],'unavailable')
        self.assertEqual(result['comparisons'][0]['integrity'],'verified')

    def test_authenticated_http_dispatch_and_write_denial(self):
        from fastapi.testclient import TestClient
        from stockanalysis.frontend.api_server import create_app
        from stockanalysis.frontend.runtime_policy import FrontendRuntimePolicy
        from stockanalysis.frontend.recommendation_eval_comparison import API_PATH
        from tests.test_recommendation_eval_history import FakeExecutor
        policy=FrontendRuntimePolicy(profile='local',source='live',auth_mode='read-token',read_token='comparison-test')
        executor=FakeExecutor({'run': {'eval_run_id':'9','eval_name':'recommendation_quality_calibration','pipeline_run_id':None,'snapshot_count':0,'stored_config':{'snapshot_count':0,'snapshot_schema_version':'recommendation-eval-snapshot-v1'}}, 'snapshots':[]})
        with TestClient(create_app(runtime_policy=policy,executor=executor,observability_mode='disabled')) as client:
            target=API_PATH+'/eval-run-9'
            self.assertEqual(client.get(target).status_code,401)
            headers={'Authorization':'Bearer comparison-test'}
            response=client.get(target,headers=headers)
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json()['contract_version'],'recommendation-eval-comparison-v1')
            self.assertIn('no-store',response.headers['cache-control'])
            self.assertEqual(client.post(target,headers=headers).status_code,405)
            self.assertEqual(client.get(API_PATH+'/eval-run-01',headers=headers).status_code,400)
