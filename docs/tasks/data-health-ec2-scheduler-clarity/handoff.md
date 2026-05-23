# Session Handoff

## Current Status

- 완료:
  - `/data-health` 첫 화면에 EC2 프로파일 스케줄러 카드를 추가했다.
  - profile별 목적 문구를 사용자용 한국어로 추가했다.
  - EC2 systemd profile scheduler가 설치된 경우 과거 로컬 워커/수동 스모크 기록을 “현재 자동화의 주 근거가 아님”으로 표시하게 했다.
- 막힌 점:
  - 없음.

## Exact Next Step

- exact next step: `apps/web` 타입체크/빌드와 AWH 검증을 통과시킨 뒤 EC2에 배포하고 `/data-health` 화면을 다시 확인한다.

## Verification Evidence

- `cd apps/web && npm run typecheck` - passed.
- `cd apps/web && npm run build` - passed.
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter` - passed.
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests` - passed.
- `git diff --check` - passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task data-health-ec2-scheduler-clarity` - passed.
