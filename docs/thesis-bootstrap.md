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
AAPL 투자 논리 초안: long_term_core 전략에서 추천은 watch 버킷의 watch, 점수 0.3610, 순위 1위다. 핵심 테마는 Annual Reporting (ANNUAL_REPORTING)이고 사이클 상태는 forming, 사이클 점수는 0.2075이다. 가격 맥락은 최신 수정종가 222.9100, 1일 수익률 -1.33%, 관측 구간 수익률 -1.33%다. 벤치마크는 SPY, 예상 보유·검토 기간은 365일이다.
```

예시 entry condition:

```text
유지 조건: 추천이 active 상태이고, 선택 유니버스 편입이 유지되며, Annual Reporting 직접 테마 근거가 연결되어 있어야 한다. 사이클 상태는 forming 상태를 유지하거나 개선되어야 하고, 가격 맥락은 현재 1일 수익률 -1.33%와 관측 구간 수익률 -1.33%보다 뚜렷하게 약해지지 않아야 한다.
```

기본 invalidation rule:

```text
무효화 조건: recommendation score falls below 0.3500, cycle state가 correcting 또는 structurally_broken으로 약화되거나, 직접 테마 근거가 제거되거나, 최신 수정종가가 unavailable 상태가 되거나, 관측 구간 수익률이 -11.33% 아래로 악화되면 thesis를 재검토한다.
```

예시 exit condition:

```text
조치 조건: 검토 중 무효화 조건이 발동되면 비중 축소 또는 청산을 검토한다. 벤치마크 SPY 커버리지, 원천 이벤트 근거, 가격 feature provenance가 누락되면 사람 검토로 승격한다.
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
