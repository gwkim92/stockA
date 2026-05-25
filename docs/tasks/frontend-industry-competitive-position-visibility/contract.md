# Task Contract

## Task

- 이름: frontend-industry-competitive-position-visibility
- 요청: 계산된 산업 경쟁 포지션을 종목 상세와 추천 상세에서 투자자가 이해할 수 있게 노출한다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: FastAPI live adapter가 `research.industry_competitive_position` 최신 값을 읽어 `StockDetailData`와 `RecommendationDetailData`에 포함하고, Next.js 종목/추천 상세 화면이 경쟁 위치, 피어 그룹, 강점, 리스크, 추정 점수를 한국어로 표시한다.

## Scope

- 포함:
  - stock detail/recommendation detail live SQL payload 확장
  - DTO 타입 확장
  - 종목 상세와 추천 상세의 피어·경쟁 위치 섹션 개선
  - frontend live adapter contract tests 갱신
  - task handoff 갱신
- 제외:
  - 신규 DB schema
  - industry competitive positioning 산식 변경
  - recommendation score/weight 변경
  - benchmark/evaluation split 변경
  - broker/order submit
  - 실시간 AI 호출

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/frontend-industry-competitive-position-visibility/*`
- 수정 금지 파일:
  - `.env` secret values
  - recommendation scoring weights
  - broker/order submit path
  - DB migrations

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task frontend-industry-competitive-position-visibility`

## Done Criteria

- [x] stock detail API payload에 `industry_competitive_position`이 포함된다.
- [x] recommendation detail API payload에 `industry_competitive_position`이 포함된다.
- [x] 종목 상세에서 경쟁 위치와 주요 강점/리스크가 보인다.
- [x] 추천 상세에서 피어 비교 점수 항목과 산업 경쟁 포지션이 함께 읽힌다.
- [x] 화면 문구는 사용자용 한국어이며 내부 runner/SQL 용어만 노출하지 않는다.
- [x] 추천 score/weight, schema, broker/order flow는 변경되지 않는다.
