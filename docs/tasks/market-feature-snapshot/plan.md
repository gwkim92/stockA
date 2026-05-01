# Task Plan

## 1. Schema

- `signal.feature_definition`을 추가한다.
- `signal.instrument_feature_value`를 추가한다.
- 초기 migration은 instrument features만 운영 경로로 사용한다.

## 2. Runner

- strategy universe batch identity로 universe members를 찾는다.
- 각 instrument의 bounded daily adjusted close history를 읽는다.
- bootstrap deterministic feature set을 계산한다.
- feature별 cross-sectional zscore를 계산한다.
- feature definition과 value rows를 upsert한다.

## 3. CLI

- `market-feature-snapshot` command를 추가한다.
- required: `--as-of-date`, `--strategy-name`, `--horizon-type`, `--universe-version`
- optional: `--market-code`, `--feature-set-version`

## 4. Verification

- unit tests for lookup, computation, upsert, runner success/failure, CLI
- Docker verify for market universe bootstrap -> price backfill -> strategy universe slice -> market feature snapshot

## 5. Handoff

- 이번 deterministic feature path가 AI path와 별개로 recommendation chain을 유지하기 위한 것임을 handoff에 남긴다.
