# cycle-ai-quality-audit-readiness-gap-diagnostics-v1 Handoff

## Status

- completed: local implementation and verification passed.
- blocked for EC2 smoke: `34.206.72.213` SSH and HTTP timed out, `127.0.0.1:13000` has no tunnel, and Chrome AWS console opened to sign-in.

## What Changed

- `cycle-ai-quality-audit-run` now emits `readiness_gaps`.
- Each gap includes `gap_key`, `label`, `metric_key`, `current_value`, and `next_action`.
- `/api/data-health` preserves the sanitized gap list.
- `/data-health` now shows missing execution stages instead of only showing `readiness_gap_count`.

## Readiness Gap Keys

- `rss_documents_missing`: RSS 뉴스 수집 결과 없음.
- `korean_translation_missing`: 한국어 번역 결과 없음.
- `ai_extraction_artifact_missing`: AI 후보 분석 결과 없음.
- `hierarchical_impact_missing`: 상위 흐름 전파 결과 없음.
- `cycle_snapshot_missing`: 사이클 스냅샷 결과 없음.

## Verification

- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cycle_ai_quality_audit`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_data_health_response_includes_sanitized_cycle_ai_quality_audit`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src/stockanalysis/operations/cycle_ai_quality_audit.py`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`

## EC2 Evidence And Blocker

- failed: `ssh -i /Users/woody/Downloads/settle.pem ... ec2-user@34.206.72.213 'echo ok'` timed out.
- failed: `curl -I http://34.206.72.213:3000/` timed out.
- failed: `curl -I http://127.0.0.1:13000/` could not connect because the tunnel is down.
- local AWS CLI profiles `default` and `beatoz-dev` both resolve to account `061051252914`, which does not contain the stockanalysis EC2.
- Chrome AWS console opened to AWS sign-in, so EC2 read-only inspection needs user login.

## Next Step

- exact next step: after AWS login or EC2 network recovery, deploy this change and rerun:
  - `stockanalysis-operations cycle-ai-quality-audit-run --env-file /opt/stockanalysis/runtime/data-operations.env --as-of-date 2026-06-04 --lookback-days 30 --execute --output /opt/stockanalysis/runtime/reports/cycle-ai-quality-audit-latest.json`
- If `readiness_gaps[0].gap_key` is `cycle_snapshot_missing`, run `decision-daily` or `cycle-hierarchy-snapshot-v2-run` for `2026-06-04`, then rerun the audit.
