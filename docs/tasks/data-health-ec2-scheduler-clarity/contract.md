# Task Contract

## Task

- 이름: data-health-ec2-scheduler-clarity
- 요청: `/data-health`가 현재 EC2에서 실제로 자동 실행 중인 프로파일 스케줄러와 과거 로컬 MVP 점검 기록을 같은 무게로 보여줘 사용자가 자동화 상태를 오해할 수 있다. 첫 화면에서 실제 EC2 자동 실행 주기와 각 작업의 목적을 바로 확인할 수 있게 정리한다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/data-health` 첫 화면에서 EC2 systemd 프로파일별 자동 실행 주기, 상태, 다음 실행, 작업 목적이 보이고, 과거 로컬 워커/수동 스모크 기록은 현재 자동화의 주 근거처럼 보이지 않는다.

## Scope

- 포함:
  - `/data-health` 첫 화면에 EC2 프로파일 스케줄러 카드 노출
  - 뉴스/AI, 주식 캔들, 추천/보유검토, 거시/공시/성과 작업의 목적을 사용자용 한국어로 표시
  - EC2 scheduler 설치 상태에서는 `manual_local_ingest_smoke`, `local_ingest_worker` 기록을 과거/보조 기록으로 표시
- 제외:
  - 백엔드 schema 변경
  - scheduler 설치/삭제/주기 변경
  - data operations runner 변경
  - secrets/env 변경

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/data-health/page.tsx`
  - `docs/tasks/data-health-ec2-scheduler-clarity/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations
  - EC2 systemd unit/timer files
  - backend scheduler cadence registry

## Verification

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task data-health-ec2-scheduler-clarity`
  - EC2 deploy 후 `GET http://127.0.0.1:13000/data-health` route smoke

## Done Criteria

- [ ] EC2 scheduler 설치 응답에서 “현재 EC2에서 실제로 도는 작업”이 첫 화면에 보인다.
- [ ] 과거 로컬 워커/수동 스모크 기록이 현재 자동화 상태처럼 보이지 않는다.
- [ ] Focused local verification passes.
- [ ] EC2 route smoke passes.
