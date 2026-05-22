# Task Contract: Cockpit Product Clarity Pass

## Request

- 첫 화면과 주요 운영 화면에서 사용자가 무엇을 봐야 하는지 명확히 한다.
- 중복되는 기능 지도와 개발자용 문구를 줄인다.
- 뉴스/종목 연결, 추천/보유 판단, paper 거래 상태를 사용자 관점으로 설명한다.

## Scope

- Next.js cockpit 화면 문구와 정보 구조를 정리한다.
- 첫 slice는 `/`, `/paper-trading`, 공통 뉴스 카드 문구에 집중한다.
- API contract, DB schema, 추천 산식, broker/order flow는 변경하지 않는다.

## Acceptance Criteria

- 첫 화면은 “수집 정상 여부 -> 뉴스/종목 영향 -> 추천/거래 안전” 순서가 명확하다.
- 첫 화면에서 같은 성격의 카드 목록이 반복되지 않는다.
- Paper 거래 화면은 현재가 실거래인지, paper 검증인지, 무엇이 막고 있는지 바로 보여준다.
- 뉴스 카드에서 종목이 없는 거시/테마 뉴스는 “종목 미분류”가 아니라 “시장/테마 뉴스”로 표현한다.
- Next typecheck/build와 EC2 route smoke가 통과한다.

## Non-goals

- 실거래 연결, broker submission, 주문 실행.
- 추천 품질 산식 변경.
- 뉴스 AI/RAG pipeline 구조 변경.
- 전체 페이지 디자인 전면 재작성.
