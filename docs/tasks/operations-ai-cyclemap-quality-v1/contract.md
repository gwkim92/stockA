# operations-ai-cyclemap-quality-v1 Contract

## Task Request

- request: `attention_required` 상태를 줄이고, Codex OAuth 기반 AI smoke를 회복하며, `/cycle-map` 투자자 화면 금지어 E2E 실패를 수정한다.
- context: paid OpenAI API quota 실패 이력은 삭제하지 않고, Codex OAuth와 local fallback 중심으로 최신 성공 invocation을 남긴다. 프론트는 투자자 화면에서 내부 실행 용어를 제거해야 한다.

## Goal

- goal: 운영 복구 명령은 기존 `stockanalysis-operations` boundary로 실행하고, `/cycle-map`은 투자자용 presentation mapping으로 raw 내부 용어를 숨기며, frontend API normalizer는 동작 변경 없이 도메인 파일로 분리한다. 최종 검증은 로컬 type/test/build/e2e와 EC2 service/data-health smoke로 확인한다.

Reduce current operating attention, recover bounded AI smoke visibility, fix the `/cycle-map` investor copy gate, split low-risk frontend API normalizers, and capture a baseline for service/performance checks without changing recommendation weights, schema, benchmark, portfolio positions, or broker order flow.

## Scope

- Run EC2 read-only operational recovery commands through existing `stockanalysis-operations` boundaries.
- Preserve failed AI invocation history; add new successful or explicit failure run evidence instead of deleting records.
- Remove raw internal terms from `/cycle-map` investor-facing text through presentation mapping only.
- Split independent frontend normalize functions out of `apps/web/src/lib/frontend-api.ts` while preserving public fetch APIs.
- Record route/API/service baseline evidence in repo task handoff.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/cycle-map/page.tsx`
  - `apps/web/src/app/cycle-map/_components/cycleMapModel.ts`
  - `apps/web/src/lib/frontend-api.ts`
  - `apps/web/src/lib/frontend-normalizer-utils.ts`
  - `apps/web/src/lib/frontend-normalizers-*.ts`
  - `apps/web/src/lib/korean-labels.ts`
  - `docs/tasks/operations-ai-cyclemap-quality-v1/*`

## Non-goals

- No paid OpenAI quota remediation.
- No recommendation weight changes.
- No DB schema migration.
- No live broker submit or order automation.
- No local AWS CLI writes; EC2 target remains personal account instance `3.211.40.142`.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run build`
- verification command: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13003 npm run test:e2e`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task operations-ai-cyclemap-quality-v1`

## Acceptance Criteria

- `/cycle-map` passes investor internal-copy E2E checks on mobile, tablet, and desktop.
- `npm run typecheck`, `npm test`, `npm run build`, and Playwright E2E pass locally against `http://127.0.0.1:13003`.
- EC2 route smoke confirms the deployed candidate remains reachable at `http://127.0.0.1:13000` after merge/deploy.
- EC2 smoke confirms FastAPI and Next services are active, `__ready` returns 200, and `/api/data-health` keeps `order_boundary=read_only_no_order`, `broker_submit_allowed=false`, and `automatic_weight_change_allowed=false`.
- Task handoff records commands, results, remaining gates, and any failed smoke with reason.
