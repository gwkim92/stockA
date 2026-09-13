"""Read-only before/after snapshots; no collector or AI invocation is requested."""
import json
import os
from pathlib import Path
import runpy
import sys
from datetime import datetime, timezone

APP=Path('/opt/stockanalysis/app')
BASE=Path('/opt/stockanalysis/runtime/operations-state-clarity-20260913')


def main():
    mode=sys.argv[1]
    assert mode in ('before','after')
    BASE.mkdir(exist_ok=True,mode=0o700)
    helper=runpy.run_path(str(APP/'docs/tasks/research-source-refresh-20260911/verify_server.py'))
    os.environ.update(helper['load_env_file_values'](str(BASE.parent/'data-operations.env')))
    db=helper['PsqlCommandExecutor'].from_config(helper['RuntimeConfig'].from_env())
    health=helper['api']('/api/data-health')
    feedback=health['portfolio_review_decision_feedback']
    calibration=health['portfolio_review_feedback_calibration']
    jobs=[row for row in health['pipeline_runs'] if row['job_id'] in ('toss-live-account-readonly','toss-priority-microdata-intraday')]
    protected=db.execute_scalar("select md5(coalesce(string_agg(md5(to_jsonb(e)::text),',' order by eval_run_id),'')) from ai.eval_run e where eval_name in ('portfolio_review_decision_history','portfolio_review_decision_outcome_feedback','portfolio_review_feedback_calibration');")
    snapshot=dict(at=datetime.now(timezone.utc).isoformat(),jobs=jobs,job_count=len(health['pipeline_runs']),
        feedback={k:feedback[k] for k in ('eval_run_id','feedback_status','decision_count','validated_count','contradicted_count','needs_more_data_count')},
        unresolved=[row for row in feedback['latest_items'] if row['feedback_status']=='needs_more_data'],
        calibration={k:calibration[k] for k in ('eval_run_id','calibration_status','mature_decision_count','decision_count','feedback_run_count','weight_review_blocked','weight_review_block_reason')},
        protected_evaluation_hash=protected,
        batch_runtime=health['scheduler']['profile_scheduler']['batch_runtime'],
        artifact_runner=health['data_operations_artifact_runner'])
    if mode=='after':
        before=json.loads((BASE/'before.json').read_text())
        assert snapshot['protected_evaluation_hash']==before['protected_evaluation_hash']
        assert snapshot['feedback']==before['feedback']
        assert snapshot['job_count']==before['job_count']
        assert all(row['health_status']=='scheduled_wait' for row in jobs)
        assert next(row for row in jobs if row['job_id']=='toss-priority-microdata-intraday')['latest_run_id']=='pipeline-run-23999'
        assert any(row['symbol']=='AMZN' and row['feedback_display_label']=='판단 보류' for row in snapshot['unresolved'])
        assert calibration['weight_review_blocked'] is True
        assert '반복 관찰' in calibration['weight_review_block_reason']
        assert snapshot['batch_runtime']['attention_profile_count']==0
        assert snapshot['batch_runtime']['monitored_profile_count']==13
        assert snapshot['artifact_runner']['active_timer_count']==13
        assert snapshot['artifact_runner']['attention_required'] is False
        assert all(not row['automatic_order_allowed'] and not row['broker_submit_allowed'] and row['order_boundary']=='read_only_no_order' for row in feedback['latest_items'])
    (BASE/(mode+'.json')).write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in snapshot.items() if k not in ('unresolved','protected_evaluation_hash')},ensure_ascii=False))

if __name__=='__main__': main()
