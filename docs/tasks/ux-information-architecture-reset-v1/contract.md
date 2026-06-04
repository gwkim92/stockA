# ux-information-architecture-reset-v1 Contract

## Task Request

- request: 전체 웹사이트의 가시성 문제를 정보구조 관점에서 리셋한다. 기존처럼 문구를 더 붙이지 말고, 사용자가 각 페이지에서 결론·이유·다음 행동을 먼저 보게 만든다.

## Goal

- goal: 웹사이트의 주요 판단 화면을 원장 덤프형 첫 화면에서 벗어나게 하고, 사용자가 각 페이지 첫 화면에서 현재 결론, 핵심 근거, 다음 확인 위치를 먼저 보게 만든다.

## Mutable Surface

- mutable surface: `apps/web/src/app/globals.css`
- mutable surface: `apps/web/src/app/events/page.tsx`
- mutable surface: `apps/web/src/app/ai-evidence/page.tsx`
- mutable surface: `apps/web/src/app/ai-evidence/blocked/page.tsx`
- mutable surface: `apps/web/src/app/ai-evidence/results/page.tsx`
- mutable surface: `apps/web/src/app/page.tsx`
- mutable surface: `apps/web/src/app/data-health/page.tsx`
- mutable surface: `apps/web/src/app/intelligence/page.tsx`
- mutable surface: `apps/web/src/app/cycle-map/page.tsx`
- mutable surface: `apps/web/src/app/paper-trading/page.tsx`
- mutable surface: `apps/web/src/app/stocks/[symbol]/page.tsx`
- mutable surface: `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
- mutable surface: `apps/web/src/app/trading-readiness/page.tsx`
- mutable surface: `apps/web/src/app/portfolio/coverage/page.tsx`
- mutable surface: `apps/web/src/app/performance/page.tsx`
- mutable surface: `apps/web/src/app/stocks/page.tsx`
- mutable surface: `apps/web/src/app/recommendations/page.tsx`
- mutable surface: `apps/web/src/app/cycles/page.tsx`
- mutable surface: `apps/web/src/app/events/classification/page.tsx`
- mutable surface: `apps/web/src/app/remediation/page.tsx`
- mutable surface: `apps/web/src/app/source-documents/[documentId]/page.tsx`
- mutable surface: `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
- mutable surface: `apps/web/src/app/themes/[themeKey]/page.tsx`
- mutable surface: `apps/web/src/app/theses/[thesisId]/page.tsx`
- mutable surface: `docs/plans/2026-06-04-ux-information-architecture-reset-v1.md`
- mutable surface: `docs/tasks/ux-information-architecture-reset-v1/`

## Invariants

- Do not change backend schema.
- Do not change recommendation scoring weights.
- Do not change benchmark definitions, portfolio positions, paper validation records, broker/order flow, live trading, or scheduler cadence.
- Do not hide source limitations or blocked state; compress them into clearer decision summaries.
- Do not add write actions or review buttons that do not actually persist decisions.

## Scope

- Replace repeated giant hero/command-panel patterns on the first news/AI pages with compact decision summaries.
- Extend the same pattern to major investor decision pages: home, data health, intelligence, cycle map, stock detail, recommendation detail, and paper trading.
- Keep raw lists available below fold.
- Use Korean investor-facing copy, not operator-log phrasing.
- Preserve existing read-only route data calls.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task ux-information-architecture-reset-v1`
- verification command: `git diff --check`

## Done Criteria

- `/events` first viewport shows current conclusion and next action before event ledger rows.
- `/ai-evidence` first viewport separates direct evidence, macro-flow evidence, blocked evidence, and latest detail without dumping rows first.
- `/ai-evidence/blocked` first viewport explains what stays blocked versus what needs taxonomy/alias remediation.
- `/ai-evidence/results` first viewport separates recommendation input, macro-flow, direct instrument, and no-order boundary.
- `/`, `/data-health`, `/intelligence` first viewport tells the user what needs attention today before raw monitoring details.
- `/cycle-map` first viewport explains the hottest flow, news impact count, exposed nodes, and recommendation links before graph layers.
- `/stocks/[symbol]` first viewport separates recommendation, holding, news/flow, and thesis before dense professional evidence panels.
- `/recommendations/[recommendationId]` first viewport separates recommendation decision, score, professional step state, paper validation, and live order boundary.
- `/paper-trading` first viewport clearly distinguishes simulated actions from real order submission.
- `/trading-readiness` first viewport explains live order status, blocked gates, kill switches, and audit boundary.
- `/portfolio/coverage` first viewport explains holding risk, thesis gaps, review maturity, and no-order boundary.
- `/performance` first viewport explains measured outcome, sample quality, attribution, exclusions, and no automatic weight/order change.
- `/stocks` first viewport points to the first stock to inspect and separates recommendation, holding, watch-only, and data freshness buckets.
- `/recommendations` first viewport points to the first recommendation to inspect and separates evidence, paper validation, order block, and source blockers.
- `/cycles` first viewport separates cycle changes, evidence axes, and upstream flow map.
- `/events/classification` first viewport separates rule tags, direct-instrument tags, macro-only tags, and AI-linked/unlinked rows.
- `/remediation` first viewport separates open tickets, high-risk gaps, allocation policy, and no-auto-action boundary.
- `/source-documents/[documentId]` first viewport separates Korean source summary, excerpts, linked AI evidence, and access policy.
- `/ai-evidence/[evidenceId]` first viewport separates evidence use status, source document, stock connection, recommendation connection, and model/cost metadata.
- `/themes/[themeKey]` first viewport separates cycle state, linked instruments, supporting events, and upstream flow map.
- `/theses/[thesisId]` first viewport separates latest review, professional gates, evidence ledger, and no-order boundary.
- Existing data remains reachable below fold.
