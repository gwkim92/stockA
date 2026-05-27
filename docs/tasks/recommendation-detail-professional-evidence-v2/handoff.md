# recommendation-detail-professional-evidence-v2 Handoff

## Status

- completed: local verification, EC2 deploy, EC2 API smoke, EC2 route smoke, and local tunnel smoke passed.

## Current Decision

- Build `professional_evidence_audit` from existing recommendation detail payloads rather than adding new schema or new write-side jobs.
- Keep this read-only. Recommendation weights, paper execution, and broker/order paths stay unchanged.

## Next Step

- exact next step: start `outcome-maturity-wait-monitor-v2` so the 2026-06-20 and 2026-06-24 outcome windows remain explicit and weight review stays blocked until mature evidence exists.

## Verification So Far

- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task recommendation-detail-professional-evidence-v2`
- passed: `git diff --check`
- passed on EC2: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- passed on EC2: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m compileall -q src tests`
- passed on EC2: `cd apps/web && npm run typecheck && npm run build`
- passed on EC2: `systemctl is-active stockanalysis-frontend-api.service stockanalysis-web.service` returned `active active`.
- passed on EC2: `/api/recommendations/recommendation-67` returned `professional_evidence_audit.status=source_blocked`, `coverage_ratio=0.2778`, `missing_layer_count=6`, `paper_validation_status=blocked_source`, `paper_validation_input_allowed=false`, `source_blocker.blocker_code=sec_companyfacts_missing_us_gaap_facts`, `paper_validation` layer `blocked`, and `order_boundary=read_only_no_order`.
- passed on EC2: `/recommendations/recommendation-67` rendered `추천 전문 분석 감사`, `전문 원천 차단 추천`, `근거 커버리지`, `거래 경계`, and `weight 변경`.
- passed locally through the EC2 tunnel: `http://127.0.0.1:13000/recommendations/recommendation-67` rendered `추천 전문 분석 감사`, `전문 원천 차단 추천`, `근거 커버리지`, `거래 경계`, and `weight 변경`.

## Risks

- This audit verifies whether professional evidence layers are present and visible; it does not prove valuation accuracy.
- Recommendation scoring weights, benchmark definitions, portfolio positions, broker submit, and live trading behavior were not changed.
