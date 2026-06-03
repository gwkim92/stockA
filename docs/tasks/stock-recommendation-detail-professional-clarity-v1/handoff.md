# stock-recommendation-detail-professional-clarity-v1 Handoff

## Current Status

- completed: local implementation, local verification, GitHub push, EC2 deploy/build/restart, route smoke, and browser text smoke are complete.

## Decisions

- This is a wording and evidence-clarity task only.
- Keep professional analysis layers visible, but avoid labels that imply a missing manual review button.
- Preserve the read-only trading boundary and recommendation weight freeze.

## Changes

- `/stocks` now labels portfolio-linked items as `보유 상태` instead of `보유 검토`, and recommendation-empty rows as `추천 전`.
- `/stocks/[symbol]` now uses `추천 근거 있음`, `보유 상태 확인`, `보유 상태 보기`, and `추천 근거 있음` for paper validation flow status.
- `/recommendations/[recommendationId]` now uses `추천 상세`, `AI 근거 검증 통과`, `판단 입력 가능`, `근거 대기`, `보유 상태 연결`, and `ETF·펀드 추천 근거`.
- Price/valuation wording now describes `가격 근거` and `판단 점수`, not action-less review states.
- Data-derived RAG quality gate messages on `/stocks/[symbol]` now pass through user-facing wording conversion before rendering.
- Data-derived professional decision step copy on `/recommendations/[recommendationId]` now maps `검토 전`, `검토 비중`, and related action-less review labels to decision/evidence wording.

## Verification

- passed: text scan found no `추천 검토서`, `AI 검토`, `검토 입력 가능`, `검토 대기`, `추천 검토`, `보유 검토`, `검토 전`, `보강 후 검토`, `검토 차단`, `사람 검토`, or `보유검토` in the three target pages.
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- passed: `git diff --check`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task stock-recommendation-detail-professional-clarity-v1`
- passed: commit `f4ab163` implemented the primary page wording cleanup.
- passed: commit `2745441` normalized data-derived RAG gate wording on stock detail.
- passed: commit `d970a72` normalized data-derived professional decision copy on recommendation detail.
- passed: EC2 `cd /opt/stockanalysis/app/apps/web && npm run typecheck`
- passed: EC2 `cd /opt/stockanalysis/app/apps/web && npm run build`
- passed: EC2 `stockanalysis-web.service` and `stockanalysis-frontend-api.service` are active after restart.
- passed: EC2 internal route smoke returned HTTP `200` for `/stocks`, `/stocks/SPY`, and `/recommendations/recommendation-209`.
- passed: EC2 `/api/data-health` returned `overall_status=healthy`, `open_gates=[]`, `alert_destination.status=external_destination_verified`, `live_ai_invocation_health.status=recovered_with_recent_failures`, and `news_ai_eval_quality.status=passed`.
- passed: local tunnel route smoke returned HTTP `200` for `/stocks`, `/stocks/SPY`, and `/recommendations/recommendation-209`.
- passed: Playwright text smoke on `/stocks` found no old review wording and found `보유 상태 보기`, `추천 전`.
- passed: Playwright text smoke on `/stocks/SPY` found no old review wording and found `보유 상태 보기`, `추천 근거 있음`, `추천 근거 연결`.
- passed: Playwright text smoke on `/recommendations/recommendation-209` found no old review wording and found `추천 상세`, `판단 입력 가능`, `보유 상태 연결`, `판단 전`, `권고 비중`.

## Next Step

- exact next step: continue the broader UX audit with the next route family, likely `/events`, `/events/classification`, `/source-documents/[documentId]`, and `/ai-evidence/results`, focusing on source-news readability and evidence trace clarity.
