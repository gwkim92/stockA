# Plan

- `resolve_performance_measurement_dates`로 explicit date와 horizon day를 하나의 정렬된 measurement date tuple로 만든다.
- `run_performance_outcome_batch_bootstrap`으로 기존 단일 outcome runner를 여러 measurement date에 대해 순차 실행한다.
- CLI `performance-outcome-batch-bootstrap`를 추가한다.
- AAPL/SPY outcome fixture에 2024-12-02 price를 추가한다.
- Docker verify를 batch CLI 기반으로 바꾸고 outcome 2건, short/long alpha를 검증한다.
- performance docs, verification plan, task handoff/review를 갱신한다.
