# Task Contract

## Task

- 이름: recommendation-professional-decision-waterfall-v1
- 요청: 추천 상세에서 거시/사이클/뉴스, 기업 분석, 재무 품질, 밸류에이션, 포지션 크기, thesis, 페이퍼 검증을 하나의 전문 의사결정 흐름으로 연결한다.
- 담당: Codex
- 날짜: 2026-05-26

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/api/recommendations/{id}`와 `/recommendations/{id}`가 추천을 단순 점수 카드가 아니라 `거시·사이클 → 뉴스·AI → 사업·경쟁 → 재무 품질 → 밸류에이션 → 투자 논리 → 포지션 크기 → 페이퍼 검증` 순서로 읽을 수 있는 read-only 투자 검토서로 제공한다.

## Scope

- 포함:
  - 추천 상세 DTO에 `professional_decision_waterfall` 추가
  - 기존 score component, equity research, industry competitive position, evidence trace, evidence review, outcome, holding review를 조합
  - 각 단계별 `status`, `tone`, `decision`, `detail`, `evidence_count`, `facts`, 링크를 한국어로 노출
  - 포지션 크기 단계는 실제 주문 수량이 아니라 현재 보유 비중, 권고 비중, 비중 차이, 보유 검토 상태만 보여준다
  - 모든 단계에서 `automatic_order_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order` 유지
  - 추천 상세 화면은 backend waterfall를 우선 사용해 같은 판단 순서를 렌더링
  - unit/type/build/AWH/EC2 route smoke 검증
- 제외:
  - 추천 score formula/weight 변경
  - target weight, order quantity, rebalance order 산출
  - broker submit, live order, kill switch unlock
  - 새 DB schema
  - benchmark/evaluation split 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/korean-labels.ts`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `docs/tasks/recommendation-professional-decision-waterfall-v1/*`
  - `docs/plans/2026-05-26-recommendation-professional-decision-waterfall-v1.md`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
- 수정 금지 파일:
  - 추천 scoring formula/weights
  - broker/order submit path
  - repo 안 secret/env 값
  - benchmark/evaluation split

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_recommendation_detail_response_matches_frontend_contract_shape`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-professional-decision-waterfall-v1`
  - `git diff --check`

## Done Criteria

- 추천 상세 API가 `professional_decision_waterfall`를 반환한다.
- waterfall는 거시/사이클, 뉴스/AI, 사업/경쟁, 재무, 밸류에이션, thesis, 포지션 크기, 페이퍼 검증을 포함한다.
- 화면은 API waterfall 순서를 사용해 투자자가 “왜 이 추천을 검토하는지”를 한 번에 읽을 수 있게 한다.
- 주문 관련 필드는 모두 read-only 차단 상태다.
- 추천 weights, broker submit, automatic order flags는 변경되지 않는다.
- EC2 API/route smoke에서 waterfall와 화면 섹션이 확인된다.
