# ai-evidence-detail-trace-ux-v3 Handoff

## Status

- completed: local implementation, local verification, GitHub push, EC2 deploy, EC2 route smoke, tunnel route smoke, and Playwright snapshot verification passed.

## Current Decision

- This is a frontend visibility slice only.
- The existing `EvidenceVisibilityTraceBoard` should become the main transition between the brief and detailed evidence sections.
- Individual evidence detail remains read-only. It shows source and linkage evidence but does not approve recommendations or orders.

## Next Step

- exact next step: continue the UX/page split sweep with `/source-documents/[documentId]`, focusing on replacing inline styles and making source document purpose, linked AI evidence, and original text disclosure easier to scan.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task ai-evidence-detail-trace-ux-v3`
- passed: `git diff --check`
- passed: EC2 `cd /opt/stockanalysis/app/apps/web && npm run typecheck`
- passed: EC2 `cd /opt/stockanalysis/app/apps/web && npm run build`
- passed: EC2 `sudo systemctl restart stockanalysis-web.service`
- passed: EC2 internal route smoke for `http://127.0.0.1:3000/ai-evidence/ai-evidence-547`
- passed: tunnel route smoke for `http://127.0.0.1:13000/ai-evidence/ai-evidence-547`
- passed: route smoke confirmed `AI 근거 핵심 요약` no longer renders.
- passed: Playwright snapshot found `한눈에 보는 근거 흐름`, `이 근거가 어디서 와서 어디에 쓰이는지 확인한다`, `원천 뉴스`, `한국어 번역`, `자동 검증`, `실시간 AI 호출 없음`, and `주문 없음`

## Risks

- This task improves comprehension only. It does not alter evidence data or validator decisions.
- Some older evidence records may have sparse visibility trace fields; existing fallback copy must remain safe.
