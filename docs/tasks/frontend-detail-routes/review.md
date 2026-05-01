# Review Notes

## Scope Review

- 작업 범위는 read-only fixture-backed detail routes로 제한한다.
- live DB adapter, auth/RBAC, write APIs, AI evidence route는 범위 밖이다.

## Verification Evidence

- `bash scripts/verify_frontend_detail_routes.sh`: 통과
- `npm run typecheck`: `verify_frontend_detail_routes.sh` 안에서 통과
- `next build`: `verify_frontend_detail_routes.sh` 안에서 통과
- Next production route smoke for `/recommendations/AAPL-2024-11-01`, `/theses/AAPL-bootstrap-v1`, `/portfolio/coverage`: `verify_frontend_detail_routes.sh` 안에서 통과
- fixture server regression check: `verify_frontend_detail_routes.sh` 안에서 통과
- `bash -n scripts/verify_frontend_detail_routes.sh`: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-detail-routes`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음
- follow-up browser QA evidence: `docs/tasks/frontend-browser-qa/review.md`

## Residual Risks

- fixture-only route는 live data freshness를 보장하지 않는다.
- dynamic route ids는 현재 contract example ids에 한정된다.
- AI evidence/source document route는 아직 구현하지 않았다.
