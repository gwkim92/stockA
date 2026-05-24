# Session Handoff

## Current Status

- 완료:
  - task contract를 만들었다.
  - 기존 deterministic graph context summary 구조를 확인했다.
  - `cycle_community_ai_v2` summary type migration을 추가했다.
  - `stockanalysis.ai.cycle_community_ai_summary`에 fixture/Codex OAuth provider, prompt/schema, invocation 기록, summary upsert runner를 추가했다.
  - `stockanalysis-operations cycle-community-ai-summary-v2-run` CLI를 추가했다.
  - decision profile에서 deterministic `cycle-graph-context-summary` 다음에 AI summary step이 실행되도록 연결했다.
  - `/cycle-map` read SQL은 같은 날짜의 `cycle_community_ai_v2`를 우선 사용하고 없으면 기존 `cycle_graph_context_v1`로 fallback한다.
  - EC2에 배포했고 migration 0020을 적용했다.
  - EC2 fixture smoke는 성공했다: `run_id=691`, `invocation_id=945`, `inserted_summary_count=1`.
  - EC2 Codex OAuth smoke는 provider 인증에서 실패했고 fallback이 정상 동작했다: `run_id=692`, `status=completed_with_fallback`, 원인 `401 token_invalidated`.
  - EC2 DB 확인: `cycle_community_ai_v2` summary row 2개, 최신 `cycle_community_ai_summary` run id 692.

## Verification

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cycle_community_ai_summary tests.test_data_operations_cli tests.test_operating_data_orchestrator tests.test_cycle_graph_context tests.test_data_operations_cadence tests.test_frontend_live_adapter`: passed, 133 tests.
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`: passed.
- `git diff --check`: passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task cycle-community-ai-summary-v2`: passed.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`: passed, 826 tests.
- EC2 `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_cycle_community_ai_summary tests.test_data_operations_cli tests.test_operating_data_orchestrator tests.test_cycle_graph_context tests.test_data_operations_cadence tests.test_frontend_live_adapter`: passed, 133 tests.
- EC2 `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m compileall -q src tests`: passed.
- EC2 migration: `db/migrations/0020_cycle_community_ai_summary_v2.sql` applied.
- EC2 fixture execute: `cycle-community-ai-summary-v2-run --provider fixture --node-code MACRO_RATES_FED --execute`: passed.
- EC2 Codex OAuth execute: `cycle-community-ai-summary-v2-run --provider codex_oauth --node-code TECH_DOMAIN --execute`: completed with fixture fallback because Codex auth token is invalidated.
- EC2 route smoke: `http://127.0.0.1:13000/cycle-map` and `/data-health` returned HTML after service restart.

## Exact Next Step

- exact next step: EC2 Codex OAuth 재로그인을 처리하거나, 그 전제 없이 `recommendation-quality-calibration`을 진행한다. 추천 weight는 아직 변경하지 않는다.
