# cycle-map-path-ux-v2 Handoff

## Status

- completed: local implementation, local verification, GitHub push, EC2 deploy, EC2 route smoke, tunnel route smoke, and Playwright snapshot verification passed.

## Current Decision

- This is a frontend visibility slice only.
- `/cycle-map` should read as the causal path map from news and macro/domain/theme nodes to exposed instruments and recommendation evidence.
- `/cycles` remains the theme-level state board.
- No graph, scoring, recommendation, broker, paper validation, order, portfolio, or benchmark state is mutated.

## Next Step

- exact next step: continue the broader UX/page split sweep with `/ai-evidence` list/results/blocked pages, focusing on making source news, Korean translation, AI extraction, validator outcome, and recommendation connection easier to trace.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task cycle-map-path-ux-v2`
- passed: `git diff --check`
- passed: EC2 `cd /opt/stockanalysis/app/apps/web && npm run typecheck`
- passed: EC2 `cd /opt/stockanalysis/app/apps/web && npm run build`
- passed: EC2 `sudo systemctl restart stockanalysis-web.service`
- passed: EC2 internal route smoke for `http://127.0.0.1:3000/cycle-map`
- passed: tunnel route smoke for `http://127.0.0.1:13000/cycle-map`
- passed: Playwright snapshot found `흐름 경로 판정판`, `뉴스가 어느 흐름을 거쳐 종목에 닿았는지 본다`, `원천 뉴스`, `흐름 노드`, `종목 노출`, `추천 연결`
- passed: Playwright/curl smoke confirmed sector/factor labels render in Korean, including `기술 섹터`, `에너지 섹터`, `채권`, `임의소비재`, and `금융 섹터`

## Risks

- This task improves comprehension only. It does not improve graph edge quality or propagation accuracy.
- Detailed source news and validator explanations remain on `/intelligence` and AI evidence pages.
