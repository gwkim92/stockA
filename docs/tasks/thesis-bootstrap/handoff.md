# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: thesis-bootstrap
- 담당: Codex
- 날짜: 2026-04-26

## Current Status

- 완료:
  - active recommendation rows에 deterministic investment thesis를 생성 또는 갱신해 연결했다.
  - `signal.recommendation.thesis_id` link를 Docker Postgres에서 검증했다.
- 막힌 점:
  - 아직 없음.

## Files Touched

- 생성:
  - `docs/plans/2026-04-26-thesis-bootstrap.md`
  - `docs/thesis-bootstrap.md`
  - `docs/tasks/thesis-bootstrap/contract.md`
  - `docs/tasks/thesis-bootstrap/plan.md`
  - `docs/tasks/thesis-bootstrap/handoff.md`
  - `docs/tasks/thesis-bootstrap/review.md`
  - `scripts/verify_thesis_bootstrap.sh`
  - `src/stockanalysis/signal/thesis.py`
  - `tests/test_thesis_bootstrap.py`
- 수정:
  - `README.md`
  - `docs/db-schema-design.md`
  - `docs/recommendation-bootstrap.md`
  - `docs/verification-plan.md`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_ingest_cli.py`

## Decisions

- 결정:
  - deterministic thesis template만 먼저 사용한다.
  - same instrument/node/thesis_type active thesis는 갱신하고, 없으면 생성한다.
  - AI-generated thesis prose는 후속 task로 둔다.
- 이유:
  - recommendation을 즉시 감사 가능한 thesis와 연결하되, LLM 품질/비용/평가 문제를 recommendation chain의 필수 경로로 만들지 않기 위해서다.

## Verification Already Run

- `python3 -m compileall src tests`
- `PYTHONPATH=src python3 -m unittest tests.test_thesis_bootstrap tests.test_ingest_cli -v`
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- `bash -n scripts/verify_thesis_bootstrap.sh`
- `bash scripts/verify_thesis_bootstrap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task thesis-bootstrap`
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Still Unverified

- 항목: live market data와 다수 recommendation batch에서 coverage와 template 품질
- 왜 중요한가: 현재 검증은 fixture AAPL 1건 기준이고, broad universe에서 thesis template과 direct theme coverage가 충분한지는 별도 검증이 필요하다.

## Exact Next Step

- 다음 세션은 이것부터 시작: deterministic 축은 `thesis-review-bootstrap` 또는 `recommendation-score-component`, AI 축은 `live OpenAI Responses provider`를 병렬 backlog로 유지한다.

## Risks

- 위험:
  - deterministic template는 설명력이 제한적이다.
  - thesis factor/review table이 아직 없다.
  - current recommendation coverage가 direct theme/cycle evidence에 의존한다.
- 대응:
  - LLM explanation/report layer는 후속 task로 분리한다.
  - factor/review는 별도 migration 또는 bootstrap task로 확장한다.
  - broader theme/sector propagation으로 coverage를 넓힌다.

## Useful Context

- 파일:
  - `src/stockanalysis/signal/recommendation.py`
  - `src/stockanalysis/signal/cycle.py`
  - `docs/recommendation-bootstrap.md`
  - `docs/cycle-state-snapshot.md`
- 다시 찾기 싫은 배경지식:
  - current fixture chain에서 AAPL recommendation 1건이 `watch`, `total_score = 0.3610`으로 생성된다.
  - `signal.investment_thesis`에는 `evidence_json` column이 없으므로 structured evidence는 text fields와 source run link 중심으로 남긴다.
