# Review Notes

## Scope Review

- 이 작업은 frontend visual/browser QA와 작고 안전한 UI 보정으로 제한한다.
- live adapter, auth, benchmark, recommendation/performance 산식은 변경하지 않는다.

## Verification Evidence

- Browser QA report: `docs/tasks/frontend-browser-visual-qa/report.md`.
- Evidence screenshots under `output/playwright/frontend-browser-visual-qa/screenshots/`.
- Final mobile width check on `/performance`: `clientWidth=390`, `scrollWidth=390`.
- Production console/errors: clean for checked routes.
- `STOCKANALYSIS_FRONTEND_API_BASE_URL=http://127.0.0.1:8766 npm run build`: exit 0 during QA.
- `bash scripts/verify_frontend_detail_routes.sh`: exit 0 after final CSS changes.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-browser-visual-qa`: exit 0.
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: no output.
- `git diff --check`: exit 0.

## Residual Risks

- QA used fixture data only.
- Full accessibility audit and live deployment smoke remain separate tasks.
- Browser artifact images are local evidence and are not intended as permanent repo assets.
