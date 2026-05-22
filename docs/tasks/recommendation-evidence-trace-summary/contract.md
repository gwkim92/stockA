# Task Contract

## Task

- 이름: recommendation-evidence-trace-summary
- 요청: 추천 상세에서 뉴스/AI 분석, 상위 흐름 전파, 보유검토가 어떻게 이어지는지 사람이 한눈에 이해할 수 있게 한다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/api/recommendations/{id}` read-only DTO가 `evidence_trace`를 제공한다.
  - `evidence_trace`는 직접 뉴스/AI 근거, 상위 흐름 전파, 보유검토 연결 상태를 분리해서 제공한다.
  - `/recommendations/[recommendationId]` 화면은 `뉴스/AI -> 상위 흐름 -> 보유검토` 경로를 한국어로 설명한다.
  - 추천 점수 산식, DB schema, scheduler, broker/order flow는 바뀌지 않는다.

## Scope

- 포함:
  - recommendation detail live adapter SQL/response contract 보강
  - recommendation detail Next.js 화면 표시 개선
  - focused backend contract test
  - task handoff와 검증 기록
- 제외:
  - DB migration
  - recommendation scoring 변경
  - scheduler cadence/activation 변경
  - paper/real order 생성
  - broker/order submission code

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `docs/tasks/recommendation-evidence-trace-summary/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations/schema
  - scheduler units/timers
  - recommendation scoring weights
  - broker/order submission code

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
  - `PYTHONPATH=src /private/tmp/stockanalysis-test-venv/bin/python -m unittest discover -s tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-evidence-trace-summary`
  - EC2 API/browser smoke for `/api/recommendations/{id}` and `/recommendations/{id}`

## Done Criteria

- [ ] API response includes normalized `evidence_trace`.
- [ ] Recommendation detail page shows a Korean evidence flow summary.
- [ ] Local verification and AWH pass.
- [ ] EC2 deploy and smoke pass.

