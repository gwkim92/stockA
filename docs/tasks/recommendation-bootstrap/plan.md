# Plan

- 입력 경계를 `strategy_universe -> market_feature_snapshot -> instrument_theme_enrichment -> cycle_state_snapshot`으로 고정한다.
- `src/stockanalysis/signal/recommendation.py`에 lookup, scoring, upsert, runner를 만든다.
- CLI `recommendation-bootstrap`을 추가한다.
- unit test와 Docker verify 스크립트로 runner와 DB write를 증명한다.
- recommendation bootstrap 문서와 verification plan, handoff/review를 갱신한다.
