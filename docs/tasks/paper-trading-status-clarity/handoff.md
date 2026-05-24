# Session Handoff

## Current Status

- 상태: in_progress
- 완료:
  - task contract를 만들었다.
  - `/paper-trading` 현재 단계 영역을 `실제 주문 제출`, `가상 검증 상태`, `거래 안전 차단`, `다음 확인` 4칸으로 재구성했다.
  - 가상 검증 차단 사유를 한국어 title/description으로 보여준다.
  - 거래 안전 상태와 추천 신호로 바로 이동하는 버튼을 추가했다.
  - broker submit, account permission, order limit, paper validation 계산 로직은 변경하지 않았다.

## Verification So Far

- `cd apps/web && npm run typecheck`: passed.
- `cd apps/web && npm run build`: passed.

## Exact Next Step

- exact next step: run `git diff --check` and AWH verify for `paper-trading-status-clarity`, then commit/push this slice.
- after EC2 SSH becomes reachable, deploy and visually smoke `/paper-trading` through `http://127.0.0.1:13000`.
