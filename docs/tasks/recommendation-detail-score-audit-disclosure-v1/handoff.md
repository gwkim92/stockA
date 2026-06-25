# recommendation-detail-score-audit-disclosure-v1 Handoff

## Status

- completed: implementation, unit tests, build, route QA, and harness verification passed locally.
- 로컬 완료: 구현, 단위 테스트, 빌드, route QA, 하네스 검증 통과.
- 시작 커밋: `2e6623a1`.

## Context

- Previous task added the top `투자 판단 요약` and `포지션 현실` sections.
- Remaining UX issue: the lower recommendation detail still exposed all score cards and calculation metadata at once.
- This task extracts the score/provenance/outcome area into a dedicated component and makes detailed calculation inputs progressive disclosure.
- The default view now shows recommendation score, score input count, active scoring inputs, judgment-assist inputs, and outcome measurement state.
- Detailed score cards and provenance metadata are still available inside the disclosure panel; provenance metadata was restored after review so the task does not remove audit detail.
- The shell skip link remains keyboard-accessible but is visually hidden until focus.

## Verification Evidence

- `cd apps/web && npm test -- --run`: passed, 12 files / 30 tests.
- `cd apps/web && npm run typecheck`: passed.
- `cd apps/web && npm run build`: passed.
- `bash scripts/verify_frontend_api_contract.sh`: passed.
- `bash scripts/verify_project_execution_roadmap.sh`: passed.
- `git diff --check`: passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-detail-score-audit-disclosure-v1`: passed.
- Browser QA against local production build `http://127.0.0.1:3002/recommendations/recommendation-471`: 375px, 768px, 1280px passed with no 4xx/5xx, no horizontal overflow, details closed by default, score cards hidden before expansion, visible after expansion, and no visible `pipeline`, `runner`, `artifact`, `canonical`, `shadow`, `설명용`, or `사용 경계`.
- Screenshot artifacts: `/tmp/stockanalysis-score-audit-qa-v2/mobile-375-viewport.png`, `/tmp/stockanalysis-score-audit-qa-v2/desktop-1280-viewport.png`, `/tmp/stockanalysis-score-audit-qa-v2/mobile-375-open.png`.

## Next Step

- exact next step: commit and push `develop`, deploy to EC2, restart Next.js, then smoke `http://127.0.0.1:13000/recommendations/recommendation-471`.
