# events-classification-decision-ux-v2 Handoff

## Status

- completed: local implementation, local verification, GitHub push, EC2 deploy, EC2 route smoke, tunnel route smoke, and Playwright snapshot verification passed.

## Current Decision

- This is a frontend visibility slice only.
- The classification page should explain that rule-based first tags are preliminary and must be checked against AI evidence and validator output.
- No rule pack, AI extraction, validator, propagation, recommendation, broker, paper validation, order, or portfolio state is mutated.

## Next Step

- exact next step: continue the broader UX/page split sweep with `/cycles`, focusing on making cycle status, evidence, and recommendation impact understandable without exposing internal runner language.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task events-classification-decision-ux-v2`
- passed: `git diff --check`
- passed: EC2 `cd /opt/stockanalysis/app/apps/web && npm run typecheck`
- passed: EC2 `cd /opt/stockanalysis/app/apps/web && npm run build`
- passed: EC2 `sudo systemctl restart stockanalysis-web.service`
- passed: EC2 internal route smoke for `http://127.0.0.1:3000/events/classification`
- passed: tunnel route smoke for `http://127.0.0.1:13000/events/classification`
- passed: Playwright snapshot found `1차 분류 판정판`, `테마 묶음`, `직접 종목`, `상위 흐름`, `AI 비교`, and `테마가 맞는지, 종목을 억지로 붙였는지 먼저 본다`

## Risks

- This task improves comprehension only. It does not improve classification accuracy.
- Richer per-event validator detail remains on AI evidence pages.
