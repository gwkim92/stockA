from datetime import date
import io
import unittest
from unittest.mock import patch

from stockanalysis.operations.portfolio_review_feedback_maintenance import run_portfolio_review_feedback_maintenance
from stockanalysis.operations.portfolio_review_feedback_action_router import build_portfolio_review_feedback_action_router_decision
from tests.test_portfolio_review_feedback_action_router import _context


class MaintenanceFixture:
    def __init__(self, stage=0, stuck=False, concurrent=False, fail_child=False):
        self.stage=stage; self.stuck=stuck; self.concurrent=concurrent; self.fail_child=fail_child
        self.calls=[]; self.cadence_calls=[]; self.eval_id=100; self.context=None

    def cadence(self, **kwargs):
        self.cadence_calls.append(kwargs['execute']); self.eval_id+=1
        status, action=[('run_feedback_now','execute_feedback'),('run_calibration_now','execute_calibration'),('calibration_current','observe')][self.stage]
        self.context=_context(cadence_status=status,action_type=action,should_run_now=self.stage<2)
        self.context['eval_run_id']=self.eval_id
        return {'status':'completed' if kwargs['execute'] else 'planned', 'eval_run_id':self.eval_id, 'cadence':self.context['score_json']}

    def router(self, **kwargs):
        action=build_portfolio_review_feedback_action_router_decision(context=self.context,
            portfolio_name=kwargs['portfolio_name'],as_of_date=kwargs['as_of_date'])
        if self.concurrent: action['source_cadence_eval_run_id']+=1
        if kwargs['execute']:
            route=action['route_action']; self.calls.append(route)
            if route!='no_op':
                action['child_runner']={'executed':True,'status':'failed' if self.fail_child else 'completed'}
                if not self.stuck: self.stage+=1
        return {'status':'completed','action':action,'eval_run_id':self.eval_id+100}

    def run(self, execute=True):
        return run_portfolio_review_feedback_maintenance(config=None,portfolio_name='Long Term Paper',
            as_of_date=date(2026,9,11),execute=execute,cadence_runner=self.cadence,router_runner=self.router)


class FeedbackMaintenanceTests(unittest.TestCase):
    def test_cadence_failure_does_not_execute_router(self):
        f = MaintenanceFixture()
        result = run_portfolio_review_feedback_maintenance(
            config=None, portfolio_name='Long Term Paper', as_of_date=date(2026, 9, 11),
            execute=True, cadence_runner=lambda **kwargs: {'status': 'failed'}, router_runner=f.router)
        self.assertEqual(result['reason'], 'cadence_not_completed')
        self.assertEqual(f.calls, [])

    def test_guardrail_violation_remains_blocked(self):
        f = MaintenanceFixture()
        def unsafe_cadence(**kwargs):
            report = f.cadence(**kwargs)
            report['cadence']['broker_submit_allowed'] = True
            return report
        result = run_portfolio_review_feedback_maintenance(
            config=None, portfolio_name='Long Term Paper', as_of_date=date(2026, 9, 11),
            execute=True, cadence_runner=unsafe_cadence, router_runner=f.router)
        self.assertEqual(result['status'], 'attention_required')
        self.assertEqual(result['reason'], 'blocked_guardrail_violation')
        self.assertEqual(f.calls, ['no_op'])

    def test_cli_follow_up_flag_dispatches_and_surfaces_attention(self):
        from stockanalysis.operations.cli import main
        target = 'stockanalysis.operations.portfolio_review_feedback_maintenance.run_portfolio_review_feedback_maintenance'
        with patch(target, return_value={'status': 'attention_required', 'reason': 'cadence_changed'}) as runner:
            exit_code = main(['portfolio-review-feedback-action-router-run', '--complete-follow-ups',
                '--as-of-date', '2026-09-11', '--execute'], stdout=io.StringIO())
        self.assertEqual(exit_code, 1)
        self.assertTrue(runner.call_args.kwargs['execute'])
        self.assertEqual(runner.call_args.kwargs['as_of_date'], date(2026, 9, 11))

    def test_feedback_and_calibration_finish_in_same_daily_run_then_no_op(self):
        f=MaintenanceFixture(); result=f.run()
        self.assertEqual(result['status'],'completed')
        self.assertEqual(f.calls,['execute_feedback','execute_calibration','no_op'])
        self.assertEqual(len(result['rounds']),3)
        self.assertEqual(result['reason'],'no_op_calibration_current')
        self.assertFalse(result['automatic_weight_change_allowed'])
        f.calls=[]; self.assertEqual(f.run()['status'],'completed')
        self.assertEqual(f.calls,['no_op'])

    def test_existing_feedback_only_calibrates_and_refreshes_final_cadence(self):
        f=MaintenanceFixture(stage=1); self.assertEqual(f.run()['status'],'completed')
        self.assertEqual(f.calls,['execute_calibration','no_op'])

    def test_repeated_selection_stops_without_repeating_child(self):
        f=MaintenanceFixture(stuck=True); result=f.run()
        self.assertEqual(result['reason'],'repeated_cadence_action')
        self.assertEqual(f.calls,['execute_feedback'])

    def test_concurrent_cadence_replacement_does_not_execute_child(self):
        f=MaintenanceFixture(concurrent=True); self.assertEqual(f.run()['reason'],'cadence_changed')
        self.assertEqual(f.calls,[])

    def test_failed_child_never_starts_follow_up(self):
        f=MaintenanceFixture(fail_child=True); self.assertEqual(f.run()['reason'],'child_not_completed')
        self.assertEqual(f.calls,['execute_feedback'])

    def test_preview_does_not_save_cadence_or_execute_router(self):
        f=MaintenanceFixture(); self.assertEqual(f.run(execute=False)['status'],'planned')
        self.assertEqual(f.cadence_calls,[False]); self.assertEqual(f.calls,[])
