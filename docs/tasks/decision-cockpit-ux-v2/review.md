# Review

## Result

- 공통 판단 흐름 컴포넌트 `DecisionReviewStrip`를 추가했다.
- 홈, 데이터 상태, 뉴스·AI 판단, 흐름 지도, 가상 거래 점검 화면이 같은 5단계 판단 순서를 공유한다.
- 사용자는 어느 화면에서든 현재 단계와 다음에 봐야 할 화면을 확인할 수 있다.
- 페이퍼 거래 화면은 “실거래가 아니라 가상 주문 검증”이라는 경계를 상단에서 반복 확인한다.

## Changed Surface

- `apps/web/src/components/decision-review-strip.tsx`
- `apps/web/src/app/page.tsx`
- `apps/web/src/app/data-health/page.tsx`
- `apps/web/src/app/intelligence/page.tsx`
- `apps/web/src/app/cycle-map/page.tsx`
- `apps/web/src/app/paper-trading/page.tsx`
- `apps/web/src/app/globals.css`
- `docs/tasks/decision-cockpit-ux-v2/*`

## Guardrails

- 추천 scoring weight 변경 없음.
- API DTO shape 변경 없음.
- DB schema 변경 없음.
- 실거래 broker submit 변경 없음.
- 저장형 승인/반려 write API 추가 없음.

## Remaining Risk

- 로컬 fixture는 2026-05-24 기준 뉴스 묶음 API fixture가 없어 브라우저 렌더가 끝까지 진행되지 않았다.
- 최종 UX 검증은 EC2 live tunnel에서 확인해야 한다.
