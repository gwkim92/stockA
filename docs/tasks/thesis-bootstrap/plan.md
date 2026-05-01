# Plan

- 입력 경계를 `recommendation_batch -> recommendation -> direct theme/cycle evidence`로 고정한다.
- `src/stockanalysis/signal/thesis.py`에 lookup, thesis rendering, upsert/link, runner를 만든다.
- CLI `thesis-bootstrap`을 추가한다.
- unit test와 Docker verify 스크립트로 active thesis 생성과 recommendation link를 증명한다.
- thesis bootstrap 문서와 verification plan, handoff/review를 갱신한다.
