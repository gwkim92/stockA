# Session Handoff

## Current Status

- 상태: local_verified
- 기준일: 2026-05-22
- 완료:
  - task contract를 생성했다.
  - recommendation detail SQL에 `macro_flow_all_rows`와 `macro_flow_recent_rows`를 추가했다.
  - `propagated_impact_count`는 전체 rows에서 계산하고, `recent_flows`는 최근 8개 preview로 제한했다.
  - 추천 상세 UI에 전체 전파 근거 수와 최근 표시 수가 다를 수 있음을 명시했다.
- 막힌 점:
  - 없음.

## Planned Fix

- recommendation detail SQL에 `macro_flow_all_rows` CTE를 추가한다.
- `macro_flow_provenance`의 count/source run은 전체 rows에서 계산하고, `recent_flows`만 최근 8개로 제한한다.
- 추천 상세 UI는 “총 N개, 아래는 최근 preview”라고 설명한다.

## Verification Log

- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v`
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-macro-flow-total-count`
- PENDING: EC2 deploy/browser smoke

## Remaining

- EC2 deploy and browser smoke.

## Exact Next Step

- exact next step: commit, push, deploy to EC2, and verify `/api/recommendations/recommendation-52` plus browser detail page.
