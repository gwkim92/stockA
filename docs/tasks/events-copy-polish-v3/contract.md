# events-copy-polish-v3

## Task Request

- request: `/events`, `/events/classification`, and shared news event cards에 남아 있는 내부 용어를 줄인다.

## Goal

- goal: 뉴스 화면을 투자자가 “수집 원장 → 1차 분류 → AI 판단 → 검증 통과/차단” 흐름으로 읽게 만들고, `validator`, `AI evidence`, `rule pack`, `exposure` 같은 개발자 용어를 사용자 문장으로 바꾼다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/events/page.tsx`
  - `apps/web/src/app/events/classification/page.tsx`
  - `apps/web/src/components/news-event-card.tsx`
  - `docs/tasks/events-copy-polish-v3/*`

## Non-Goals

- news ingest, enrichment, AI extraction, validator logic 변경 금지
- event classification, propagation, recommendation link logic 변경 금지
- DB/API contract 변경 금지
- broker/order/portfolio/scoring 변경 금지

## Acceptance Criteria

- `/events`와 `/events/classification` 주요 문구에 `validator`, `AI evidence`, `rule pack`, `exposure`가 그대로 보이지 않는다.
- 뉴스 카드 action과 tag가 “AI 판단 상세”, “검증 차단”, “저신호 보류”, “시장/테마 뉴스”처럼 사용자가 읽는 말로 표시된다.
- 기존 링크 구조는 유지한다: 원문, AI 근거 상세, 종목 상세, 테마 흐름.
- 검증은 Next typecheck/build, AWH verify, EC2 route/content smoke로 수행한다.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task events-copy-polish-v3`
- verification command: EC2 route/content smoke for `/events` and `/events/classification`
