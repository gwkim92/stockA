# Thesis Bootstrap

이 문서는 active recommendation rows를 deterministic investment thesis와 연결하는 첫 경로를 설명한다.

## Goal

- source:
  - `signal.recommendation_batch`
  - `signal.recommendation`
  - `ref.instrument_classification_membership`
  - `signal.cycle_state_snapshot`
  - `signal.instrument_feature_value`
- target:
  - `signal.investment_thesis`
  - `signal.recommendation.thesis_id`

이 단계의 목적은 recommendation row가 왜 생성됐는지, 어떤 조건에서 무효화되는지, 어떤 holding horizon으로 검토해야 하는지를 저장하는 것이다.

## CLI

```bash
STOCKANALYSIS_PSQL_COMMAND="psql -U postgres -d stockanalysis" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli thesis-bootstrap \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --thesis-version bootstrap-v1
```

## Current Input Rule

현재 bootstrap은 recommendation 이후의 감사 가능한 설명 layer다.

- selected recommendation batch 기준
- `status = active` recommendation만 대상
- `internal_theme` taxonomy만 대상
- `derived_theme` membership만 대상
- matching `cycle_state_snapshot`이 있는 instrument-node evidence만 대상
- recommendation별 cycle score가 가장 높은 node 1개를 primary thesis node로 사용
- 같은 `instrument_id`, `primary_node_id`, `thesis_type`의 active thesis가 있으면 갱신하고 없으면 생성
- 생성 또는 갱신한 thesis를 `signal.recommendation.thesis_id`에 연결

## Thesis Template

현재 thesis prose는 LLM이 작성하지 않는다. 비용, 재현성, 평가 기준이 준비되기 전까지는 deterministic template만 사용한다.

예시 title:

```text
AAPL watch thesis via Annual Reporting
```

예시 summary:

```text
AAPL is an active watch recommendation linked to Annual Reporting. Cycle state is forming; recommendation score is 0.3610.
```

기본 invalidation rule:

```text
Invalidate if recommendation score falls below 0.3500, cycle state weakens to correcting or structurally_broken, or direct theme evidence is removed.
```

## Holding Horizon

- `horizon_type`에 `long`이 포함되면 `expected_holding_days = 365`
- `horizon_type`에 `medium`이 포함되면 `expected_holding_days = 180`
- 그 외는 초기 기본값 `180`

미국 시장(`US`)은 현재 benchmark code를 `SPY`로 둔다.

## Boundary

- AI는 아직 thesis prose를 생성하지 않는다.
- recommendation rank, score, bucket, action은 변경하지 않는다.
- thesis factor table과 review scheduler는 아직 범위 밖이다.
- portfolio execution 또는 실거래는 범위 밖이다.

## Verification

- `bash /Users/woody/ai/stockanalysis/scripts/verify_thesis_bootstrap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task thesis-bootstrap`

현재 Docker verify는 아래를 이어 실행한다.

```text
market-universe-bootstrap
-> market-price-universe-backfill
-> strategy-universe-slice
-> market-feature-snapshot
-> sec-filings-upsert
-> sec-filing-raw-fetch
-> sec-filings-event-extract
-> event-classification-impact-bootstrap
-> event-instrument-impact-bootstrap
-> instrument-theme-enrichment
-> cycle-state-snapshot
-> recommendation-bootstrap
-> thesis-bootstrap
```

그리고 active thesis 1건, AAPL recommendation의 non-null `thesis_id`, title `AAPL watch thesis via Annual Reporting`, conviction score `0.3610`, latest `thesis_bootstrap` pipeline run status 성공을 확인한다.

## Next Step

1. `recommendation-score-component`
2. `portfolio-review-bootstrap`
3. `live OpenAI Responses provider`
