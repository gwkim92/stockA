# Plan

- `src/stockanalysis/performance/coverage.py`에 read-only coverage lookup과 summary builder를 추가한다.
- coverage status는 `covered`, `missing_outcome`, `missing_thesis`, `missing_weight`로 구분한다.
- CLI `portfolio-outcome-coverage-report`를 추가한다.
- unit test로 SQL shape, JSON parsing, summary ratios, CLI dispatch를 검증한다.
- AAPL covered + BABA missing thesis fixture를 추가한다.
- Docker verify로 실제 pipeline 이후 coverage count/weight/cash를 확인한다.
- README, attribution docs, verification plan, task handoff/review를 갱신한다.
