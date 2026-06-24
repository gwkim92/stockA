# professional-workspace-visual-hierarchy-v1 Contract

## Task Request

- request: 데이터 상태, 추천 상세, 종목 상세 화면의 시각 위계와 사용자용 문구를 정리한다.
- request: 사용자가 `오늘 무엇을 먼저 봐야 하는지`, `어떤 근거가 통과/차단됐는지`, `가상 매매와 실거래 경계가 어디인지`를 첫 화면에서 구분할 수 있게 만든다.

## Goal

- goal: `/data-health`, `/stocks/AAPL`, `/recommendations/recommendation-455` 상단에서 먼저 볼 결론 카드와 보조 확인 카드가 시각적으로 구분되고, 투자 판단 화면이 운영 로그처럼 보이지 않는다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/globals.css`
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `docs/tasks/professional-workspace-visual-hierarchy-v1/*`

## Scope

- Include shared workspace hero/card CSS.
- Make the first decision card visually dominant on the target pages.
- Separate repeated recommendation wording into conclusion, next check order, and decision flow.
- Correct user-facing card tone mapping for data-health command cards.

## Non-Goals

- No DB schema changes.
- No API payload changes.
- No recommendation scoring weight changes.
- No benchmark, outcome/evaluation split, portfolio position, scheduler, AWS, or broker/order changes.
- No Toss data promotion into recommendation/cycle scoring.

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task professional-workspace-visual-hierarchy-v1`
- verification command: Browser/route smoke for `/data-health`, `/stocks/AAPL`, `/recommendations/recommendation-455`

## Acceptance Criteria

- The target pages render with a clear primary decision card and secondary support cards.
- User-facing copy no longer repeats `현재 결론` in adjacent recommendation sections.
- Data-health top card tone matches `ready/watch/block` semantics.
- Investment screens do not reintroduce `canonical`, `shadow`, `pipeline`, `artifact`, `runner`, `fallback`, `LLM`, `human review`, `사람 검토`, `검토 가능` in the visible decision area.
