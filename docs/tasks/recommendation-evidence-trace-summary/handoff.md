# Session Handoff

## Current Status

- 상태: local_verified_in_progress
- 기준일: 2026-05-22
- 완료:
  - task contract를 생성했다.
  - recommendation detail DTO에 `evidence_trace`를 추가했다.
  - `evidence_trace`는 직접 뉴스/AI, 상위 흐름 전파, 보유검토 상태를 분리한다.
  - `/recommendations/[recommendationId]`에 “근거 흐름 요약” 패널을 추가했다.
  - focused backend contract test, full unittest, Next typecheck/build를 통과했다.
- 막힌 점:
  - 없음.

## Planned Fix

- recommendation detail SQL에서 기존 canonical table만 읽어 direct event/AI anchor, propagated macro-flow count, latest portfolio review item을 요약한다.
- response builder에서 raw DB id를 opaque frontend id로 정규화한다.
- 화면에서는 원천 ID보다 “무엇을 보고 검토해야 하는가”를 먼저 보여준다.

## Verification Log

- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v`
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
- PASS: `PYTHONPATH=src /private/tmp/stockanalysis-test-venv/bin/python -m unittest discover -s tests` ran 739 tests.
- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `git diff --check`
- PENDING: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-evidence-trace-summary`
- PENDING: EC2 deploy and smoke.

## Remaining

- AWH 형식 검증을 다시 통과시킨다.
- EC2에 반영하고 API/브라우저 smoke를 확인한다.

## Exact Next Step

- exact next step: rerun AWH verification, then deploy to EC2 and smoke `/api/recommendations/{id}` plus `/recommendations/{id}`.

