# Task Contract

## Task

- 이름: frontend-recommendation-cycle-waterfall
- 요청: 계층형 사이클·뉴스·AI 고도화 작업의 다음 단계로, 추천 상세 화면에서 새 추천 점수 component가 사용자에게 이해 가능한 경로로 보이게 한다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 추천 상세 화면에서 새 계층형 사이클 점수 항목이 일반 점수 목록에 묻히지 않고, 사용자가 `거시 -> 도메인 -> 테마 -> 종목 -> 충돌` 순서로 왜 이 종목이 추천 검토 대상이 되었는지 읽을 수 있다.

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/korean-labels.ts`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/frontend-recommendation-cycle-waterfall/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB schema/migrations
  - recommendation scoring formulas
  - broker/live order submission

## Scope

- 포함:
  - FastAPI live adapter의 recommendation detail DTO에 계층형 사이클 provenance 추가
  - Next.js 추천 상세 화면에 계층형 사이클 waterfall 섹션 추가
  - 새 score component 이름 한국어 라벨 추가
  - focused frontend/live adapter test 갱신
- 제외:
  - 추천 산식 변경
  - DB schema 변경
  - 배치 runner 변경
  - 실거래/broker/order flow

## Acceptance

- `macro_regime_score`, `domain_cycle_score`, `theme_cycle_score`, `instrument_cycle_score`, `cycle_conflict_penalty`가 `cycle_stack_context` provenance로 노출된다.
- 화면에서 선택된 사이클 노드와 weight가 보인다.
- weight 0 항목은 “현재 총점 영향 없음”으로 표시되어 사용자가 설명용 항목임을 알 수 있다.
- 기존 macro flow, 가격/순위, AI/event evidence 표시가 깨지지 않는다.

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task frontend-recommendation-cycle-waterfall`

## Done Criteria

- [ ] Recommendation detail DTO exposes cycle stack provenance.
- [ ] Recommendation detail page shows cycle stack waterfall.
- [ ] Focused backend/frontend verification passes.
- [ ] EC2 live route smoke confirms the new section renders with production data.
