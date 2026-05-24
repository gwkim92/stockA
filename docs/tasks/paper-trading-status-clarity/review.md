# Review

## Result

- `/paper-trading` 상단에서 실거래 여부, 가상 검증 상태, 차단 조건, 다음 확인 화면을 분리했다.
- 실제 주문 제출 건수가 0인지 아닌지를 첫 카드에서 바로 확인할 수 있다.
- `paper_validation.blocked_reasons`를 한국어 차단 사유 카드로 풀어 보여준다.
- 차단 조건이 있으면 `거래 안전 상태 보기`를 첫 행동으로 유도한다.

## Changed Surface

- `apps/web/src/app/paper-trading/page.tsx`
- `apps/web/src/app/globals.css`
- `docs/tasks/paper-trading-status-clarity/*`

## Guardrails

- broker submit 구현 없음.
- 계좌 권한/주문 한도 변경 없음.
- paper validation 계산 로직 변경 없음.
- 추천 scoring 변경 없음.

## Remaining Risk

- EC2 SSH가 timeout이라 live tunnel visual smoke는 아직 못 했다.
- 실제 운영 데이터에서 차단 사유가 긴 경우 모바일 줄바꿈을 EC2 화면으로 다시 확인해야 한다.
