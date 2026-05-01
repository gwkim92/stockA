# Portfolio Attribution Bootstrap

이 문서는 보유 portfolio snapshot의 장기 성과 원인을 저장하는 첫 attribution 경로를 고정한다.

## Purpose

`portfolio-attribution-bootstrap`은 portfolio position snapshot과 `performance.thesis_outcome`을 연결해 `performance.attribution_run`, `performance.attribution_component`에 설명 가능한 attribution row를 저장한다.

이 단계는 추천, thesis, portfolio review 판단을 바꾸지 않는다. 역할은 사후 설명이다. 즉, 현재 보유가 어떤 종목과 테마 노출 때문에 성과를 냈는지 기록해 보유 검토와 성과 분석의 입력으로 사용한다.

## Methodology

초기 방법론은 `position_weighted_alpha_v1`이다.

- security selection: `position.weight * alpha_pct * 10000`
- benchmark alpha가 없으면 fallback으로 `position.weight * absolute_return_pct * 10000`
- theme exposure: thesis `primary_node_id`의 classification node별 security contribution 합산
- cash timing: `1 - sum(position.weight)`를 cash weight로 저장하고 contribution은 `0.0000` bps로 둔다.

모든 return 값은 소수점 6자리, weight는 소수점 4자리, contribution bps는 소수점 4자리로 quantize한다.

## Inputs

- portfolio identity: `portfolio_name`
- snapshot identity: `snapshot_date`
- outcome identity: `measurement_end_date`
- source tables:
  - `portfolio.portfolio`
  - `portfolio.position_snapshot`
  - `signal.investment_thesis`
  - `ref.classification_node`
  - `performance.thesis_outcome`

## Output Components

- `security_selection`: 종목별 weight-adjusted alpha contribution
- `theme_exposure`: thesis primary theme별 contribution 집계
- `cash_timing`: 미투자 현금 weight 표시

component를 단순 합산하면 중복 해석될 수 있다. `security_selection`과 `theme_exposure`는 같은 position contribution을 서로 다른 관점으로 표현한다.

## CLI

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-attribution-bootstrap \
  --portfolio-name "Long Term Paper" \
  --snapshot-date 2024-11-01 \
  --measurement-end-date 2024-12-02 \
  --methodology position_weighted_alpha_v1
```

## Verification

```bash
bash scripts/verify_portfolio_attribution_bootstrap.sh
```

검증은 Docker Postgres에서 migration/seed를 적용하고, universe/price/event/theme/recommendation/thesis/outcome/position pipeline을 실행한 뒤 attribution row를 확인한다.

기대값:

- `performance.attribution_run` 1건
- `performance.attribution_component` 3건
- AAPL `security_selection` contribution `30.0000` bps
- `ANNUAL_REPORTING` `theme_exposure` contribution `30.0000` bps
- `CASH` `cash_timing` weight `0.9500`, contribution `0.0000` bps
- latest `portfolio_attribution_bootstrap` pipeline run status `succeeded`

## Boundaries

- 실거래 PnL은 계산하지 않는다.
- Brinson-Fachler full decomposition은 아직 아니다.
- macro/cycle attribution은 자동 분해하지 않는다.
- LLM은 attribution 계산에 사용하지 않는다. 이후 report generation에서만 계산 결과를 설명할 수 있다.
- 현재 fixture는 31일 horizon 검증이다. 실제 중장기/장기 검증은 더 긴 가격 history가 붙은 뒤 확장한다.
- attribution 대상에서 제외되는 missing thesis/outcome/weight position은 `docs/portfolio-outcome-coverage-report.md`의 read-only report로 별도 확인한다.

## Next Steps

- scheduled outcome runner와 coverage report를 운영 루틴으로 연결해 missing outcome을 줄인다.
- portfolio review에 attribution coverage gate를 추가한다.
- macro/cycle attribution은 theme/cycle state snapshot과 연결되는 별도 component로 확장한다.
