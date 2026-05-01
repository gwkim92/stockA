# Task Contract

## Task

- 이름: portfolio-review-coverage-gate
- 요청: portfolio outcome coverage blind spot을 portfolio review에 연결한다.
- 담당: Codex
- 날짜: 2026-04-27

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `portfolio-review-bootstrap`이 선택적 coverage measurement date를 받아 missing thesis/outcome/weight position을 review item action과 portfolio risk에 반영한다.

## Why

- coverage report가 별도 조회로만 있으면 보유 검토 루틴에서 빠질 수 있다. portfolio review에 coverage gate를 붙이면 "잘 투자하고 있는지"를 점검할 때 attribution/outcome blind spot도 함께 드러난다.

## Scope

- 포함:
  - `portfolio-review-bootstrap` optional coverage measurement date
  - coverage status fields in review candidates
  - deterministic coverage gate action mapping
  - CLI option
  - unit tests
  - Docker verification extension
  - docs/task handoff 갱신
- 제외:
  - DB schema 변경
  - attribution methodology 변경
  - outcome 자동 생성
  - thesis 자동 생성
  - 실거래 주문/체결
  - LLM 기반 action 결정

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/plans/2026-04-27-portfolio-review-coverage-gate.md`
  - `docs/portfolio-review-bootstrap.md`
  - `docs/portfolio-outcome-coverage-report.md`
  - `docs/tasks/portfolio-review-coverage-gate/`
  - `docs/verification-plan.md`
  - `scripts/verify_portfolio_review_bootstrap.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/signal/portfolio_review.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_portfolio_review_bootstrap.py`
- 수정 금지 파일:
  - DB migrations
  - attribution calculation
  - recommendation score formula
  - thesis generation rule
- 검증에 사용할 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n scripts/verify_portfolio_review_bootstrap.sh`
  - `bash scripts/verify_portfolio_review_bootstrap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-review-coverage-gate`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Verification Commands

- `python3 -m compileall src tests`
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- `bash -n scripts/verify_portfolio_review_bootstrap.sh`
- `bash scripts/verify_portfolio_review_bootstrap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-review-coverage-gate`
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - portfolio review coverage gate
  - CLI optional coverage date
  - unit tests
  - Docker verify extension
  - docs and task handoff/review

## Completion Criteria

- [x] 옵션이 없으면 기존 portfolio review 동작이 유지된다.
- [x] 옵션이 있으면 coverage status가 candidate/reason/summary에 포함된다.
- [x] `missing_thesis`가 `needs_thesis_review` action으로 review item에 저장된다.
- [x] `missing_outcome`이 `needs_outcome_review` action으로 분리된다.
- [x] `missing_weight`가 `needs_weight_review` action으로 분리된다.
- [x] Docker verify가 AAPL monitor와 BABA needs thesis review를 함께 확인한다.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Risks

- coverage gate는 remediation을 자동 실행하지 않는다.
- position-linked thesis 기준이라, recommendation에 thesis가 있어도 position snapshot에 thesis가 없으면 missing thesis로 본다.
- coverage measurement date를 잘못 지정하면 아직 도래하지 않은 outcome을 missing으로 표시할 수 있다.
