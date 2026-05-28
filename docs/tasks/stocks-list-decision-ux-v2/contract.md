# stocks-list-decision-ux-v2 Contract

## Task Request

- request: `/stocks` 목록 화면을 사용자가 종목을 어디서 어떻게 봐야 하는지 이해할 수 있게 재구성한다.

## Goal

- goal: 종목 목록 첫 화면에서 추천 연결, 보유 연결, 관찰 대상, 데이터 신선도를 분리해 보여주고, 각 종목 상세와 추천 근거로 바로 이동하게 한다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/stocks/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/stocks-list-decision-ux-v2/*`

## Invariants

- Do not change stock list API contracts.
- Do not change recommendation scoring weights, recommendation generation, benchmark definitions, portfolio positions, paper validation records, broker/order flow, or live trading.
- Do not add write actions or order buttons.
- Keep this task as frontend visibility and UX copy only.

## Scope

- Add a first-screen stock command panel that separates recommendation-linked stocks, held stocks, watch-only stocks, and stale/missing price data.
- Make the page say that source/professional evidence is checked in stock detail, not in the list itself.
- Keep row-level navigation explicit: stock detail and recommendation evidence links only.
- Preserve the existing stock table and summary data contract.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task stocks-list-decision-ux-v2`
- verification command: `git diff --check`

## Done Criteria

- [x] `/stocks` has a first-screen Korean command panel explaining recommended, held, watch-only, and stale/missing data groups.
- [x] The page routes users to stock detail and recommendation detail without implying a trade action.
- [x] Local frontend verification passes.
- [x] AWH task verification passes.
- [x] EC2/tunnel route smoke confirms the new Korean copy renders.
