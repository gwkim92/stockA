# professional-analysis-quality-v1 Handoff

## Status

- completed: local verification, EC2 deploy, API smoke, EC2 route smoke, and local tunnel smoke passed.

## Current Decision

- Implement this as a derived visibility layer over existing professional coverage/source/outcome evidence.
- Do not introduce new scoring weights, broker/order behavior, paid data providers, or synthetic financial data.

## Next Step

- exact next step: continue outcome-backed professional quality calibration after the 2026-06-24 maturity window; do not change recommendation weights before that evidence exists.

## Verification So Far

- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task professional-analysis-quality-v1`
- passed: `git diff --check`
- passed on EC2: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- passed on EC2: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m compileall -q src tests`
- passed on EC2: `cd apps/web && npm run typecheck && npm run build`
- passed on EC2: `systemctl is-active stockanalysis-frontend-api.service stockanalysis-web.service` returned `active active`.
- passed on EC2: `/api/data-health` returned `professional_analysis_quality.status=managed_source_limited`, active candidates `23`, complete candidates `22`, source blocked `1`, average coverage `0.9674`, `automatic_weight_change_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`, and `open_gates=[]`.
- passed on EC2: `/data-health` rendered `전문 분석 품질`, `재무·피어·밸류에이션·산업·AI 리서치`, `원천 한계 관리 중`, `weight 변경 금지`, `읽기 전용·주문 금지`.
- passed locally through the EC2 tunnel: `http://127.0.0.1:13000/data-health` rendered `전문 분석 품질` and `읽기 전용·주문 금지`.

## Risks

- This is a quality visibility slice, not a full valuation model audit.
- Source-blocked symbols remain intentionally blocked until source remediation exists.
- Recommendation scoring weights, benchmark definitions, portfolio positions, broker submit, and live trading behavior were not changed.
