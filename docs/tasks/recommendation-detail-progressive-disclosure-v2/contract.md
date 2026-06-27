# recommendation-detail-progressive-disclosure-v2 Contract

## Task Request

- request: 사용자가 추천 상세 화면이 여전히 과밀하고 전문 투자 판단서처럼 읽히지 않는다고 지적했다. 특히 추천 상세 하단의 전문 감사, 원천, AI 근거, 점수 감사, 재무·밸류에이션 섹션이 한 화면에 길게 노출되어 첫 판단 흐름을 방해하므로, 핵심 결론을 먼저 읽고 세부 근거는 필요한 경우 펼쳐보는 구조로 바꾼다.

## Purpose

추천 상세 화면의 하단 과밀 영역을 투자자용 요약 우선 구조로 정리한다. 사용자는 먼저 추천 결론, 포지션 현실, 판단 흐름, 핵심 리스크를 읽고, 세부 감사·원천·점수·AI 근거는 필요한 경우에만 펼쳐본다.

## Concrete Goal

- goal: `/recommendations/[recommendationId]` route를 summary-first 판단서로 유지하면서 하단의 깊은 근거 묶음을 route-local disclosure component로 접는다. 기본 화면은 추천 결론과 투자 의미를 우선 보여주고, 전문 감사·ETF/펀드 분석·재무 모델·가치 범위·AI 리서치·근거 대조·점수 감사는 명확한 제목을 가진 접힘 영역으로 제공한다.

## Scope

- Route: `/recommendations/[recommendationId]`
- Keep URL, backend DTO, DB schema, recommendation score, benchmark, portfolio position, broker/order boundary unchanged.
- Add route-local presentation components and CSS Modules only.
- Reduce direct JSX responsibility in `page.tsx`.
- Hide deep technical evidence behind native `<details>` disclosure blocks.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/_components/*.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/_components/*.module.css`
  - `apps/web/tests/e2e/investment-workspace.spec.ts`
  - `docs/tasks/recommendation-detail-progressive-disclosure-v2/*`

## Non Goals

- No scoring weight change.
- No AI extraction, validator, or scheduler logic change.
- No broker submit or paper trading behavior change.
- No EC2 systemd unit change unless deployment smoke requires restart.

## User-Facing Rules

- Investor-visible sections must avoid `pipeline`, `runner`, `artifact`, `fallback`, `canonical`, `shadow`, raw snake_case, `검토 가능`, `확인한다`, `봐야 한다`, `미수집`.
- Page must keep company stock and ETF/fund distinction.
- First visible flow stays decision-oriented; deep evidence is available but not forced into the default reading path.
- Korean text must wrap without horizontal overflow at 375px.

## Acceptance Criteria

- `/recommendations/<live-id>` renders with summary-first detail disclosures.
- Detailed professional audit, product/fund/financial analysis, evidence trace, macro flow, evidence review, and score audit are grouped into disclosure sections.
- `page.tsx` has less direct rendering responsibility than before.
- Local verification passes: `npm run typecheck`, `npm test`, `npm run build`, relevant e2e.
- Browser QA captures 375px, 768px, 1280px screenshots with no horizontal overflow.
- EC2 deploy uses `develop` only and route smoke returns 200.

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run build`
- verification command: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13008 npm run test:e2e`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-detail-progressive-disclosure-v2`
