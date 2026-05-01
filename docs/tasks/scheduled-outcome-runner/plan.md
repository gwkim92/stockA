# Plan

- `PerformanceOutcomeScheduleCandidate`와 schedule candidate lookup SQL을 추가한다.
- horizon day resolver를 추가해 default `(30, 90, 180, 365)`와 custom horizon validation을 처리한다.
- `run_performance_outcome_schedule_bootstrap`가 due candidates를 순회하며 기존 `run_performance_outcome_bootstrap`을 호출하게 한다.
- schedule parent `ops.pipeline_run`을 별도 기록한다.
- CLI `performance-outcome-schedule-bootstrap`를 추가한다.
- unit test로 lookup, resolver, runner success/failure/no-op, CLI dispatch를 검증한다.
- Docker verify로 schedule CLI가 2024-11-04, 2024-12-02 outcome을 생성하는지 확인한다.
- README, performance docs, verification plan, task handoff/review를 갱신한다.
