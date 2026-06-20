# investor-facing-copy-boundary-v1 Handoff

## Status

- completed: local copy refactor, GitHub push, EC2 deploy, EC2 route smoke, local tunnel route smoke, and user-facing copy search passed.

## Current Decision

- Investor-facing pages should not explain internal agent work, pipeline mechanics, or analysis implementation details as the primary message.
- User-facing pages should show conclusion, evidence, risk, blocked state, and next action.
- Operations/admin pages may keep internal wording because they are for system monitoring and troubleshooting.

## Changed Surfaces

- Home now frames the first screen as investment checkpoints, not internal operating sequence.
- `/intelligence`, `/events`, `/events/classification`, `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked`, `/ai-evidence/[id]`, `/cycle-map`, `/market-map`, `/stocks/[symbol]`, `/themes/[themeKey]`, `/source-documents/[id]`, and recommendation detail copy now prefer 투자 근거, 품질 기준, 추천 영향, 상위 흐름 language.
- Shared Korean labels, common news cards, stock detail normalization, and backend evidence DTO strings were also updated so old process wording does not reappear through data-driven messages.
- `/data-health` and `/admin/ai-agents` are intentionally unchanged because they are operational surfaces.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `PYTHONPATH=src python3 -m compileall -q src`
- passed: `git diff --check`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task investor-facing-copy-boundary-v1`
- passed: investor-surface search excluding `/data-health` and `/admin` found no `AI가 한 일`, `처리 순서`, `AI 구조화`, `자동 검증`, `뉴스 AI`, `AI 후보`, `작업 방식`, `분석 방식`, `파이프라인`, or `구조화 결과`.
- passed on EC2: `git pull --ff-only origin develop`, Python compile, Next typecheck, Next build, and `stockanalysis-web.service`/`stockanalysis-frontend-api.service` active at commit `83281159`.
- passed on EC2: `/`, `/intelligence`, `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked`, `/cycle-map`, `/events`, `/events/classification`, `/market-map`, `/recommendations`, `/stocks/AAPL` returned 200 with required investor-facing terms and no forbidden process-copy terms.
- passed through local tunnel: `http://127.0.0.1:13000/`, `/intelligence`, `/ai-evidence`, `/stocks/AAPL` returned 200 and rendered investor-facing evidence terms.

## Next Step

- exact next step: continue the UX audit with pages not deeply redesigned yet, especially `/cycles`, `/paper-trading`, `/performance`, `/portfolio/coverage`, and recommendation detail layout density.

## Risks

- This task changes copy only. It does not improve data quality, AI result quality, recommendation scoring, or trading readiness.
- Some operational terms still appear in `/data-health` and `/admin/ai-agents` by design.
