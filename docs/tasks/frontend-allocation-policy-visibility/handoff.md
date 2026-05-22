# Session Handoff

## Current Status

- 상태: local_verified
- 기준일: 2026-05-22
- 완료:
  - 작업 범위와 mutable surface를 `contract.md`에 고정했다.
  - `/api/remediation-tickets` live 응답에 active allocation policy payload를 추가했다.
  - `/remediation` 화면에 단일 종목 상한, 리밸런싱 목표 해석 기준, 정책 범위를 표시했다.
  - fixture contract example에도 `allocation_policy`를 추가해 local fixture 모드와 live 모드가 같은 필드를 갖게 했다.
  - 정책 코드명이 화면에 그대로 노출되지 않도록 한국어 라벨을 추가했다.
- 막힌 점:
  - 없음.

## Implemented

- `src/stockanalysis/frontend/live_adapter.py`
  - `render_frontend_remediation_allocation_policy_sql()` 추가.
  - active policy가 없으면 read-only fallback guardrail을 DTO로 반환한다.
  - ticket row contract는 유지하고 `data.allocation_policy`만 추가했다.
- `apps/web/src/app/remediation/page.tsx`
  - 상단 요약 rail의 4번째 항목을 “비중 정책”으로 바꿨다.
  - 우측 ledger에 “현재 적용 기준” 카드를 추가했다.
- `apps/web/src/lib/types.ts`, `docs/api/frontend/examples/remediation-tickets.json`
  - frontend DTO와 fixture example에 allocation policy를 반영했다.

## Verification

- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter tests.test_frontend_api_adapter tests.test_frontend_fixture_server`
- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- PASS: `git diff --check`

## Remaining

- Run AWH verification.
- Commit and push.
- Deploy to EC2, restart FastAPI and Next service, then verify `/remediation`.

## Exact Next Step

- exact next step: run AWH verification for `frontend-allocation-policy-visibility`.
