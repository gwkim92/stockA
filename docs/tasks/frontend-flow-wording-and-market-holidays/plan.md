# Frontend Flow Wording And Market Holidays Plan

## Steps

1. 공식 거래소 휴장일을 확인하고 repo 밖 data operations env에 full-closure dates를 추가한다.
2. 첫 화면에 사용자가 이해할 수 있는 end-to-end 시스템 플로우를 추가한다.
3. 네비게이션과 각 페이지 hero/metric/table wording에서 영어와 내부 구현 용어를 줄인다.
4. 주요 라우트가 데이터를 깨지지 않게 표시하는지 HTTP와 브라우저로 점검한다.
5. Next.js typecheck/build, env readiness, AWH, diff 검증을 실행한다.
6. handoff/review에 검증 증거와 남은 UX/데이터 리스크를 남긴다.

## Non-Goals

- 외부 holiday API 도입
- 화면 전체 디자인 재작성
- 실거래, 페이퍼 거래, write API 구현
- AI 추천 품질/스코어링 로직 변경
