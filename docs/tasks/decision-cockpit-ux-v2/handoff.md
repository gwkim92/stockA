# Session Handoff

## Current Status

- 상태: in_progress
- 완료:
  - `decision-cockpit-ux-v2` contract를 만들었다.
  - 공통 `DecisionReviewStrip` 컴포넌트를 추가했다.
  - `/`, `/data-health`, `/intelligence`, `/cycle-map`, `/paper-trading` 상단에 같은 5단계 판단 흐름을 연결했다.
  - 각 화면의 활성 단계가 다르게 보이도록 했다.
  - 추천 산식, API DTO, DB schema, broker/order flow는 변경하지 않았다.

## UX Direction

- 공통 판단 순서:
  - `01 수집 상태`
  - `02 뉴스·AI 근거`
  - `03 상위 흐름`
  - `04 추천·보유`
  - `05 페이퍼 안전`
- 각 페이지는 같은 순서를 보여주되 현재 페이지의 단계만 강조한다.
- 데이터 상태 화면은 운영 로그가 아니라 판단 게이트로 설명한다.
- 인텔리전스 화면은 뉴스 묶음, AI 해석, 직접 종목/상위 흐름 관계를 먼저 보게 한다.
- 사이클맵은 추천 전 단계의 상위 흐름 지도임을 강조한다.
- 페이퍼 거래는 실거래 직전 화면이 아니라 안전 검증 단계임을 강조한다.

## Verification So Far

- `cd apps/web && npm run typecheck`: passed.
- `cd apps/web && npm run build`: passed.
- `git diff --check`: passed.
- Local fixture browser attempt:
  - Next dev server started on `127.0.0.1:3001`.
  - Fixture server started on `127.0.0.1:8765`.
  - Browser render did not complete because the fixture server lacks current-date `/api/ai/news-clusters?asOfDate=2026-05-24&limit=3`.
  - This is a fixture coverage limitation, not a TypeScript/build failure.

## Exact Next Step

- exact next step: commit and deploy this slice to EC2, then verify through the live tunnel at `http://127.0.0.1:13000` for `/`, `/data-health`, `/intelligence`, `/cycle-map`, `/paper-trading`.
- after EC2 visual smoke, update this handoff/review with route evidence and mark the task completed.
