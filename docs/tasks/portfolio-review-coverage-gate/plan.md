# Plan

- `portfolio-review-bootstrap`에 optional `coverage_measurement_end_date`를 추가한다.
- candidate lookup에서 position-linked thesis 기준 coverage status를 계산한다.
- review action rule에 `needs_outcome_review`, `needs_weight_review`를 추가한다.
- `missing_thesis`는 기존 `needs_thesis_review` action으로 매핑한다.
- CLI `--coverage-measurement-end-date`를 추가한다.
- Docker verify에서 기존 정상 AAPL review와 coverage gap BABA review를 함께 확인한다.
- README, portfolio review docs, verification plan, task handoff/review를 갱신한다.
