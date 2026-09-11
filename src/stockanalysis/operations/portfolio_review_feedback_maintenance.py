"""Complete deterministic feedback and calibration in one bounded daily pass."""
from datetime import date
from typing import Any, Callable

from stockanalysis.operations.portfolio_review_feedback_cadence import run_portfolio_review_feedback_cadence
from stockanalysis.operations.portfolio_review_feedback_action_router import (
    build_portfolio_review_feedback_action_router_decision,
    run_portfolio_review_feedback_action_router,
)


def run_portfolio_review_feedback_maintenance(*, config: Any, portfolio_name: str, as_of_date: date,
        execute: bool = False, executor: Any = None,
        cadence_runner: Callable = run_portfolio_review_feedback_cadence,
        router_runner: Callable = run_portfolio_review_feedback_action_router) -> dict[str, Any]:
    common = dict(config=config, portfolio_name=portfolio_name, as_of_date=as_of_date, executor=executor)
    result = {'report_name': 'portfolio_review_feedback_maintenance', 'execute': execute,
              'as_of_date': as_of_date.isoformat(), 'portfolio_name': portfolio_name,
              'status': 'planned' if not execute else 'running', 'rounds': [],
              'maximum_child_actions': 2, 'automatic_weight_change_allowed': False,
              'broker_submit_allowed': False, 'order_boundary': 'read_only_no_order'}
    seen = set()
    # At most feedback, calibration, then one fresh no-op observation. Repeating
    # a stale selection never triggers another child execution within this pass.
    for _ in range(3 if execute else 1):
        cadence = cadence_runner(**common, execute=execute)
        if execute and (cadence.get('status') != 'completed' or type(cadence.get('eval_run_id')) is not int):
            return {**result, 'status': 'attention_required', 'reason': 'cadence_not_completed'}
        action = build_portfolio_review_feedback_action_router_decision(
            context={'status': 'loaded', 'eval_run_id': cadence.get('eval_run_id'),
                     'score_json': cadence['cadence']},
            portfolio_name=portfolio_name, as_of_date=as_of_date)
        route = action['route_action']
        observation = {'cadence_eval_run_id': cadence.get('eval_run_id'), 'action': action}
        result['rounds'].append(observation)
        if not execute:
            return result
        if route in seen:
            return {**result, 'status': 'attention_required', 'reason': 'repeated_cadence_action'}
        if route != 'no_op' and len(seen) >= 2:
            return {**result, 'status': 'attention_required', 'reason': 'follow_up_limit'}
        # Refuse a concurrent replacement of our freshly saved selection.
        planned = router_runner(**common, execute=False)['action']
        if (planned['source_cadence_eval_run_id'] != cadence.get('eval_run_id')
                or planned['route_action'] != route):
            return {**result, 'status': 'attention_required', 'reason': 'cadence_changed'}
        routed = router_runner(**common, execute=True)
        observation['router_eval_run_id'] = routed.get('eval_run_id')
        observation['action'] = routed['action']
        if (routed['status'] != 'completed' or routed['action']['route_action'] != route
                or routed['action']['source_cadence_eval_run_id'] != cadence.get('eval_run_id')):
            return {**result, 'status': 'attention_required', 'reason': 'router_result_changed'}
        if route == 'no_op':
            blocked = str(routed['action']['action_status']).startswith('blocked_')
            return {**result, 'status': 'attention_required' if blocked else 'completed',
                    'reason': routed['action']['action_status']}
        child = routed['action']['child_runner']
        if not child.get('executed') or child.get('status') != 'completed':
            return {**result, 'status': 'attention_required', 'reason': 'child_not_completed'}
        seen.add(route)
    return {**result, 'status': 'attention_required', 'reason': 'follow_up_limit'}
