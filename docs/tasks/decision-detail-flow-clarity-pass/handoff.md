# Session Handoff

## Current Status

- 상태: in_progress
- in progress: 종목 상세, 추천 상세, 가상 거래 화면의 판단 흐름과 사용자-facing 문구를 정리한다.
- 기준일: 2026-05-23

## Investigation

- `/stocks/[symbol]`는 가격 차트, 추천, 보유, 뉴스, 상위 흐름을 모두 갖고 있으나 일부 링크/문구가 `이벤트 원장`, `검색 준비 상태`, `근거 문서 조각`처럼 내부 표현이다.
- `/recommendations/[id]`는 직접 뉴스, 상위 흐름, 보유검토 trace가 있으나 링크 라벨이 `이벤트 원장 열기`, `종목 흐름 보기` 등으로 흐름을 충분히 설명하지 못한다.
- `/paper-trading`은 실제 주문 여부와 가상 후보 상태를 보여주지만, 첫 화면에서 “현재 할 수 있는 것/할 수 없는 것/다음 확인 화면”이 더 명확해야 한다.

## Mutable Surface

- `apps/web/src/app/stocks/[symbol]/page.tsx`
- `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
- `apps/web/src/app/paper-trading/page.tsx`
- `apps/web/src/lib/korean-labels.ts`
- `docs/tasks/decision-detail-flow-clarity-pass/*`

## Exact Next Step

- exact next step: 세 페이지의 내부 표현을 사용자 문장으로 바꾸고, 각 화면 상단에 읽는 순서와 안전 상태를 더 선명하게 표시한 뒤 typecheck/build/AWH와 EC2 route smoke를 실행한다.
