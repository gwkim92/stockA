# Plan

- `performance.attribution_run`, `performance.attribution_component` migration을 추가한다.
- portfolio snapshot과 thesis outcome을 연결하는 candidate lookup SQL을 작성한다.
- `position_weighted_alpha_v1` builder를 구현해 security selection, theme exposure, cash timing component를 만든다.
- CLI `portfolio-attribution-bootstrap`를 추가한다.
- unit test로 lookup SQL, component 계산, upsert SQL, runner pipeline 상태, CLI dispatch를 검증한다.
- Docker verify script로 전체 pipeline 이후 attribution row와 contribution bps를 확인한다.
- README, schema docs, verification plan, task handoff/review를 갱신한다.
