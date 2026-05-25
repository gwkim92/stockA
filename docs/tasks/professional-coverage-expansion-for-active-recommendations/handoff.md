# Session Handoff

## Current Status

- 완료:
  - task contract를 만들었다.
  - `sec-companyfacts-upsert`가 회사명 매칭 실패 시 요청 symbol fallback을 받을 수 있게 했다.
  - `professional-coverage-expansion-run` operations CLI를 추가했다.
  - active recommendation gap symbols를 읽고 SEC `company_tickers_exchange`로 CIK를 해석한 뒤 companyfacts 수집, financial metric normalization, peer relative, valuation, industry competitive positioning, equity research reporting을 순서대로 실행하도록 만들었다.
  - weekly `sec-filings-weekly` profile에 `professional-coverage-expansion` step을 추가했다.
  - data-health cadence registry에 `professional-coverage-expansion-weekly` job을 추가했다.
- 진행 중:
  - EC2 배포와 실제 운영 DB smoke.
- 직전 guardrail 결과 기준 EC2 active recommendation complete professional coverage는 `4/36`이었다.

## Decisions

- coverage 확장은 무료 공개 SEC 데이터와 기존 Postgres canonical tables만 사용한다.
- SEC companyfacts는 active recommendation symbol을 SEC ticker mapping으로 CIK 해석한 뒤 수집한다.
- companyfacts entity name matching이 실패하면 요청 symbol fallback을 사용한다.
- equity research artifact는 같은 runner에서 선택적으로 생성하되, 추천 weight는 계속 0으로 유지한다.

## Next Step

- exact next step: local compile/AWH 검증 후 EC2에 배포하고, 운영 DB에서 dry-run/execute smoke를 수행한다. smoke 후 `recommendation-quality-eval-run`을 재실행해 professional coverage가 개선됐는지 확인한다.

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

## Residual Risk

- SEC companyfacts가 없는 ETF, ADR, 신규상장/비상장성 ticker는 자동 coverage가 제한될 수 있다.
- Codex OAuth 기반 equity research는 runtime token 상태에 의존하므로 fixture provider fallback과 별도 smoke가 필요하다.
