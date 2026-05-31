# source-document-trace-ux-v3 Handoff

## Status

- completed: local implementation, local verification, GitHub push, EC2 deploy, EC2 route smoke, tunnel route smoke, and Playwright snapshot verification passed.

## Current Decision

- This is a frontend visibility slice only.
- Source documents should be read as proof inputs for AI evidence, not recommendation or order approval screens.
- Existing source excerpts and linked AI evidence remain read-only.

## Next Step

- exact next step: continue the UX/page split sweep with thesis and recommendation detail pages, focusing on reducing English financial/research wording and making decision boundaries easier to scan.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task source-document-trace-ux-v3`
- passed: `git diff --check`
- passed: EC2 `cd /opt/stockanalysis/app/apps/web && npm run typecheck`
- passed: EC2 `cd /opt/stockanalysis/app/apps/web && npm run build`
- passed: EC2 `sudo systemctl restart stockanalysis-web.service`
- passed: EC2 internal route smoke for `http://127.0.0.1:3000/source-documents/rss%3Amarketwatch-topstories%3A8b0d961a7ac08839d1f3c2ff`
- passed: tunnel route smoke for `http://127.0.0.1:13000/source-documents/rss%3Amarketwatch-topstories%3A8b0d961a7ac08839d1f3c2ff`
- passed: Playwright snapshot found `원천 문서 작업대`, `AI 해석의 출발점을 한국어로 먼저 대조한다`, `문서 요약`, `검토 발췌`, `AI 근거 연결`, `접근 정책`, and `추천을 승인하는 화면이 아니다`

## Risks

- This task improves comprehension only. It does not improve source document extraction or translation quality.
- Some source documents may still lack Korean summaries and must fall back to inferred Korean digest copy.
