# Plan

- 입력 경계를 `strategy_universe -> instrument_theme_enrichment -> market_feature_snapshot -> recent event heat`로 고정한다.
- `src/stockanalysis/signal/cycle.py`에 lookup, scoring, upsert, runner를 만든다.
- CLI `cycle-state-snapshot`을 추가한다.
- unit test와 Docker verify 스크립트로 runner와 DB write를 증명한다.
- cycle state 문서와 verification plan, handoff/review를 갱신한다.
