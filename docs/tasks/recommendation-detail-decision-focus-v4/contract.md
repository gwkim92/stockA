# recommendation-detail-decision-focus-v4 Contract

## Task Request

- request: 추천 상세 화면이 한눈에 읽히지 않는다. 사용자가 추천서를 열었을 때 먼저 무엇을 봐야 하는지, 어디가 차단됐는지, 어떤 근거 경로를 따라가야 하는지 상단에서 명확히 보여준다.

## Goal

- goal: `/recommendations/[recommendationId]` 상단이 `추천서 읽는 순서`를 제공하고, 원천 차단·전문 분석 차단·가상 매매 입력 차단·성과 대기·근거 경로·재무/밸류·시장 동조성 중 사용자가 먼저 볼 지점을 고정한다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/recommendation-detail-decision-focus-v4/*`

## Scope

- Add a top-level recommendation focus panel.
- Improve the professional waterfall density so the seven-step sequence is easier to scan.
- Keep all existing data contracts, recommendation scores, weight behavior, broker/order boundaries, portfolio state, benchmark state, and schema unchanged.

## Non-Goals

- Do not change recommendation scoring weights.
- Do not change paper trading eligibility logic.
- Do not change broker submit behavior.
- Do not add new backend data.
- Do not alter benchmark, portfolio, or outcome evaluation policy.

## User-Facing Criteria

- The page states the first thing to review.
- The page separates blocking conditions, evidence path, professional analysis, market correlation, and paper trading status.
- The wording avoids internal-only terms where practical.
- The layout remains usable on desktop and mobile.

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-detail-decision-focus-v4`
- verification command: EC2 route smoke for `/recommendations` and a concrete `/recommendations/[id]`.
- verification command: Browser smoke through `http://127.0.0.1:13000`.
