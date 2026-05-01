# Task Plan

## 1. Lookup

- strategy universe batch identity로 selected instruments를 찾는다.
- selected instruments와 `event.event_instrument_impact`, `event.event_classification_impact`를 조인한다.
- internal theme taxonomy nodes만 대상으로 한다.

## 2. Aggregation

- instrument-node 기준 supporting event count
- first event date
- latest event date
- max combined confidence
- latest source document id

## 3. Write Path

- selected universe instruments의 기존 `derived_theme` internal memberships를 교체한다.
- 새 candidate rows를 `ref.instrument_classification_membership`에 insert한다.

## 4. CLI

- `instrument-theme-enrichment`
- required: `--as-of-date`, `--strategy-name`, `--horizon-type`, `--universe-version`
- optional: `--market-code`

## 5. Verification

- unit tests for lookup, replace SQL, runner success/failure, CLI
- Docker verify chaining market universe, price backfill, strategy universe, SEC event impacts, instrument theme enrichment

## 6. Handoff

- next step을 `cycle-state-snapshot`으로 연결하고 AI live provider backlog를 계속 남긴다.
