# Session Handoff

## Current Status

- 상태: ec2_verified
- 기준일: 2026-05-22
- 완료:
  - 작업 범위와 mutable surface를 `contract.md`에 고정했다.
  - `/api/remediation-tickets` live 응답에 active allocation policy payload를 추가했다.
  - `/remediation` 화면에 단일 종목 상한, 리밸런싱 목표 해석 기준, 정책 범위를 표시했다.
  - fixture contract example에도 `allocation_policy`를 추가해 local fixture 모드와 live 모드가 같은 필드를 갖게 했다.
  - 정책 코드명이 화면에 그대로 노출되지 않도록 한국어 라벨을 추가했다.
  - GitHub와 EC2에 배포했고 FastAPI/Next 서비스를 재시작했다.
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
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task frontend-allocation-policy-visibility`
- PASS: EC2 `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- PASS: EC2 `stockanalysis-frontend-api.service` and `stockanalysis-web.service` are `active`.
- PASS: EC2 `/__health` returns `status=ok`, `source_mode=live`, `auth_mode=read-token`, `connection_boundary=psycopg_pool`.
- PASS: EC2 authorized `/api/remediation-tickets?status=open` returns `ticket_count=2`, symbols `MSFT`, `TSLA`, policy `global_default_long_term_guardrail`, max single-position weight `0.25`, min rebalance target weight `0.1`.
- PASS: Chrome `http://127.0.0.1:13000/remediation` renders “비중 정책”, “현재 적용 기준”, “25.0%”, “MSFT”, “TSLA”.

## Remaining

- None for this task.
- Next work should continue with broader page-by-page UX/data-quality remediation or the next project roadmap task.

## Exact Next Step

- exact next step: continue the next project task from `docs/project-execution-roadmap.md` or run a focused page-by-page UI/data audit.
