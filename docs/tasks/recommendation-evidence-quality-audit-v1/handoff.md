# recommendation-evidence-quality-audit-v1 Handoff

## Status

- completed: local verification, EC2 deploy, EC2 API smoke, EC2 route smoke, local tunnel smoke, and in-app browser smoke passed.

## Scope

- Read-only recommendation evidence quality visibility.
- No scoring, benchmark, portfolio, broker, or live order changes.

## Current Decision

- Reuse the existing recommendation list read adapter instead of adding schema or write jobs.
- Keep detail-level `professional_evidence_audit` as the deep drilldown and add only a compact list-level `evidence_quality` summary.

## Verification So Far

- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-evidence-quality-audit-v1`
- passed: `git diff --check`
- passed on EC2: commit `cbb889d` deployed to `/opt/stockanalysis/app`.
- passed on EC2: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- passed on EC2: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m compileall -q src tests`
- passed on EC2: `cd apps/web && npm run typecheck`
- passed on EC2: `cd apps/web && npm run build`
- passed on EC2: `systemctl is-active stockanalysis-web.service stockanalysis-frontend-api.service` returned `active active`.
- passed on EC2: `/api/recommendations` returned recommendation count `12`, evidence quality summary `ready=0`, `gap=12`, `source_blocked=0`, first row `ARM paper_validation_pending`, missing layer `페이퍼 검증`, and `order_boundary=read_only_no_order`.
- passed on EC2 route smoke: `/recommendations` rendered `성과 검증 대기`, `근거 감사`, and `상위 흐름 점수`.
- passed through local tunnel: `http://127.0.0.1:13000/recommendations` rendered `성과 검증 대기`, `근거 감사`, `페이퍼 검증`, and `실거래 상태`.
- passed in app browser: `http://127.0.0.1:13000/recommendations` rendered `근거 감사`, `성과 검증 대기`, `상위 흐름 점수`, and no stale `투자 논리나 근거가 연결되지 않은 신호` copy.

## Next Step

- exact next step: start `stocks-page-professional-analysis-clarity-v1` to make stock detail pages show the same professional evidence stack clearly at the individual-symbol level.

## Risks

- The list-level audit checks evidence coverage and blockers; it does not prove valuation accuracy or recommendation alpha.
- All recommendation scoring weights, benchmark definitions, portfolio positions, broker submit, and live trading behavior remain unchanged.
