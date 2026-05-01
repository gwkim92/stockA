# Plan

- 실제 migration에 `signal.recommendation_score_component`를 추가한다.
- 기존 recommendation score formula는 변경하지 않는다.
- `src/stockanalysis/signal/recommendation.py`에서 recommendation row insert와 같은 transaction 안에 component rows를 저장한다.
- unit test로 SQL rendering과 summary component row count를 고정한다.
- Docker verify로 AAPL recommendation 1건과 score component 4건을 확인한다.
- 운영 문서와 verification plan, handoff/review를 갱신한다.
