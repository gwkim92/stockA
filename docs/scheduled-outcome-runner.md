# Scheduled Outcome Runner

이 문서는 recommendation batch의 장기 outcome 측정을 자동으로 찾아 실행하는 schedule runner 경로를 고정한다.

## Purpose

`performance-outcome-schedule-bootstrap`은 due date와 horizon days를 기준으로 아직 outcome이 없는 recommendation batch/horizon 조합을 찾고, 기존 `performance-outcome-bootstrap` 계산을 실행한다.

이 단계는 OS cron 또는 외부 automation을 만들지 않는다. 역할은 "어떤 outcome이 지금 실행되어야 하는가"를 deterministic하게 찾고 실행하는 repo-local runner다.

## Candidate Rule

후보는 아래 조건을 모두 만족해야 한다.

- `signal.recommendation_batch.as_of_date + horizon_day <= due_on_date`
- `signal.recommendation_batch.universe_version is not null`
- active recommendation이 1개 이상 있다.
- 해당 horizon의 `performance.recommendation_outcome`이 active recommendation 수보다 적다.

즉 이미 모든 active recommendation outcome이 있는 batch/horizon은 다시 후보로 잡지 않는다.

## Horizons

기본 horizon days:

- 30
- 90
- 180
- 365

CLI에서 `--horizon-day`를 반복 지정하면 custom horizon을 사용한다. horizon day는 calendar day 기준이며, 실제 거래일 보정은 기존 price lookup의 latest-on-or-before rule이 처리한다.

## CLI

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli performance-outcome-schedule-bootstrap \
  --due-on-date 2024-12-02 \
  --horizon-day 3 \
  --horizon-day 31 \
  --market-code US \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --outcome-version bootstrap-v1
```

옵션:

- `--due-on-date`: due horizon 기준일
- `--horizon-day`: 반복 가능. 생략하면 30/90/180/365
- `--market-code`, `--strategy-name`, `--horizon-type`, `--universe-version`: optional batch filter
- `--limit`: 최대 candidate 수
- `--outcome-version`: child outcome runner config metadata

## Pipeline Runs

- parent run: `performance_outcome_schedule_bootstrap`
- child run: 각 candidate마다 기존 `performance_outcome_bootstrap`

candidate 중 하나라도 실패하면 parent run은 `failed`로 기록하고, CLI는 exit code 1을 반환한다. 성공한 candidate 결과는 유지된다.

## Verification

```bash
bash scripts/verify_scheduled_outcome_runner.sh
```

검증은 Docker Postgres에서 migration/seed를 적용하고, recommendation/thesis/price fixture 준비 후 schedule CLI가 AAPL outcome 2건을 생성하는지 확인한다.

기대값:

- `performance.recommendation_outcome` 2건
- `performance.thesis_outcome` 2건
- 2024-11-04 AAPL alpha `0.005000`
- 2024-12-02 AAPL alpha `0.060000`
- child `performance_outcome_bootstrap` succeeded run 2건과 outcome source link
- parent `performance_outcome_schedule_bootstrap` latest status `succeeded`

## Boundaries

- 가격 데이터 backfill을 자동 실행하지 않는다.
- 실제 cron/heartbeat automation은 만들지 않는다.
- recommendation score, thesis generation, portfolio attribution은 수정하지 않는다.
- price가 없어서 outcome 계산이 불가능한 후보는 failed candidate로 summary에 남긴다.

## Next Steps

- 실제 automation을 붙일 때는 이 CLI를 cron/heartbeat에서 호출한다.
- 90/180/365일 fixture 또는 실제 price history 기반 integration test를 추가한다.
- failed candidate retry/report를 별도 운영 리포트로 만든다.
