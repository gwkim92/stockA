# decision-cockpit-evidence-clarity-v1 Handoff

## Current Status

- in progress: local implementation and local verification are complete; EC2 deploy/route smoke is pending.

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

## Verification

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`

## Next Step

- exact next step: run AWH verify, commit/push, deploy to EC2, rebuild/restart Next.js, and route-smoke `/`, `/ai-evidence`, and `/ai-evidence/ai-evidence-973`.
