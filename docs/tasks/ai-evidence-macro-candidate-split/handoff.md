# Session Handoff

## Current Status

- 상태: local_verified
- 기준일: 2026-05-22
- 완료:
  - task contract를 생성했다.
  - `/ai-evidence`를 직접 종목 후보와 상위 흐름 후보 섹션으로 분리했다.
  - `/events` 기본 판단 목록을 직접 종목 후보와 상위 흐름 후보 섹션으로 분리했다.
  - 종목 없는 거시/테마 뉴스가 오류가 아니라 상위 흐름 입력임을 설명하는 문구를 추가했다.
- 막힌 점:
  - 없음.

## Planned Fix

- `/ai-evidence`에서 `symbol`이 `UNKNOWN`/`UNCLASSIFIED`인 후보를 상위 흐름 후보 섹션으로 분리한다.
- `/events` 기본 판단 목록도 직접 종목 후보와 상위 흐름 후보를 분리한다.
- 상위 흐름 후보는 “종목 미분류 오류”가 아니라 “테마/거시 흐름으로 전파될 후보”라는 설명을 붙인다.

## Verification Log

- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task ai-evidence-macro-candidate-split`
- PENDING: EC2 deploy/browser smoke

## Remaining

- EC2 deploy and browser smoke.

## Exact Next Step

- exact next step: commit, push, deploy to EC2, and verify `/events` plus `/ai-evidence` through the tunnel.
