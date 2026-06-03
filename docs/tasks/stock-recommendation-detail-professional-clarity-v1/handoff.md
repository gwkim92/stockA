# stock-recommendation-detail-professional-clarity-v1 Handoff

## Current Status

- in progress: local implementation and local verification are complete. GitHub push and EC2 deploy are next.

## Decisions

- This is a wording and evidence-clarity task only.
- Keep professional analysis layers visible, but avoid labels that imply a missing manual review button.
- Preserve the read-only trading boundary and recommendation weight freeze.

## Changes

- `/stocks` now labels portfolio-linked items as `보유 상태` instead of `보유 검토`, and recommendation-empty rows as `추천 전`.
- `/stocks/[symbol]` now uses `추천 근거 있음`, `보유 상태 확인`, `보유 상태 보기`, and `추천 근거 있음` for paper validation flow status.
- `/recommendations/[recommendationId]` now uses `추천 상세`, `AI 근거 검증 통과`, `판단 입력 가능`, `근거 대기`, `보유 상태 연결`, and `ETF·펀드 추천 근거`.
- Price/valuation wording now describes `가격 근거` and `판단 점수`, not action-less review states.

## Verification

- passed: text scan found no `추천 검토서`, `AI 검토`, `검토 입력 가능`, `검토 대기`, `추천 검토`, `보유 검토`, `검토 전`, `보강 후 검토`, `검토 차단`, `사람 검토`, or `보유검토` in the three target pages.
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- passed: `git diff --check`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task stock-recommendation-detail-professional-clarity-v1`

## Next Step

- exact next step: commit/push, deploy to EC2, and smoke `/stocks`, `/stocks/SPY`, and a representative recommendation detail route.
