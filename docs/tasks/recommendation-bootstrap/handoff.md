# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: recommendation-bootstrap
- 담당: Codex
- 날짜: 2026-04-25

## Current Status

- 완료:
  - selected strategy universe와 deterministic evidence를 recommendation batch로 저장하는 경로를 구현했다.
- 막힌 점:
  - 현재 없음.

## Files Touched

- 생성:
  - `docs/plans/2026-04-25-recommendation-bootstrap.md`
  - `docs/recommendation-bootstrap.md`
  - `docs/tasks/recommendation-bootstrap/contract.md`
  - `docs/tasks/recommendation-bootstrap/plan.md`
  - `docs/tasks/recommendation-bootstrap/handoff.md`
  - `docs/tasks/recommendation-bootstrap/review.md`
  - `scripts/verify_recommendation_bootstrap.sh`
  - `src/stockanalysis/signal/recommendation.py`
  - `tests/test_recommendation_bootstrap.py`
- 수정:
  - `README.md`
  - `docs/db-schema-design.md`
  - `docs/cycle-state-snapshot.md`
  - `docs/verification-plan.md`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_ingest_cli.py`

## Decisions

- 결정:
  - AI는 추천 rank를 결정하지 않는다.
  - thesis는 이번 task에서 만들지 않는다.
  - direct internal theme/cycle evidence가 있는 instruments만 recommendation row로 저장한다.
- 이유:
  - 추천은 재현 가능한 deterministic score로 먼저 고정되어야 하고, thesis/review는 그 다음 감사 layer로 붙이는 편이 안전하다.

## Verification Already Run

- `python3 -m compileall src tests`
- `PYTHONPATH=src python3 -m unittest tests.test_recommendation_bootstrap tests.test_ingest_cli -v`
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- `bash -n scripts/verify_recommendation_bootstrap.sh`
- `bash scripts/verify_recommendation_bootstrap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task recommendation-bootstrap`
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Still Unverified

- 항목: 없음
- 왜 중요한가: compile, targeted unit, full unit, Docker integration, harness readiness, placeholder 검색까지 완료했다.

## Exact Next Step

- 다음 세션은 이것부터 시작: deterministic 축은 `thesis-bootstrap` 또는 `recommendation-score-component`, AI 축은 `live OpenAI Responses provider`를 병렬 backlog로 유지한다.

## Risks

- 위험:
  - current taxonomy가 reporting theme bootstrap에 치우쳐 있다.
  - thesis가 아직 없어서 recommendation row의 설명력이 낮다.
  - score component table이 아직 없어 component-level audit은 code/docs에 의존한다.
  - current recommendation은 direct theme/cycle evidence가 있는 instruments만 포함한다.
- 대응:
  - 현재는 conservative recommendation bootstrap으로 제한한다.
  - thesis와 score component는 후속 task로 분리한다.
  - AI path는 explanation/report layer로 병렬 유지한다.
  - broader theme/sector propagation으로 coverage를 확장한다.

## Useful Context

- 파일:
  - `src/stockanalysis/signal/recommendation.py`
  - `src/stockanalysis/signal/cycle.py`
  - `src/stockanalysis/signal/features.py`
  - `src/stockanalysis/signal/theme_enrichment.py`
  - `docs/recommendation-bootstrap.md`
  - `docs/cycle-state-snapshot.md`
- 다시 찾기 싫은 배경지식:
  - current fixture chain에서 `AAPL -> ANNUAL_REPORTING -> forming` cycle snapshot이 1건 생긴다.
  - `signal.recommendation`에는 아직 evidence_json column이 없다.
  - Docker verify는 recommendation batch 1건, AAPL recommendation 1건, bucket `watch`, action `watch`, total score `0.3610`, latest `recommendation_bootstrap` run status `succeeded`를 확인한다.
