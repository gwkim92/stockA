# decision-cockpit-evidence-clarity-v1 Handoff

## Current Status

- completed: local implementation, local verification, AWH verify, GitHub push, EC2 deploy/build/restart, route smoke, Playwright text smoke, and data-health smoke are complete.

## Decisions

- Keep this as a frontend clarity slice, not a backend scoring or schema task.
- Use Korean user-facing judgment language first; leave operator details for `/data-health`.
- Avoid labels that imply a manual review button exists when the page only exposes read-only evidence.

## Changes

- Home page now describes the first decision path as `데이터 정상 여부 → 새 뉴스 근거 → 추천/보유/페이퍼 검증 → 주문 차단 경계`.
- Home page replaced action-less `검토 가능` wording with `판단 후보` / `추천 근거` where no explicit review action exists.
- Home page now exposes `주문 상태` in the hero summary so read-only/order-blocked status is visible before entering details.
- AI evidence detail now frames cluster evidence as a source-to-recommendation evidence path, not a buy/review decision.
- AI evidence detail replaced `AI 자동 판정` with `근거 사용 상태`, and `운영 경계` with clearer `주문 경계`.
- Recommendation-linked evidence copy now says the recommendation detail must combine price, cycle, financials, thesis, and paper/order boundary before any action.
- Global Korean labels now use `AI 검증` and `성과 표본 충족` instead of action-less `AI 검토` / `검토 가능` labels in the touched decision flow.

## Verification

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- passed: local text scan for `사람 검토`, `AI 검토`, `추천·보유검토`, and `검토 가능` in the touched files returned no matches.
- passed: first EC2 deploy/route smoke for commit `26d3b58`; `/` and `/ai-evidence/ai-evidence-973` rendered the new home and evidence-path wording.
- passed: final commit `6979c8a` deployed to EC2; `npm run build` passed and `stockanalysis-web.service` restarted active.
- passed: EC2 internal route smoke returned HTTP 200 for `/`, `/ai-evidence`, and `/ai-evidence/ai-evidence-973`.
- passed: Playwright text smoke on `http://127.0.0.1:13000/ai-evidence/ai-evidence-973` returned `hasAiVerification=true`, `hasAiReview=false`, `hasOrderBoundary=true`, and `hasEvidencePath=true`.
- passed: EC2 `/api/data-health` returned `overall_status=healthy`, `open_gates=[]`, `alert_destination.status=external_destination_verified`, `live_ai_invocation_health.status=recovered_with_recent_failures`, and `news_ai_eval_quality.status=passed`.

## Next Step

- exact next step: continue the broader UX audit with `/data-health`, `/intelligence`, `/cycle-map`, `/recommendations`, and `/paper-trading`, focusing on duplicate wording, operator-only phrasing, and pages that show status without an obvious decision path.
