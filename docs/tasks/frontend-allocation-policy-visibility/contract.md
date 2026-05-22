# Task Contract

## Task

- 이름: frontend-allocation-policy-visibility
- 요청: `/remediation`에서 현재 어떤 포트폴리오 비중 정책 때문에 티켓이 생성되는지 직접 볼 수 있게 한다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/api/remediation-tickets` 응답에 active allocation policy가 포함된다.
  - `/remediation` 화면이 단일 종목 상한과 리밸런싱 목표 해석 기준을 한국어로 표시한다.
  - 사용자는 MSFT/TSLA가 왜 비중 검토 티켓으로 보이는지 화면만 보고 이해할 수 있다.

## Scope

- 포함:
  - FastAPI live adapter remediation response에 allocation policy payload 추가
  - Next.js `RemediationTicketsData` 타입 확장
  - `/remediation` policy 카드 추가
  - live adapter unit test와 Next typecheck/build
- 제외:
  - 정책 편집 write API
  - DB schema 변경
  - 추천 점수 산식 변경
  - broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/korean-labels.ts`
  - `apps/web/src/app/remediation/page.tsx`
  - `docs/api/frontend/examples/remediation-tickets.json`
  - `docs/tasks/frontend-allocation-policy-visibility/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations/schema
  - broker/live order submission

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task frontend-allocation-policy-visibility`

## Done Criteria

- [ ] API response includes `allocation_policy`.
- [ ] UI shows policy name/source, max single-position weight, min rebalance target weight.
- [ ] Existing remediation ticket contract remains backward-compatible for ticket rows.
- [ ] EC2 `/remediation` renders the policy card.
