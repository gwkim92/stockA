# Session Handoff

## Current Status

- 완료: State Street 공식 SPY daily holdings XLSX를 benchmark composition import로 연결했고, EC2에서 `provider_file` source로 적재한 뒤 guardrail/data-health smoke까지 통과했다.

## Implementation Notes

- 공식 source 후보: `https://www.ssga.com/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx`
- State Street SPY page는 `Download All Holdings: Daily` 링크를 제공한다.
- raw XLSX와 normalized CSV는 repo 밖 runtime/artifact 경로에 저장해야 한다.
- 추천 weight와 주문 경로는 절대 변경하지 않는다.
- 추가된 CLI: `stockanalysis-operations benchmark-composition-ssga-spdr-import-run`
- provider parser는 stdlib `zipfile`/`xml.etree.ElementTree`로 XLSX를 읽고, `BRK.B` 같은 class ticker를 `BRK-B`로 정규화한다.
- 명시적 `--create-missing-instruments` 옵션이 있을 때만 benchmark component용 missing instrument를 생성한다.
- guardrail source 선택은 `provider_file`을 `operator_upload`/`manual_seed`보다 우선한다.

## Verification

- Local focused tests:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_benchmark_composition_import tests.test_benchmark_composition_provider tests.test_data_operations_cli tests.test_portfolio_risk_budget_guardrail`
  - Result: `Ran 86 tests ... OK`
- Local compile:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - Result: passed
- Local official provider dry-run:
  - Parsed SSGA SPY daily holdings as of `2026-05-21`
  - `component_count=503`
  - `target_weight_total=0.99837820`
  - `coverage_status=full_enough_for_drift`
- EC2 deploy:
  - `/opt/stockanalysis/app` fast-forwarded to `8a914de`
  - EC2 focused tests: `Ran 86 tests ... OK`
- EC2 provider import:
  - command: `benchmark-composition-ssga-spdr-import-run --source-name ssga_spdr_spy_daily_holdings --create-missing-instruments --execute`
  - import `run_id=992`
  - `source_type=provider_file`
  - `source_as_of_date=2026-05-21`
  - `component_count=503`
  - `target_weight_total=0.99837820`
  - `coverage_status=full_enough_for_drift`
- EC2 guardrail rerun:
  - `portfolio-risk-budget-guardrail-run --portfolio-name "Long Term Paper" --as-of-date 2026-05-25 --execute`
  - `run_id=993`
  - `eval_run_id=23`
  - `risk_gate_decision=blocked_by_risk_budget_review`
  - `benchmark_drift.status=calculated`
  - `benchmark_source=ssga_spdr_spy_daily_holdings`
  - `source_type=provider_file`
  - `composition_coverage_weight=0.9983782`
  - `active_share=0.77853213`
  - top active outliers: `TSLA`, `MSFT`, `AAPL`
- EC2 API/route smoke:
  - `stockanalysis-frontend-api.service` and `stockanalysis-web.service` restarted and active.
  - `/api/data-health` reports `benchmark_drift_quality.status=drift_outlier_review`, `source_type=provider_file`, `active_share=0.77853213`.
  - `http://127.0.0.1:13000/`, `/data-health`, `/trading-readiness`, `/paper-trading` returned `200`.

## Guardrails

- 추천 weight 변경 금지.
- benchmark/evaluation split 변경 금지.
- broker submit, live order, kill switch unlock 금지.
- repo 안 secret/env 값 수정 금지.

## Exact Next Step

- exact next step: `portfolio-risk-budget-rebalance-candidate-review` task를 열고, full benchmark drift에서 드러난 `TSLA/MSFT/AAPL` active weight outlier를 주문 없이 검토 가능한 리밸런싱 후보/근거로 정리한다.
