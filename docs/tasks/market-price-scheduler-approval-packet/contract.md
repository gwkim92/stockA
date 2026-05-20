# Task Contract

## Task

- 이름: market-price-scheduler-approval-packet
- 요청: `market-price-daily` scheduler 실제 활성화 전에 사용자가 이해할 수 있는 승인 패킷과 exact command를 정리한다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 현재 scheduler activation blocker가 plain Korean으로 설명된다.
  - 실제 실행될 install/launchctl command와 rollback command가 문서화된다.
  - approval record 템플릿이 제공된다.
  - 이 작업 안에서는 `launchctl`, LaunchAgents write/delete, child command 실행이 발생하지 않는다.

## Scope

- 포함:
  - `docs/market-price-scheduler-approval-packet.md`
  - `docs/plans/2026-05-20-market-price-scheduler-approval-packet.md`
  - `docs/tasks/market-price-scheduler-approval-packet/*`
- 제외:
  - 실제 `launchctl` 실행
  - `~/Library/LaunchAgents` 쓰기/삭제
  - repo-outside env secret 변경
  - DB/schema/backend/frontend 변경
  - trading/order behavior 변경

## Mutable Surface

- 수정 가능한 파일:
  - `docs/market-price-scheduler-approval-packet.md`
  - `docs/plans/2026-05-20-market-price-scheduler-approval-packet.md`
  - `docs/tasks/market-price-scheduler-approval-packet/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task market-price-scheduler-approval-packet`
  - `git diff --check`

## Done Criteria

- [x] Approval packet is written.
- [x] Exact execution commands are documented.
- [x] Exact rollback commands are documented.
- [x] Approval record template is included.
- [x] Verification commands pass.
- [x] Handoff and review are updated.
