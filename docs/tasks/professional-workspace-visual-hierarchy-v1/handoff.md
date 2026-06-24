# professional-workspace-visual-hierarchy-v1 Handoff

## Current Status

- 완료: implemented locally, verified with typecheck/build/AWH, and rendered route smoke on fixture-backed local production server.

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

## Next

- exact next step: commit, push to `develop`, deploy to EC2, restart FastAPI/Next, and smoke live routes `/data-health`, `/stocks/AAPL`, `/recommendations/recommendation-455`, `/market-map`, `/admin/ai-agents`.
