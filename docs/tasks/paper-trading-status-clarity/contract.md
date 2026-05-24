# Task Contract

## Task

- 이름: paper-trading-status-clarity
- 요청: 페이퍼 거래가 테스트 중인지, 차단됐는지, 실행 가능한 상태인지 명확히 표시한다.
- 담당: Codex
- 날짜: 2026-05-24

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/paper-trading` 상단에서 `실거래 여부`, `페이퍼 후보 상태`, `차단 조건`, `다음 확인`이 분리되어 보인다.

## Scope

- 포함:
  - 페이퍼 거래 상태를 `실거래 제출`, `가상 검증`, `차단 조건`, `다음 행동`으로 분리 표시
  - 차단 사유와 실제 주문 제출 건수를 사용자 문장으로 설명
  - 추천/보유 충돌 후보 표는 유지
- 제외:
  - broker submit 구현
  - 계좌 권한 변경
  - 주문 한도 변경
  - paper validation 계산 로직 변경
  - 추천 scoring 변경

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/paper-trading/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/paper-trading-status-clarity/*`
- 수정 금지 파일:
  - backend trading runner
  - broker/order submit path
  - DB migrations
  - env/secrets
  - recommendation scoring

## Verification

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task paper-trading-status-clarity`

## Done Criteria

- 사용자가 현재가 실거래가 아니라 페이퍼 검증 단계임을 상단에서 바로 이해한다.
- 실제 주문 전송 건수가 0인지 아닌지가 상단에 보인다.
- 차단 조건과 승인 후보가 분리되어 보인다.
- 다음에 봐야 할 화면이 거래 안전 상태인지 추천 상세인지 명확하다.
