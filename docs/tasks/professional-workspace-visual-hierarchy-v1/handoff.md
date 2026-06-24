# professional-workspace-visual-hierarchy-v1 Handoff

## Current Status

- 완료: implemented locally, pushed to `develop`, deployed to EC2, and smoke verified on live `127.0.0.1:13000`.

## Current Decision

이번 작업은 기능 추가가 아니라 핵심 페이지의 정보 위계 개선이다. 데이터 상태, 추천 상세, 종목 상세의 첫 화면에서 사용자가 무엇을 먼저 봐야 하는지 분명하게 만든다.

## Changed

- Added shared `workspace-brief` and `workspace-command-grid` CSS for professional research workspace hierarchy.
- Applied the hierarchy to `/data-health`, `/stocks/[symbol]`, and `/recommendations/[recommendationId]`.
- Fixed data-health command card tone mapping from `ready/watch/block` to the correct visual classes.
- Reduced repeated recommendation wording by separating conclusion, next check order, and decision flow.
- Added market-map DTO normalization so older/partial fixture payloads render as missing data instead of a server-component error.
- Added a read-only AI agent registry fallback so `/admin/ai-agents` still renders when the fixture endpoint is absent.
- Removed remaining visible internal English terms from the fallback AI agent screen copy.

## Verification

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `git diff --check`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task professional-workspace-visual-hierarchy-v1`
- passed: fixture-backed local production route smoke for `/`, `/market-map`, `/cycle-map`, `/stocks/AAPL`, `/recommendations`, `/recommendations/AAPL-2024-11-01`, `/paper-trading`, `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked`, `/data-health`, `/portfolio/coverage`, `/admin/ai-agents`.
- passed: rendered visible text scan found no visible hits for `canonical`, `shadow`, `pipeline`, `artifact`, `runner`, `fallback`, `LLM`, `human review`, `사람 검토`, `검토 가능`.
- passed: rendered visible text scan found no visible server-component/error-like text on the same route set.
- passed on EC2 commit `211c40e8`: `git pull --ff-only origin develop`, `cd apps/web && npm run typecheck && npm run build`, `sudo systemctl restart stockanalysis-frontend-api.service stockanalysis-web.service`, both services `active`.
- passed on EC2 internal route smoke: `/`, `/market-map`, `/cycle-map`, `/stocks/AAPL`, `/recommendations`, `/recommendations/recommendation-455`, `/paper-trading`, `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked`, `/data-health`, `/portfolio/coverage`, `/admin/ai-agents` all `200`; `/__ready` returned `status=ok`, `source_mode=live`.
- passed on local tunnel `http://127.0.0.1:13000`: `/data-health`, `/stocks/AAPL`, `/recommendations/recommendation-455`, `/market-map`, `/admin/ai-agents` returned `200`.
- passed on live `127.0.0.1:13000` rendered visible text scan for the 13 route set: no visible hits for `canonical`, `shadow`, `pipeline`, `artifact`, `runner`, `fallback`, `LLM`, `human review`, `사람 검토`, `검토 가능`; no visible server-component/error-like text.

## Next

- exact next step: continue the broader UX refactor on pages that still do not use the new workspace hierarchy, starting with `/market-map`, `/cycle-map`, `/recommendations`, `/paper-trading`, and `/ai-evidence`.
