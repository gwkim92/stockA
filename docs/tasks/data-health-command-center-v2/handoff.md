# data-health-command-center-v2 Handoff

## Status

- completed and deployed to EC2.

## Current Status

- 상태: local verification, EC2 deploy, route smoke, and in-app browser smoke passed.
- 기준일: 2026-06-16
- 완료:
  - task contract created.
  - current `/data-health` render structure inspected.
  - replaced the first-screen operation verdict cards with a five-axis command center:
    - `1. 지금 먼저`
    - `2. 자동 수집`
    - `3. 뉴스·AI 품질`
    - `4. 투자 안전`
    - `5. 원천·전문분석`
  - removed the duplicate `오늘 조치` priority card section from the first screen.
  - kept detailed decision cards in the existing collapsed detail area.
  - deployed commit `2633a15c` to EC2 `develop`.
- 막힌 점:
  - none.

## Intended Change

- Add a command-center section that groups data-health into immediate action, automation, data/AI quality, investment safety, and source limits.
- Remove or compress duplicate top priority cards so the first screen does not repeat the same judgment twice.
- Preserve detailed audit/log sections lower on the page.

## Verification

- Passed:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-command-center-v2`
  - EC2 deploy: `git pull --ff-only origin develop`, `npm run typecheck`, `npm run build`, `sudo systemctl restart stockanalysis-web.service`; service state `active`; commit `2633a15c`.
  - EC2 FastAPI smoke: `/api/data-health` returned `overall_status=attention_required`, `open_gates=['live_ai_invocation_health_attention']`.
  - EC2 Next route smoke:
    - `/data-health` rendered `1. 지금 먼저`, `2. 자동 수집`, `3. 뉴스·AI 품질`, `4. 투자 안전`, `5. 원천·전문분석`, `열린 확인 항목`, `수집/분석별 상태`.
    - duplicate `오늘 조치` section absent.
    - server error absent.
  - in-app browser smoke through `http://127.0.0.1:13000/data-health`:
    - command card count `5`.
    - first card: `즉시 조치 1개`.
    - automation card: `8/8개 활성 · 문제 실행 0개`.
    - AI quality card: `실제 AI 호출 확인 필요`.
    - investment safety card: `추천 산식·실거래 차단`.
    - professional source card: `원천 차단 1개`.
    - command grid: `repeat(auto-fit, minmax(210px, 1fr))`.
    - server error absent.

## Next Step

- exact next step: fix the underlying `live_ai_invocation_health_attention` gate by inspecting recent failed Codex OAuth model invocations, separating current failures from stale historical failures, and rerunning the limited AI smoke if credentials are valid.

## Risks

- This task is visibility-only. It does not repair the current AI invocation attention gate.
- Recommendation weights, benchmark definitions, portfolio positions, schema, scheduler cadence, paper execution logic, broker submit, and live trading behavior were not changed.
