# intelligence-flow-clarity-v1 Handoff

## Current Status

- completed: local implementation, EC2 deployment, route smoke, browser wording smoke, and AWH verification are complete.

## Decisions

- This is a frontend wording and information-architecture clarity task only.
- Keep current backend payload shape and page layout structure.
- Keep all order and scoring boundaries unchanged.
- Preserve source-news Korean translations as source content.
- Use `/intelligence` as the high-level news-flow map, not as a raw operations log or approval/review surface.

## Changes

- `/intelligence` metadata and hero now use `뉴스 흐름과 AI 근거` instead of `뉴스·AI 판단`.
- The page now describes the sequence as `오늘의 상위 흐름`, `통과한 AI 근거`, `차단·오염 의심`, and `추천 연결`.
- AI evidence wording now uses `AI 구조화 항목`, `AI 근거`, and `뉴스 묶음 근거` instead of `AI 후보` and `뉴스 묶음 증거`.
- Recommendation linkage copy now uses `추천 상세`, `보유 상태`, and `가상 매매` instead of `보유 검토` or `페이퍼`.
- Local page-specific impact-direction labels now render `risk_review` as `리스크 확인` on `/intelligence`.

## Verification

- passed: source scan found no `AI 후보`, `뉴스·AI 판단`, `뉴스 묶음 증거`, `AI 증거`, `보유검토`, `보유 검토`, `페이퍼`, or `검토서` in `apps/web/src/app/intelligence/page.tsx`.
- passed: `cd apps/web && npm run typecheck`.
- passed: `cd apps/web && npm run build`.
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`.
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`.
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task intelligence-flow-clarity-v1`.
- passed: EC2 deployed commit `7b7ca27`; `npm run typecheck` and `npm run build` passed on `/opt/stockanalysis/app/apps/web`.
- passed: EC2 services active after restart: `stockanalysis-web.service`, `stockanalysis-frontend-api.service`.
- passed: EC2 internal route smoke returned `200` for `/intelligence`.
- passed: local tunnel route smoke returned `200` for `http://127.0.0.1:13000/intelligence`.
- passed: `/api/data-health` still reports `open_gates=[]`, `alert_destination.status=external_destination_verified`, `news_ai_eval_quality.status=passed`, and `outcome_maturity_wait_monitor.status=managed_wait`.
- passed: Playwright browser text smoke for `/intelligence` found zero old terms: `AI 후보`, `뉴스·AI 판단`, `뉴스 묶음 증거`, `AI 증거`, `보유검토`, `보유 검토`, `페이퍼`, `검토서`, `리스크 검토`.
- passed: Playwright confirmed intended terms: `뉴스 흐름과 AI 근거`, `오늘의 확인 순서`, `AI 구조화 항목`, `뉴스 묶음 근거`, `보유 상태`, `가상 매매`, `리스크 확인`.

## Next Step

- exact next step: continue the broader UX audit on `/data-health`, because it intentionally contains operational state but still needs clearer separation between operator diagnostics and investor-facing status.
