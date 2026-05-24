# Task Contract

## Task

- 이름: cycle-community-ai-summary-v2
- 요청: 기존 deterministic cycle graph context summary 위에 Codex OAuth batch AI summary를 추가한다.
- 담당: Codex
- 날짜: 2026-05-24

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations cycle-community-ai-summary-v2-run`이 Postgres graph context를 읽고, fixture 또는 Codex OAuth provider로 한국어 community summary를 생성해 `ai.model_invocation`과 `ai.cycle_community_summary(summary_type='cycle_community_ai_v2')`에 저장할 수 있다.

## Scope

- 포함:
  - `cycle_community_ai_v2` summary type migration
  - Postgres graph context 기반 prompt/schema
  - fixture provider와 Codex OAuth batch provider boundary
  - `ai.model_invocation` 기록
  - `ai.cycle_community_summary` upsert
  - CLI와 unit/CLI/orchestrator tests
  - decision profile에 batch step 추가
- 제외:
  - FastAPI request-time AI 호출
  - 외부 RAG/vector/graph service
  - 추천 weight 변경
  - 실거래 broker submit
  - frontend redesign

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ai/cycle_community_ai_summary.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `src/stockanalysis/operations/cadence.py`
  - `db/migrations/0020_cycle_community_ai_summary_v2.sql`
  - `tests/test_cycle_community_ai_summary.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_operating_data_orchestrator.py`
  - `docs/tasks/cycle-community-ai-summary-v2/*`
- 수정 금지 파일:
  - `.env` secret values
  - recommendation scoring weights
  - broker/order submit path

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cycle_community_ai_summary tests.test_data_operations_cli tests.test_operating_data_orchestrator tests.test_cycle_graph_context`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task cycle-community-ai-summary-v2`

## Done Criteria

- Codex OAuth prompt는 고정 지시/schema를 앞에 두고 node별 context를 뒤에 둔다.
- 출력 schema는 `korean_summary`, `key_drivers`, `causal_paths`, `supporting_events`, `conflicts`, `uncertainty`, `watchlist_symbols`를 포함한다.
- dry-run은 DB write 없이 preview를 반환한다.
- execute는 pipeline run, model invocation, AI summary upsert를 남긴다.
- decision profile에서 deterministic graph summary 다음에 AI summary step이 실행된다.
