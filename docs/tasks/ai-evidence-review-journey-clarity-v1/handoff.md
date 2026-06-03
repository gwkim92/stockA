# ai-evidence-review-journey-clarity-v1 Handoff

## Current Status

- completed: local implementation, EC2 deployment, route smoke, browser wording smoke, and AWH verification are complete.

## Decisions

- This is a frontend wording and information-architecture clarity task only.
- Keep current backend payload shape and page layout structure.
- Keep all order and scoring boundaries unchanged.
- Normalize user-facing system copy from `AI 후보`, `후보`, `보유검토`, and `AI 증거` toward `AI 구조화 항목`, `항목`, `보유 상태 판단`, and `AI 근거`.
- Do not rewrite source-news Korean translations. If a translated news title says "투자 후보", that is source content and should remain intact.

## Changes

- `/ai-evidence` now presents AI news records as `AI 구조화 항목`, split into direct stock items, macro/theme flow items, passed results, and blocked items.
- `/ai-evidence/[evidenceId]` now normalizes API-derived trace copy before rendering, so validator/recommendation linkage text uses `보유 상태 판단`, `입력 항목`, and `뉴스 AI 구조화 항목`.
- `/ai-evidence/blocked` now describes blocked/low-signal records as `차단 항목` and `저신호 보류`, without implying a manual review or approval UI.
- `/ai-evidence/results` now describes passed AI output as investment inputs, not final recommendations or orders.
- `apps/web/src/lib/korean-labels.ts` now maps candidate-related system codes to `항목` or `대상` language where appropriate.

## Verification

- passed: source scan found no `AI 후보`, `검토서`, `보유검토`, `AI 판단`, `AI 증거`, `뉴스 묶음 증거`, or `AI 추출 증거` in target AI evidence page/component/label code.
- passed: `cd apps/web && npm run typecheck`.
- passed: `cd apps/web && npm run build`.
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`.
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`.
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task ai-evidence-review-journey-clarity-v1`.
- passed: EC2 deployed commit `ce76bd3`; `npm run typecheck` and `npm run build` passed on `/opt/stockanalysis/app/apps/web`.
- passed: EC2 services active after restart: `stockanalysis-web.service`, `stockanalysis-frontend-api.service`.
- passed: EC2 internal route smoke returned 200 for `/ai-evidence`, `/ai-evidence/ai-evidence-973`, `/ai-evidence/blocked`, and `/ai-evidence/results`.
- passed: local tunnel route smoke returned 200 for the same four routes at `http://127.0.0.1:13000`.
- passed: `/api/data-health` still reports `open_gates=[]`, `alert_destination.status=external_destination_verified`, `news_ai_eval_quality.status=passed`, and `outcome_maturity_wait_monitor.status=managed_wait`.
- passed: Playwright browser text smoke on the four routes found zero old terms: `AI 후보`, `검토서`, `보유검토`, `AI 판단`, `AI 증거`, `뉴스 묶음 증거`, `AI 추출 증거`.
- passed: Playwright confirmed intended terms:
  - `/ai-evidence`: `AI 구조화 작업대`, `직접 종목 항목`, `상위 흐름 항목`, `차단 항목`.
  - `/ai-evidence/ai-evidence-973`: `AI 구조화 항목`, `근거 사용 경로`, `원천 뉴스`, `자동 검증`.
  - `/ai-evidence/blocked`: `차단 항목 판정판`, `추천 입력에서 제외된 AI 구조화 항목`, `보유 상태 판단`.
  - `/ai-evidence/results`: `AI 통과 결과를 투자 입력으로만 본다`, `통과 항목`, `차단 항목`, `가상 매매`.
- note: bare `후보` remains only inside Korean source-news translations such as "상승 여력이 큰 중형주 후보" and "투자 후보로 언급". Those are source-content translations, not system wording.

## Next Step

- exact next step: continue the broader UX audit on `/intelligence` and then `/data-health`, because both still contain dense operational copy and older `AI 후보`/`검토 후보` wording outside this task's mutable surface.
