# Session Handoff

## Current Status

- 상태: local_verified
- 기준일: 2026-05-22
- 완료:
  - task contract를 생성했다.
  - `/recommendations/[recommendationId]`에 `상위 흐름 전파 경로` 패널을 추가했다.
  - 기존 `macro_flow_propagation` provenance의 `recent_flows`를 사용하며 API/schema/scoring은 변경하지 않았다.
  - 각 flow row에 테마, 이벤트 제목, 방향, 강도, 신뢰도, 노출도, 발생 시점을 표시한다.
- 막힌 점:
  - 없음.

## Planned Fix

- `/recommendations/[recommendationId]`에서 `macro_flow_propagation` score component를 찾아 별도 패널에 표시한다.
- 각 flow row는 테마, 방향, 강도, 신뢰도, 노출도, 이벤트 제목을 보여준다.
- 기존 score component 목록은 유지하고, 패널은 데이터가 있을 때만 보여준다.

## Verification Log

- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-macro-flow-trace-panel`
- PENDING: EC2 deploy/browser smoke

## Remaining

- EC2 deploy and browser smoke.

## Exact Next Step

- exact next step: commit, push, deploy to EC2, find a recommendation with macro flow provenance, and browser-smoke the detail page.
