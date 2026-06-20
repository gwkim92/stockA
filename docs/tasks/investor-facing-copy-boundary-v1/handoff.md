# investor-facing-copy-boundary-v1 Handoff

## Status

- completed: local copy refactor, local verification, and user-facing copy search passed.

## Current Decision

- Investor-facing pages should not explain internal agent work, pipeline mechanics, or analysis implementation details as the primary message.
- User-facing pages should show conclusion, evidence, risk, blocked state, and next action.
- Operations/admin pages may keep internal wording because they are for system monitoring and troubleshooting.

## Changed Surfaces

- Home now frames the first screen as investment checkpoints, not internal operating sequence.
- `/intelligence`, `/events`, `/events/classification`, `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked`, `/ai-evidence/[id]`, `/cycle-map`, `/market-map`, `/stocks/[symbol]`, `/themes/[themeKey]`, `/source-documents/[id]`, and recommendation detail copy now prefer 투자 근거, 품질 기준, 추천 영향, 상위 흐름 language.
- `/data-health` and `/admin/ai-agents` are intentionally unchanged because they are operational surfaces.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `git diff --check`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task investor-facing-copy-boundary-v1`
- passed: investor-surface search excluding `/data-health` and `/admin` found no `AI가 한 일`, `처리 순서`, `AI 구조화`, `자동 검증`, `뉴스 AI`, `AI 후보`, `작업 방식`, `분석 방식`, `파이프라인`, or `구조화 결과`.

## Next Step

- exact next step: deploy to EC2 and smoke key routes so the running site reflects the copy boundary.

## Risks

- This task changes copy only. It does not improve data quality, AI result quality, recommendation scoring, or trading readiness.
- Some operational terms still appear in `/data-health` and `/admin/ai-agents` by design.
