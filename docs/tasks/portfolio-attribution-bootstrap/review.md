# Review

## Review Notes

- attribution v1은 deterministic `position_weighted_alpha_v1`로 구현했다.
- `security_selection`과 `theme_exposure`는 같은 underlying contribution을 서로 다른 관점으로 저장한다. consumer는 `component_type`별로 분리해서 해석해야 한다.
- LLM은 계산 경로에 넣지 않았다. 향후 AI는 attribution 결과 설명 report에만 붙이는 것이 현재 boundary에 맞다.

## Verification Evidence

- `python3 -m compileall src tests`: 통과
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`: 196 tests 통과
- `bash -n scripts/verify_portfolio_attribution_bootstrap.sh`: 통과
- `bash scripts/verify_portfolio_attribution_bootstrap.sh`: 통과
  - Docker Postgres migration/seed 적용 통과
  - `performance.attribution_run` 1건 확인
  - `performance.attribution_component` 3건 확인
  - AAPL `security_selection` contribution `30.0000` bps 확인
  - `ANNUAL_REPORTING` `theme_exposure` contribution `30.0000` bps 확인
  - `CASH` `cash_timing` weight `0.9500`, contribution `0.0000` bps 확인
  - latest `portfolio_attribution_bootstrap` run status `succeeded` 확인
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-attribution-bootstrap`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음
