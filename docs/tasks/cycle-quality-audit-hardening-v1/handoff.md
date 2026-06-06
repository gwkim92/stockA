# cycle-quality-audit-hardening-v1 Handoff

## Status

- status: completed_ec2_smoked
- current status: audit hardening deployed to EC2; stale direct ticker cleanup executed; cycle snapshot ignores weak hierarchical propagation in event heat; weak propagation is classified as managed warning rather than an open contamination gate.
- completed: EC2 live audit found 6 ungrounded direct ticker impacts and removed them with the existing explicit cleanup runner.
- updated_at: 2026-06-06
- branch: `develop`

## Completed

- `cycle-ai-quality-audit-run` now audits three additional quality risks:
  - `cross_theme_mismatch_count`: strong news/theme incompatibility, such as energy news on quantum cycle or rate/Fed news on energy geopolitics.
  - `duplicate_flow_evidence_count`: the same title split across multiple events and multiple cycle nodes.
  - `weak_propagation_evidence_count`: hierarchical propagation rows with missing source document linkage, low confidence, low impact strength, or weak path weight.
- Audit samples now include `cross_theme_mismatches`, `duplicate_flow_evidence`, and `weak_propagation_evidence`.
- Report `next_actions` now points to the specific remediation path before recommendation input.
- `/data-health` renders the new counters and sample groups in Korean.
- `cycle_hierarchy_snapshot_v2` now excludes weak hierarchical propagation rows from event heat inputs using confidence, impact strength, and path weight thresholds.
- `cycle-ai-quality-audit-run` now reports weak propagation as `managed_warning` when it is the only remaining issue, so severe contamination gates can close while the weak evidence count stays visible.
- EC2 cleanup runner removed 6 stale direct instrument impacts without changing recommendation scoring or order boundary.

## Explicit Non-Changes

- Recommendation score weights unchanged.
- Broker/order boundary unchanged: `read_only_no_order`.
- Portfolio position and benchmark unchanged.
- No data deletion added. Existing cleanup runners remain the only explicit cleanup path.
- The existing explicit stale direct impact cleanup runner was executed on EC2 after previewing the 6 candidates.
- No external paid RAG/vector/graph provider added.

## Local Verification

- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cycle_ai_quality_audit`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `git diff --check`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task cycle-quality-audit-hardening-v1`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cycle_hierarchy_snapshot_v2 tests.test_cycle_ai_quality_audit`
- passed: `cd apps/web && npm run build`

## EC2 Evidence

- exact next step: continue with the separate `professional_source_gap_attention` remediation path; cycle AI quality audit hardening itself is complete.
- deployed final commit: `b8565f1d`.
- EC2 service status after restart: `stockanalysis-frontend-api.service=active`, `stockanalysis-web.service=active`.
- `cycle-ai-stale-direct-impact-cleanup-run --dry-run`: `candidate_count=6`, `removed_count=0`.
- `cycle-ai-stale-direct-impact-cleanup-run --execute`: `run_id=3703`, `candidate_count=6`, `removed_count=6`, `recommendation_scoring_mutated=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`.
- `cycle-hierarchy-snapshot-v2-run --execute`: `run_id=3707`, `node_count=18`, `transition_count=1`.
- latest final audit: `run_id=3709`, `audit_status=managed_warning`, `audit_score=95`, `issue_count=0`, `readiness_gap_count=0`.
- final checks: `duplicate_title_count=0`, `ungrounded_direct_ticker_count=0`, `macro_false_ticker_count=0`, `quantum_energy_mislink_count=0`, `cross_theme_mismatch_count=0`, `duplicate_flow_evidence_count=0`, `weak_propagation_evidence_count=1244`, `normal_macro_flow_count=495`.
- `/api/data-health`: `cycle_ai_quality_audit.status=managed_warning`, `audit_score=95`, `issue_count=0`, `readiness_gap_count=0`.
- `/data-health` route smoke rendered `약한 전파 근거 관리 중`, `약한 전파 근거`, `교차 테마 불일치`, `중복 흐름 근거`.
- unrelated remaining open gate: `professional_source_gap_attention` for EROK/QQQ/AAPL source gaps. It is outside this cycle audit task.

## Risks

- Cross-theme mismatch rules are intentionally conservative. They catch strong incompatibilities, not every possible bad taxonomy assignment.
- Weak propagation evidence is a warning signal. It should not delete rows by itself because some low-confidence propagation can still be useful as watch evidence.
- Existing weak hierarchical propagation rows remain in the table for traceability. The cycle snapshot filter prevents them from driving event heat after the final filter deployment.
