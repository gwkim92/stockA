# Task Contract

## Task

- 이름: macro-event-propagation
- 요청: 상위 흐름 뉴스가 개별 종목에 전파되는 DB/runner/recommendation/frontend 흐름을 구현한다.
- 담당: Codex
- 날짜: 2026-05-21

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 거시/테마 뉴스는 직접 종목 뉴스가 아니어도 `event_classification_impact`에서 시작해 `instrument_factor_exposure`를 거쳐 `propagated_instrument_impact`로 종목 영향 후보가 생성되고, recommendation/frontend에서 직접 뉴스와 상위 흐름 전파를 구분해 볼 수 있다.

## Scope

- 포함:
  - `ref.instrument_factor_exposure`, `signal.propagated_instrument_impact` migration/index
  - 최소 exposure seed
  - `macro-event-propagation-run` operations CLI
  - recommendation `macro_flow_score` component 추가
  - `/intelligence`, `/stocks/[symbol]`, `/recommendations/[recommendationId]` 상위 흐름 trace 표시
  - EC2 smoke
- 제외:
  - 유료 데이터 공급자
  - 외부 graph/vector DB
  - 실거래/broker/order flow
  - AI가 추천/주문을 직접 결정하는 변경

## Mutable Surface

- 수정 가능한 파일:
  - `db/migrations/`
  - `db/seeds/`
  - `src/stockanalysis/operations/`
  - `src/stockanalysis/signal/`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/app/intelligence/page.tsx`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - 관련 tests
  - `docs/tasks/macro-event-propagation/`
- 수정 금지 파일:
  - `.env` secret values
  - broker/live order submission
  - benchmark/evaluation split

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src python3 -m unittest tests.test_macro_event_propagation tests.test_recommendation_bootstrap tests.test_cycle_state_snapshot tests.test_frontend_live_adapter tests.test_data_operations_cli`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/test-venv/bin/python -m unittest discover -s tests`
  - `cd apps/web && npm run typecheck && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task macro-event-propagation`
  - EC2 deploy 후 `macro-event-propagation-run --execute` 1회와 API/page smoke

## Done Criteria

- [ ] Macro/theme-only event can produce propagated instrument impacts without direct event instrument impact.
- [ ] Propagation is idempotent by `(event_id, node_id, instrument_id)`.
- [ ] Recommendation component rows include `macro_flow_score`.
- [ ] Frontend exposes `뉴스 → 상위 흐름 → 종목` trace.
- [ ] EC2 smoke confirms propagated rows and no duplicated news clusters.
