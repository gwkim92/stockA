# cycle-quality-audit-hardening-v1 Contract

## Task Request

- request: 오분류, 중복 묶음, 원문 근거 없는 종목 연결을 자동 감사하고 화면에서 확인 가능한 형태로 강화한다.
- context: 사용자는 뉴스/AI/사이클 화면에서 어떤 데이터가 오염됐는지, 무엇이 정상 macro flow인지, 왜 특정 종목이 연결됐는지 판단하기 어렵다고 지적했다.

## Goal

- goal: `cycle-ai-quality-audit-run`과 `/data-health`가 오염 의심 항목과 정상 macro flow 샘플을 함께 보여줘 운영자가 바로 확인할 수 있게 한다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/cycle_ai_quality_audit.py`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_cycle_ai_quality_audit.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/cycle-quality-audit-hardening-v1/*`

## Invariants

- Do not change recommendation scoring weights.
- Do not change benchmark, portfolio position, paper/live broker order flow, or order boundary.
- Do not call LLM from FastAPI or Next request path.
- Do not expose DB URL, bearer token, webhook URL, OAuth token, or repo-outside file paths in user-facing payloads.
- Treat macro-only news without direct ticker as normal when it has upper-flow classification.

## Scope

- Add richer audit samples for `macro_false_tickers` and `normal_macro_flows`.
- Include event title, symbol, instrument name, node codes, and impact direction where available.
- Surface sample groups on `/data-health` in Korean so the operator can distinguish contamination from valid macro flow.
- Keep cleanup execution separate. This task improves detection/visibility only.

## Verification

- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_cycle_ai_quality_audit tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task cycle-quality-audit-hardening-v1`
- verification command: `git diff --check`

## Done Criteria

- [ ] Audit SQL emits detailed sample payloads for macro false tickers and normal macro flows.
- [ ] `/data-health` renders audit sample groups in Korean without exposing secret paths.
- [ ] Unit tests cover the new sample payload shape.
- [ ] Local verification and EC2 smoke pass.
