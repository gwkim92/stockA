# Review

## Review Notes

- `portfolio-review-bootstrap`에 optional `--coverage-measurement-end-date`를 추가했다.
- 옵션이 없으면 candidate coverage status는 `not_requested`이며 기존 review action은 유지된다.
- 옵션이 있으면 position-linked thesis 기준으로 `performance.thesis_outcome`을 left join한다.
- coverage gate action mapping:
  - `missing_thesis` -> `needs_thesis_review`
  - `missing_outcome` -> `needs_outcome_review`
  - `missing_weight` -> `needs_weight_review`
- DB schema, attribution calculation, recommendation score, thesis generation rule은 변경하지 않았다.

## Verification Evidence

- `PYTHONPATH=src python3 -m unittest tests.test_portfolio_review_bootstrap tests.test_ingest_cli -v`: 46 tests 통과
- `python3 -m compileall src tests`: 통과
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`: 217 tests 통과
- `bash -n scripts/verify_portfolio_review_bootstrap.sh`: 통과
- `bash scripts/verify_portfolio_review_bootstrap.sh`: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-review-coverage-gate`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음

## Remaining Review Items

- 실제 운영 스케줄러 또는 dashboard 연결은 후속 task다.
