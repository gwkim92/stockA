# page-content-ux-audit-fix-v1 Handoff

## Status

- completed: route inventory, first UI audit, home duplicate remediation CTA reduction, Korean labels for English AI eval cases and runner names, local verification, EC2 deploy, EC2 route smoke, and local tunnel browser smoke passed.

## Findings

- `/` renders too many repeated remediation group cards and the same `보완 큐에서 처리` CTA appears dozens of times.
- `/data-health` still exposes some fixture case IDs and backend runner names in English, for example `direct nvda ai chip news`, `energy shock exxon direct`, and `low signal should block`.
- Current data analysis state is not treated as perfect: source limits and outcome maturity waits remain visible and should not be hidden.

## Current Scope

- Keep this as display/wording/visibility work only.
- Do not modify recommendation scoring, benchmark definitions, portfolio positions, schema, or broker/order boundaries.

## Next Step

- exact next step: continue the broader page-by-page UX pass, starting with `/intelligence`, `/ai-evidence`, `/cycle-map`, and `/recommendations` to reduce duplicate explanations and make the evidence path easier to read.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `git diff --check`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task page-content-ux-audit-fix-v1`
- passed on EC2: `cd /opt/stockanalysis/app/apps/web && npm run typecheck && npm run build`
- passed on EC2: `systemctl is-active stockanalysis-web.service stockanalysis-frontend-api.service` returned `active active`.
- passed on EC2: route smoke for `/`, `/data-health`, `/intelligence`, `/ai-evidence`, `/cycle-map`, `/recommendations`, `/stocks`, and `/paper-trading` returned HTTP 200.
- passed locally through the EC2 tunnel: `http://127.0.0.1:13000/` and `/data-health` returned HTTP 200.
- passed browser smoke: `/` renders 5 `보완 큐에서 처리` links plus one `보완 큐 전체 보기`, not dozens of repeated actions.
- passed browser smoke: `/data-health` renders `NVDA AI 반도체 뉴스 직접 영향`, `에너지 충격 XOM 직접 영향`, `저신호 뉴스 차단`, and `뉴스 한국어 번역`.
- passed API smoke on EC2: `/api/data-health` returned `overall_status=healthy`, `open_gates=[]`, `news_ai_eval_quality.status=passed`, `failed_case_count=0`, and `order_boundary=read_only_no_order`.

## Remaining Risks

- This pass improves page wording and density only. It does not redesign every page from scratch.
- EC2 live data may still show legitimate source limits, managed waits, or blocked recommendations; those should remain visible rather than hidden.
