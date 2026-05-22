# Session Handoff

## Current Status

- 상태: local_verified
- 기준일: 2026-05-22
- 완료:
  - task contract를 생성했다.
  - `/events`에서 news candidate 링크와 상태 설명을 `종목 AI 근거` / `흐름 AI 근거`로 분리했다.
  - `/events`에서 상위 흐름 후보의 관련 이벤트 empty text를 별도로 작성했다.
  - `/ai-evidence` 카드의 상세 버튼을 `종목 근거 상세` / `흐름 근거 상세`로 분리했다.
  - `/ai-evidence` 상단 badge를 `뉴스 AI 근거`로 정리했다.
- 막힌 점:
  - 없음.

## Planned Fix

- `/events`의 evidence label/detail/purpose 문구를 후보 종류별로 나눈다.
- `/ai-evidence`의 카드 badge와 상세 버튼명을 후보 종류별로 나눈다.
- 관련 이벤트가 없는 경우 직접 종목 후보와 상위 흐름 후보를 다르게 설명한다.

## Verification Log

- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task candidate-card-wording-cleanup`
- PENDING: EC2 deploy/browser smoke

## Remaining

- EC2 deploy and browser smoke.

## Exact Next Step

- exact next step: commit, push, deploy to EC2, and verify `/events` plus `/ai-evidence` through the tunnel.
