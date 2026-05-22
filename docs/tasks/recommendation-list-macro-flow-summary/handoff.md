# Session Handoff

## Current Status

- 상태: local_verified
- 기준일: 2026-05-22
- 완료:
  - task contract를 생성했다.
  - recommendation list SQL에 `macro_flow_component_count`와 `macro_flow_evidence_count`를 추가했다.
  - recommendation list summary에 `macro_flow_evidence_recommendation_count`를 추가했다.
  - `/recommendations` 카드에 상위 흐름 근거 badge와 요약 문구를 표시했다.
- 막힌 점:
  - 없음.

## Planned Fix

- recommendation list SQL의 score component count에 `macro_flow_component_count`를 추가한다.
- recommendation row 별 propagated impact count를 bounded lateral query로 계산한다.
- `/recommendations` summary와 row card에 상위 흐름 근거 수를 표시한다.

## Verification Log

- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v`
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-list-macro-flow-summary`
- PENDING: EC2 deploy/browser smoke

## Remaining

- EC2 deploy and browser smoke.

## Exact Next Step

- exact next step: commit, push, deploy to EC2, and verify `/api/recommendations` plus `/recommendations`.
