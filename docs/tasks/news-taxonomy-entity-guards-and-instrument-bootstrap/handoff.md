# Session Handoff

## Current Status

- 진행 중: 로컬 구현과 단위 검증 완료. EC2 smoke와 배포 검증 전 단계.
- 기준일: 2026-05-22

## Investigation

- 기존 rule enrichment는 `_SYMBOL_KEYWORDS`에 `XOM` 직접 키워드로 `oil prices`, `crude oil`을 포함해 유가 일반 뉴스가 Exxon 직접 종목 뉴스로 오탐될 위험이 있었다.
- `detect_instrument_symbol()`은 명시적 티커 패턴을 일반적으로 감지하지 않아 DB에 없는 신규 종목을 안전하게 후보화하기 어렵다.
- 이미 SEC company_tickers_exchange 기반 `market_universe_bootstrap`이 있으므로 새 종목 생성은 placeholder가 아니라 SEC 검증 후 canonical instrument bootstrap으로 가야 한다.

## Implemented

- 일반 `oil prices`, `crude oil` 문구는 더 이상 `XOM` 직접 종목으로 연결하지 않는다. `XOM`은 `exxon`, `exxon mobil`, `xom`처럼 회사/티커가 직접 언급될 때만 연결한다.
- `AI_LABOR_PRODUCTIVITY` subtheme을 추가해 AI가 고용, 노동, 자동화, 생산성에 미치는 뉴스가 AI 반도체 사이클로 과잉 분류되지 않게 했다.
- 명시 티커 감지를 추가했다: `$ALAB`, `(ALAB)`, `ALAB stock` 형태만 보수적으로 후보화하고 `AI`, `CEO`, `SEC`, `ETF` 같은 일반 대문자 약어는 차단한다.
- `run_news_missing_instrument_bootstrap()`을 추가했다. pending RSS news에서 감지된 missing ticker를 SEC `company_tickers_exchange` universe와 대조하고, Nasdaq/NYSE에서 검증된 symbol만 `ref.instrument`에 bootstrap한다.
- `stockanalysis-operations news-missing-instrument-bootstrap-run` CLI를 추가했다.
- `news-intraday` 자동 프로파일 순서를 `RSS 수집 -> 누락 티커 SEC bootstrap -> rule enrichment -> cluster evidence -> Codex OAuth AI evidence -> macro propagation`으로 보강했다.
- EC2 smoke 중 `news-rss-enrich-run --limit 100`이 FOMC 같은 거시 뉴스에서도 `ref.instrument` 회사명 alias lookup을 수행해 느려지는 병목을 발견했다. 회사명 alias lookup은 `stock`, `shares`, `earnings`, `revenue`, `upgrade`, `downgrade`, `price target` 같은 종목형 문맥이 있을 때만 수행하도록 가드했다.

## Verification

- 통과: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_enrichment tests.test_data_operations_cli tests.test_operating_data_orchestrator tests.test_data_operations_cadence -v`
- 통과: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`

## Exact Next Step

- exact next step: commit/push alias lookup guard, deploy to EC2, re-run `news-rss-enrich-run --limit 100`, then complete EC2 task smoke.
