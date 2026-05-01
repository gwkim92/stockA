# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: portfolio-review-bootstrap
- 요청: 현재 포지션 스냅샷을 thesis review와 recommendation evidence에 연결해 보유 검토 결과를 저장한다.
- 담당: Codex
- 날짜: 2026-04-26

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `portfolio-review-bootstrap` CLI가 `portfolio.position_snapshot` rows를 읽어 `portfolio.review`와 `portfolio.review_item` rows를 deterministic하게 저장한다.

## Why

- 추천과 thesis review만 있으면 신규 판단은 남지만 실제로 들고 있는 포지션을 계속 보유해도 되는지 검토한 기록이 부족하다. 포트폴리오 검토 결과가 남아야 보유 유지, 모니터링, 축소, 청산 판단과 이후 성과 분석을 연결할 수 있다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/signal/thesis_review.py`
  - `src/stockanalysis/signal/recommendation.py`
  - `src/stockanalysis/ingest/cli.py`
- 관련 schema:
  - `portfolio.portfolio`
  - `portfolio.position_snapshot`
  - `signal.recommendation`
  - `signal.investment_thesis`
  - `signal.thesis_review`
- 이전 결정:
  - 실거래 자동화는 별도 승인 전까지 범위 밖이다.
  - LLM은 추천/보유 action을 직접 결정하지 않는다.
  - 결정 당시 입력 데이터, score, thesis, review 근거를 저장한다.

## Scope

- 포함:
  - `portfolio.review`와 `portfolio.review_item` migration
  - portfolio review candidate lookup
  - deterministic portfolio action rule
  - CLI, tests, Docker verify, docs
- 제외:
  - broker 또는 실거래 연동
  - order/trade 생성
  - portfolio optimizer
  - live portfolio API adapter
  - AI action ranking

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `db/migrations/0009_portfolio_review.sql`
  - `docs/db-schema-design.md`
  - `docs/portfolio-review-bootstrap.md`
  - `docs/plans/2026-04-26-portfolio-review-bootstrap.md`
  - `docs/tasks/portfolio-review-bootstrap/`
  - `docs/verification-plan.md`
  - `scripts/verify_portfolio_review_bootstrap.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/signal/portfolio_review.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_portfolio_review_bootstrap.py`
- 수정 금지 파일:
  - recommendation score formula
  - thesis review action formula unless only reading output
  - live AI provider path
  - broker/trade execution path
  - benchmark 또는 performance schema semantics
- 검증에 사용할 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n scripts/verify_portfolio_review_bootstrap.sh`
  - `bash scripts/verify_portfolio_review_bootstrap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-review-bootstrap`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `db/migrations/0009_portfolio_review.sql`
  - `src/stockanalysis/signal/portfolio_review.py`
  - `scripts/verify_portfolio_review_bootstrap.sh`
  - `docs/portfolio-review-bootstrap.md`
  - `docs/tasks/portfolio-review-bootstrap/contract.md`
  - `docs/tasks/portfolio-review-bootstrap/plan.md`
  - `docs/tasks/portfolio-review-bootstrap/handoff.md`
  - `docs/tasks/portfolio-review-bootstrap/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] `portfolio.review`와 `portfolio.review_item` table이 실제 migration에 존재한다
- [x] `portfolio-review-bootstrap`이 position snapshot을 review item으로 저장한다
- [x] 실거래 자동화가 범위 밖임이 문서화되어 있다

## Verification Plan

- 자동 검증: compileall, unittest, shell syntax, Docker integration verify, harness verify, placeholder 검색
- 수동 검증: `docs/portfolio-review-bootstrap.md`에서 action rule, boundary, next step이 명확한지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: Docker Postgres에서 `portfolio.review` 1건, `portfolio.review_item` 1건, AAPL action `monitor`, latest `portfolio_review_bootstrap` pipeline run status가 `succeeded`다.

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `0009_portfolio_review.sql`, portfolio review runner, CLI command, verify script, docs만 제거하면 이전 thesis review 상태로 복귀한다.

## Open Questions

- 질문: 실제 계좌/브로커 포지션을 바로 연결할지
- 답: 이번 작업은 paper portfolio와 fixture snapshot만 사용한다. live portfolio adapter는 후속 task로 분리한다.

- 질문: portfolio action을 optimizer나 AI가 결정할지
- 답: deterministic rule만 사용하고 AI는 이후 report/explanation layer로 분리한다.
