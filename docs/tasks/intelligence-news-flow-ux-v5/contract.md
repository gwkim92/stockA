# intelligence-news-flow-ux-v5 Contract

## Task Request

- request: 인텔리전스 화면을 오늘의 상위 흐름, 통과한 AI 근거, 차단·오염 의심, 추천 연결 순서로 재구성한다.

## Goal

- goal: `/intelligence` 첫 화면에서 오늘 무엇을 먼저 봐야 하는지, 어떤 근거가 통과/차단됐는지, 추천·보유 화면으로 어디서 이어지는지 한눈에 알 수 있다.

판단 순서는 다음으로 고정한다.

1. 오늘의 상위 흐름
2. 통과한 AI 근거
3. 차단·오염 의심
4. 추천 연결

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/intelligence/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/intelligence-news-flow-ux-v5/*`

## Invariants

- recommendation weight, scoring formula, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- DB schema, FastAPI contract, scheduler, data ingest, AI batch runtime은 변경하지 않는다.
- 화면은 저장된 read-only 데이터만 조합하며 쓰기/검토 저장/주문 기능을 추가하지 않는다.

## Scope

- `apps/web/src/app/intelligence/page.tsx`
- `apps/web/src/app/globals.css`
- `docs/tasks/intelligence-news-flow-ux-v5/`

## Non-Goals

- 추천 score weight 변경 금지
- DB schema/API contract 변경 금지
- scheduler, data ingest, broker/order flow 변경 금지
- 실제 주문 또는 쓰기 기능 추가 금지

## Acceptance Criteria

- `/intelligence` 첫 화면에서 오늘 무엇을 먼저 봐야 하는지 명확해야 한다.
- 수집 뉴스 원장, AI 후보, 차단 후보, 추천 연결이 같은 의미로 중복 노출되지 않아야 한다.
- 운영자용 로그성 표현은 줄이고 사용자 판단 문구를 우선해야 한다.
- 모바일에서 카드와 버튼이 잘리지 않아야 한다.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task intelligence-news-flow-ux-v5`
- verification command: `git diff --check`
- verification command: EC2 또는 local tunnel에서 `/intelligence` route smoke

## Done Criteria

- [x] `/intelligence` 상단에 네 단계 판단 패널이 렌더링된다.
- [x] 기존 중복 검토 안내를 제거하고 대표 흐름, AI 후보, 차단 후보, 추천 연결 섹션을 분리한다.
- [x] 모바일에서 네 단계 카드와 요약 카드가 1열로 내려간다.
- [x] local verification과 EC2 route smoke가 통과한다.
