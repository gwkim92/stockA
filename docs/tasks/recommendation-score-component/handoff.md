# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: recommendation-score-component
- 담당: Codex
- 날짜: 2026-04-26

## Current Status

- 완료:
  - recommendation total score를 구성하는 component score와 weight를 DB에 저장한다.
  - `signal.recommendation_score_component` migration, recommendation upsert, unit test, Docker verify, 운영 문서를 추가했다.
- 막힌 점:
  - 아직 없음.

## Files Touched

- 생성:
  - `db/migrations/0008_recommendation_score_component.sql`
  - `docs/plans/2026-04-26-recommendation-score-component.md`
  - `docs/recommendation-score-component.md`
  - `docs/tasks/recommendation-score-component/contract.md`
  - `docs/tasks/recommendation-score-component/plan.md`
  - `docs/tasks/recommendation-score-component/handoff.md`
  - `docs/tasks/recommendation-score-component/review.md`
  - `scripts/verify_recommendation_score_component.sh`
- 수정:
  - `README.md`
  - `docs/db-schema-design.md`
  - `docs/recommendation-bootstrap.md`
  - `docs/verification-plan.md`
  - `src/stockanalysis/signal/recommendation.py`
  - `tests/test_recommendation_bootstrap.py`

## Decisions

- 결정:
  - score formula는 바꾸지 않는다.
  - component score/weight/explanation만 저장한다.
  - component rows는 recommendation child rows로 두고 recommendation 삭제 시 cascade한다.
- 이유:
  - 추천 결과의 감사 가능성을 높이되, scoring behavior 자체의 regression risk는 만들지 않기 위해서다.

## Verification Already Run

- `python3 -m compileall src tests` passed.
- `PYTHONPATH=src python3 -m unittest discover -s tests -v` passed: 155 tests.
- `bash -n scripts/verify_recommendation_score_component.sh` passed.
- `bash scripts/verify_recommendation_score_component.sh` passed with Docker Postgres.

## Still Unverified

- 항목: live broad universe의 score component distribution
- 왜 중요한가: fixture chain은 AAPL 1건 기준 end-to-end를 증명하지만, 대규모 universe에서 점수 분포가 투자 의사결정에 적절한지는 별도 검증이 필요하다.
- 항목: LLM 기반 explanation/report layer
- 왜 중요한가: 이번 작업은 deterministic score audit 저장만 추가했고, AI는 아직 component 설명이나 리포트를 생성하지 않는다.

## Exact Next Step

- 다음 세션은 이것부터 시작: `portfolio-review-bootstrap`로 thesis/recommendation/review 이후의 보유 검토 기록을 만들거나, `live-data score distribution report`로 실제 universe 점수 분포를 검증한다.

## Risks

- 위험:
  - component explanation은 deterministic text라 설명력이 제한적이다.
  - component score는 current feature coverage에 의존한다.
  - live broad universe에서는 component distribution 검증이 아직 없다.
- 대응:
  - LLM explanation/report layer는 후속 task로 분리한다.
  - live-data smoke와 score distribution report를 별도 task로 추가한다.

## Useful Context

- 파일:
  - `src/stockanalysis/signal/recommendation.py`
  - `tests/test_recommendation_bootstrap.py`
  - `docs/recommendation-bootstrap.md`
- 다시 찾기 싫은 배경지식:
  - current fixture chain에서 AAPL recommendation 1건이 `watch`, `total_score = 0.3610`으로 생성된다.
  - component scores는 `cycle_score`, `momentum_score`, `short_term_score`, `rank_score` 네 가지다.
  - AAPL fixture chain은 component row 4건과 weighted sum `0.3610`을 Docker Postgres에서 확인한다.
