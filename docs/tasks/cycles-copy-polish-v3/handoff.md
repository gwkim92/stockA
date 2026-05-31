# cycles-copy-polish-v3 handoff

## Status

- current status: completed.
- completed: task contract created.
- completed: `/cycles` copy and labels now emphasize cycle status, evidence axes, and recommendation/thesis review boundary in user-facing Korean.
- completed: EC2 deployment and route/content smoke passed.

## Changes

- changed hero copy so cycles are positioned as a 투자 논리 점검 지도, not a direct buy/sell signal.
- changed command panel to separate status, evidence, and recommendation impact.
- replaced `thesis` wording with `투자 논리`.
- replaced evidence axis labels with `뉴스 흐름`, `가격 흐름`, and `기업 품질`.
- changed theme CTA to `테마 상세 보기`.
- did not change cycle scoring, propagation, recommendation, portfolio, broker/order, API, or DB logic.

## Verification

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task cycles-copy-polish-v3`
- passed: `git diff --check`
- passed: EC2 deploy from `origin/codex/local-mvp-runtime-aws-bootstrap`, Next build, and `stockanalysis-web.service` restart.
- passed: `http://127.0.0.1:13000/cycles` returned 200 and contained `사이클은 매수 신호가 아니라 투자 논리 점검 지도다`, `상태, 근거, 추천 영향을 분리해서 본다`, `뉴스 흐름`, `가격 흐름`, `기업 품질`, `테마 상세 보기` with no `thesis`, `runner`, `artifact`, `근거 축`, or `가격 모멘텀`.
- passed: Playwright snapshot smoke for `/cycles` found required Korean terms and no targeted jargon.

## Exact Next Step

- exact next step: continue the page-by-page UX refactor with `/cycle-map`, because it should explain macro/domain/theme/instrument paths and evidence propagation more clearly.

## Notes

- frontend visibility only.
- cycle scoring, recommendation, portfolio, broker/order, API, and DB logic are not changed.
- commits: `ce080024`, `c81477f0`.
