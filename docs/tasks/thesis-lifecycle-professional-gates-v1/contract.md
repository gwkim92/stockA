# Task Contract

## Task

- 이름: thesis-lifecycle-professional-gates-v1
- 요청: thesis 상세에서 catalyst, invalidation, risk, valuation context, review cadence, evidence freshness를 전문 투자 검토 gate로 강제 표시한다.
- 담당: Codex
- 날짜: 2026-05-26

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/api/theses/{id}`와 `/theses/{id}`가 thesis를 단순 설명이 아니라 `왜 보유하는가`, `무엇이 맞아야 하는가`, `무엇이 틀리면 나가는가`, `밸류에이션 맥락이 있는가`, `언제 재검토해야 하는가`, `최근 근거가 검토에 반영됐는가`를 gate별 통과/주의/차단으로 제공한다.

## Scope

- 포함:
  - thesis detail DTO에 `professional_lifecycle_gates` 추가
  - thesis evidence에 `observed_at` 추가
  - gate 구성: buy case, catalysts, risks, invalidation, valuation, review cadence, evidence freshness, order boundary
  - 각 gate별 `status`, `decision`, `detail`, `next_step`, `facts`, read-only order boundary 노출
  - `/theses/[thesisId]` 화면 상단에 전문 thesis gate 요약 추가
  - unit/adapter/frontend type/build 검증
- 제외:
  - thesis write/edit API
  - recommendation score/weight 변경
  - valuation 계산식 변경
  - broker submit, live order, kill switch unlock
  - 새 DB schema
  - repo 안 secret/env 값

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/korean-labels.ts`
  - `apps/web/src/app/theses/[thesisId]/page.tsx`
  - `docs/tasks/thesis-lifecycle-professional-gates-v1/*`
  - `docs/plans/2026-05-26-thesis-lifecycle-professional-gates-v1.md`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
- 수정 금지 파일:
  - 추천 scoring formula/weights
  - broker/order submit path
  - benchmark/evaluation split
  - repo 안 secret/env 값

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_thesis_detail_response_matches_frontend_contract_shape`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task thesis-lifecycle-professional-gates-v1`
  - `git diff --check`

## Done Criteria

- API는 `professional_lifecycle_gates`와 evidence `observed_at`을 반환한다.
- Gate는 thesis lifecycle 필수요소와 evidence freshness를 통과/주의/차단으로 판정한다.
- 모든 gate는 `automatic_order_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`를 유지한다.
- 화면은 사용자가 현재 thesis에서 무엇을 봐야 하고 무엇이 부족한지 한국어로 이해할 수 있게 표시한다.
- 추천 weights, broker submit, automatic order flags는 변경되지 않는다.
- EC2 API/route smoke에서 gate section과 read-only boundary가 확인된다.
