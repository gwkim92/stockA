# Task Contract

## Task

- 이름: recommendation-fundamental-evidence-visibility
- 요청: 추천 상세 API와 화면에서 zero-weight 재무, 피어, 밸류에이션, 재무 안정성, thesis 일관성 component를 별도 기업 분석 근거로 보여준다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/api/recommendations/{id}` live payload가 `fundamental_quality_score`, `valuation_margin_score`, `peer_relative_score`, `balance_sheet_risk_penalty`, `thesis_consistency_score`를 `fundamental_context` provenance로 반환하고, Next.js 추천 상세 화면이 이를 `재무·밸류에이션 근거` 섹션으로 분리 표시한다.

## Scope

- 포함:
  - 추천 상세 live adapter score component provenance 보강
  - frontend `RecommendationDetailData` type 보강
  - 한국어 label/copy 보강
  - 추천 상세 화면의 재무·밸류에이션 근거 섹션 추가
  - live adapter contract test 갱신
- 제외:
  - 추천 total score 재계산
  - component weight 변경
  - 신규 valuation/peer/fundamental 산출 로직 변경
  - broker/live order submit
  - 유료 데이터, 외부 RAG, 외부 graph DB 도입

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/korean-labels.ts`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/recommendation-fundamental-evidence-visibility/*`
- 수정 금지 파일:
  - 추천 total score 산식
  - 기존 component weight
  - broker/order submit path
  - repo 안 secret/env 값

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-fundamental-evidence-visibility`

## Done Criteria

- fundamental component는 `fundamental_context`로 식별된다.
- 추천 상세 화면은 재무·밸류에이션 근거를 점수 일반 목록과 별도 섹션으로 보여준다.
- 화면은 해당 항목이 현재 추천 총점에 미반영된 검증 항목임을 명확히 쓴다.
- 추천 score, weight, broker/order 경계는 변경하지 않는다.
