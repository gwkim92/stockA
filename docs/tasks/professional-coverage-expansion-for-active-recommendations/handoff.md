# Session Handoff

## Current Status

- 완료:
  - task contract를 만들었다.
  - `sec-companyfacts-upsert`가 회사명 매칭 실패 시 요청 symbol fallback을 받을 수 있게 했다.
  - `professional-coverage-expansion-run` operations CLI를 추가했다.
  - active recommendation gap symbols를 읽고 SEC `company_tickers_exchange`로 CIK를 해석한 뒤 companyfacts 수집, financial metric normalization, peer relative, valuation, industry competitive positioning, equity research reporting을 순서대로 실행하도록 만들었다.
  - weekly `sec-filings-weekly` profile에 `professional-coverage-expansion` step을 추가했다.
  - data-health cadence registry에 `professional-coverage-expansion-weekly` job을 추가했다.
  - 한 issuer의 SEC companyfacts 실패가 전체 batch를 중단하지 않도록 부분 실패 허용으로 보강했다.
  - GOOG/GOOGL 같은 복수 share class 오염을 막기 위해 explicit fallback symbol이 있으면 회사명보다 symbol lookup을 우선하도록 수정했다.
  - EC2에서 active recommendation complete professional coverage를 `4/36`에서 `30/36`으로 올렸고, `recommendation-quality-eval-run`의 coverage guardrail을 `sufficient_coverage`로 통과시켰다.
  - EC2에서 가격 기반 outcome backfill을 실행해 recommendation outcome `55`개와 thesis outcome `43`개를 생성했다.
  - EC2 quality eval은 outcome sample과 professional coverage 기준을 모두 통과해 `ready_for_weight_review`가 됐다.
- 진행 중:
  - 없음.
- 직전 guardrail 결과 기준 EC2 active recommendation complete professional coverage는 `30/36 = 0.833333`이고, outcome count는 `30`이다.

## Decisions

- coverage 확장은 무료 공개 SEC 데이터와 기존 Postgres canonical tables만 사용한다.
- SEC companyfacts는 active recommendation symbol을 SEC ticker mapping으로 CIK 해석한 뒤 수집한다.
- companyfacts entity name matching이 실패하면 요청 symbol fallback을 사용한다.
- equity research artifact는 같은 runner에서 선택적으로 생성하되, 추천 weight는 계속 0으로 유지한다.
- `ready_for_weight_review`는 자동 weight 변경 허가가 아니다. 별도 review task에서 component spread, 표본 편향, paper validation conflict를 검토해야 한다.
- ARM, EROK, SPY는 SEC companyfacts 기반 재무 coverage가 구조적으로 제한된다. ARM은 현재 supported facts가 없고, EROK은 `facts.us-gaap`가 없으며, SPY는 ETF라 companyfacts endpoint가 404다.

## Next Step

- exact next step: `recommendation-weight-review-readiness-audit` task를 열어 `eval_run_id=11`의 component spread와 표본 품질을 검토한다. 단, paper validation latest status가 `failed`이고 conflict count가 `3`이므로 weight 변경 전 `paper-validation-conflict-remediation`도 함께 확인해야 한다.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_sec_companyfacts tests.test_professional_coverage_expansion tests.test_data_operations_cli tests.test_operating_data_orchestrator`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_ingest_cli tests.test_data_operations_cadence tests.test_sec_companyfacts tests.test_professional_coverage_expansion tests.test_data_operations_cli tests.test_operating_data_orchestrator`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m stockanalysis.operations.cli professional-coverage-expansion-run --help`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- Passed: `git diff --check`
- Passed: `bash scripts/verify_project_execution_roadmap.sh`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task professional-coverage-expansion-for-active-recommendations`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests` (`892` tests)
- Note: bare `/opt/homebrew/bin/python3.13 -m unittest discover -s tests` failed because that interpreter does not have `fastapi` installed; the verify venv has FastAPI/Uvicorn/psycopg/httpx and passed the full suite.
- Passed on EC2: pulled commit `68d1f3b`.
- Passed on EC2: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_sec_companyfacts tests.test_professional_coverage_expansion tests.test_data_operations_cli tests.test_operating_data_orchestrator`
- Passed on EC2 dry-run: `professional-coverage-expansion-run --limit 10 --companyfacts-limit 3 --research-limit 3 --research-provider fixture --dry-run`
  - candidate symbols: `ADI`, `AEIS`, `ALAB`, `ARM`, `DIS`, `ELF`, `EROK`, `FANG`, `GILD`, `GOOG`
  - resolved targets: `10/10`
- Passed on EC2 execute: `professional-coverage-expansion-run --limit 10 --companyfacts-limit 2 --research-limit 3 --research-provider fixture --execute`
  - parent `run_id=824`
  - SEC companyfacts: `ADI run_id=825 fact_count=1295`, `AEIS run_id=826 fact_count=1451`
  - downstream: financial metric normalization `run_id=827`, peer relative `run_id=828`, valuation `run_id=829`, industry competitive positioning `run_id=830`, equity research reporting `run_id=831`, failed artifact count `0`
- Passed on EC2: services restarted and active: `stockanalysis-frontend-api.service`, `stockanalysis-web.service`.
- Passed on EC2: `/api/data-health` shows `professional-coverage-expansion-weekly` as `ok/succeeded`, latest `pipeline-run-824`.
- Passed on EC2: `recommendation-quality-eval-run --execute` returned `eval_run_id=9`; complete professional coverage improved from `4/36 = 0.111111` to `9/36 = 0.25`. It still remains `insufficient_coverage`, so recommendation weight review remains blocked.
- Passed local after failure-resilience fix: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_professional_coverage_expansion tests.test_data_operations_cli tests.test_operating_data_orchestrator tests.test_sec_companyfacts`
- Passed local after explicit ticker fix: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_sec_companyfacts tests.test_professional_coverage_expansion tests.test_data_operations_cli tests.test_operating_data_orchestrator`
- Passed local after both fixes: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`, `git diff --check`, AWH verify.
- Passed on EC2: pulled commit `6c0b582`; `tests.test_professional_coverage_expansion` passed.
- Passed on EC2: `professional-coverage-expansion-run --limit 20 --companyfacts-limit 5 --research-limit 5 --research-provider fixture --execute`
  - parent `run_id=835`
  - success: `ALAB run_id=836`, `DIS run_id=837`, `ELF run_id=838`
  - failed but non-blocking: `ARM`, `EROK`
  - downstream runs: financial `839`, peer `840`, valuation `841`, industry `842`, research `843`
- Passed on EC2: pulled commit `8730763`; `tests.test_sec_companyfacts tests.test_professional_coverage_expansion` passed.
- Passed on EC2: `professional-coverage-expansion-run --limit 20 --companyfacts-limit 10 --research-limit 10 --research-provider fixture --execute`
  - parent `run_id=844`
  - success: `FANG 845`, `GILD 846`, `GOOG initially resolved to GOOGL before the explicit ticker fix`, `INTU 848`, `LDOS 849`, `LLY 850`, `MSFT 851`, `QUBT 852`
  - failed but non-blocking: `ARM`, `EROK`
  - downstream runs: financial `853`, peer `854`, valuation `855`, industry `856`, research `857`
- Passed on EC2 after explicit ticker fix: `professional-coverage-expansion-run --limit 20 --companyfacts-limit 7 --research-limit 7 --research-provider fixture --execute`
  - parent `run_id=858`
  - success: `GOOG run_id=859` now correctly wrote to `instrument_symbol=GOOG`, plus `TGT 860`, `TSLA 861`, `XOM 862`
  - failed but non-blocking: `ARM`, `EROK`, `SPY`
  - downstream runs: financial `863`, peer `864`, valuation `865`, industry `866`, research `867`
- Passed on EC2: `/api/data-health` shows `professional-coverage-expansion-weekly`, `performance_outcome_schedule_bootstrap`, and `recommendation_quality_eval` as `ok/succeeded`.
- Passed on EC2: `recommendation-outcome-backfill-run --due-on-date 2026-05-25 --horizon-day 1 --horizon-day 3 --horizon-day 5 --limit 10 --execute`
  - parent `run_id=869`
  - succeeded candidates `5/5`
  - recommendation outcomes `55`
  - thesis outcomes `43`
  - labels: outperform `6`, underperform `8`, inline `29`, flat `12`
- Passed on EC2: `recommendation-quality-eval-run --execute` returned `run_id=875`, `eval_run_id=11`
  - `quality_status=ready_for_weight_review`
  - `sample_status=sufficient_sample`
  - `outcome_count=30`
  - complete professional coverage `30/36 = 0.833333`
  - fundamental/cycle protected weights remain `0`

## Residual Risk

- SEC companyfacts가 없는 ETF, ADR, 신규상장/비상장성 ticker는 자동 coverage가 제한될 수 있다. 현재 known gaps는 `ARM`, `EROK`, `SPY`다.
- Codex OAuth 기반 equity research는 runtime token 상태에 의존하므로 fixture provider fallback과 별도 smoke가 필요하다.
- outcome sample은 충분 기준은 넘었지만 단기 1/3/5일 표본이므로 중장기 투자 weight 변경 근거로는 약하다.
- paper validation latest status가 `failed`이고 conflict count가 `3`이다. weight 변경이나 paper action 확대 전에 conflict 원인을 해소해야 한다.
