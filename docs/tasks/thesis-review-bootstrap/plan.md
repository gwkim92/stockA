# Plan

- 실제 migration에 `signal.thesis_review`를 추가한다.
- 입력 경계를 `recommendation_batch -> active recommendation -> linked active thesis -> current cycle/features`로 고정한다.
- `src/stockanalysis/signal/thesis_review.py`에 lookup, review rendering, upsert, runner를 만든다.
- CLI `thesis-review-bootstrap`을 추가한다.
- unit test와 Docker verify 스크립트로 review row 생성과 pipeline run 성공을 증명한다.
- thesis review bootstrap 문서와 verification plan, handoff/review를 갱신한다.
