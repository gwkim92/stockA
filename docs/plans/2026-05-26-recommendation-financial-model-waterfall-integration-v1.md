# recommendation-financial-model-waterfall-integration-v1 Plan

## Summary

- Goal: 추천 상세와 professional decision waterfall의 `financial_quality` 단계가 실제 `financial_statement_model`을 읽도록 연결한다.
- Scope: read-only visibility only. Recommendation score, score weight, benchmark split, paper/live trading boundary는 변경하지 않는다.

## Implementation

1. Add `financial_statement_model` to recommendation detail SQL output.
2. Reuse existing financial statement model payload builder so stock detail and recommendation detail share semantics.
3. Pass the model into `professional_decision_waterfall`.
4. Upgrade the `financial_quality` step to show latest financial period, computed metric count, and data gap count.
5. Render a Korean recommendation-detail panel for revenue growth, margins, cash flow, balance sheet, earnings quality, and dilution/share count.
6. Add regression coverage in `tests/test_frontend_live_adapter.py`.

## Guardrails

- No score or weight mutation.
- No benchmark or evaluation split change.
- No broker submit, automatic order, or kill-switch boundary change.
- Missing SEC/companyfacts-derived metrics remain data gaps; do not hallucinate values.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter`
- `PYTHONPATH=src python3 -m compileall -q src tests`
- `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-financial-model-waterfall-integration-v1`
