# Task Contract

## Task

- 이름: frontend-cycle-map-experience
- 요청: 추천 상세 밖에서도 거시 -> 도메인 -> 테마 -> 종목 흐름을 탐색할 수 있는 cycle map 화면을 만든다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/cycle-map`에서 상위 흐름 노드, 사이클 상태, 연결 종목, 최근 뉴스/전파/추천 근거 수, 노드 간 관계를 한국어로 확인할 수 있다.

## Scope

- 포함:
  - `/api/cycle-map` live read DTO 추가
  - `ai.cycle_community_summary`, `signal.cycle_hierarchy_state_snapshot`, `ref.classification_edge` 기반 read-only SQL
  - Next.js `/cycle-map` 페이지 추가
  - 홈/뉴스AI/사이클 화면에서 cycle map 링크 추가
  - focused backend/frontend tests
- 제외:
  - DB schema 변경
  - 신규 AI 호출
  - 추천 점수 산식 변경
  - broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `src/stockanalysis/frontend/pagination.py`
  - `apps/web/src/app/cycle-map/page.tsx`
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/intelligence/page.tsx`
  - `apps/web/src/app/cycles/page.tsx`
  - `apps/web/src/lib/frontend-api.ts`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/korean-labels.ts`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/frontend-cycle-map-experience/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations
  - recommendation scoring formulas
  - live broker/order submission

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task frontend-cycle-map-experience`
  - EC2 deploy 후 `GET http://127.0.0.1:13000/cycle-map` route smoke

## Done Criteria

- [x] `/api/cycle-map` is supported by the live adapter.
- [x] `/cycle-map` renders cycle nodes and edges in Korean.
- [x] Existing home/intelligence/cycles routes link to the map.
- [x] Focused local verification passes.
- [x] EC2 route smoke passes.

## Follow-up Hardening

- 2026-05-23: 화면 대표 종목은 `ai.cycle_community_summary.summary_json.top_symbols`를 신뢰하지 않고 canonical DB(`ref.instrument_factor_exposure`, `signal.propagated_instrument_impact`)에서 다시 계산한다. 이유: AI 요약 artifact가 오염되면 `AI_SEMICONDUCTOR_CYCLE -> XOM` 같은 잘못된 화면 링크가 생길 수 있다.
- 2026-05-23: 뉴스 AI validator는 직접 종목 영향이 RSS 원문 제목/요약에 티커 또는 회사명으로 근거가 있을 때만 통과시키도록 강화한다.
