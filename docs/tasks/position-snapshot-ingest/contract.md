# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: position-snapshot-ingest
- 요청: paper/live 연동 전 단계로 표준 CSV position snapshot을 canonical portfolio tables에 업서트한다.
- 담당: Codex
- 날짜: 2026-04-26

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `portfolio-position-snapshot-upsert` CLI가 CSV position snapshot을 읽어 `portfolio.portfolio`와 `portfolio.position_snapshot` rows를 저장한다.

## Why

- portfolio review가 동작하려면 보유 position snapshot이 필요하다. 지금까지 verify script는 SQL로 position을 직접 넣었기 때문에 운영 흐름상 수집기가 비어 있었다. CSV upsert를 먼저 만들면 broker adapter 전에도 재현 가능한 paper portfolio snapshot을 적재할 수 있다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/signal/portfolio_review.py`
  - `src/stockanalysis/ingest/market/price.py`
- 관련 schema:
  - `portfolio.portfolio`
  - `portfolio.position_snapshot`
  - `ref.instrument`
  - `signal.investment_thesis`
- 이전 결정:
  - 실거래 자동화는 별도 승인 전까지 범위 밖이다.
  - 데이터는 수동 SQL 삽입보다 수집기/업서터를 통해 canonical DB에 넣는다.
  - portfolio review는 position snapshot을 입력으로 사용한다.

## Scope

- 포함:
  - CSV position snapshot loader
  - portfolio upsert
  - position snapshot upsert
  - canonical symbol lookup
  - active thesis auto-link fallback
  - CLI, tests, Docker verify, docs
- 제외:
  - broker API 또는 실계좌 sync
  - trade/order 생성
  - portfolio optimizer
  - live credentials 또는 secret handling
  - portfolio review action rule 변경

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/db-schema-design.md`
  - `docs/portfolio-review-bootstrap.md`
  - `docs/position-snapshot-ingest.md`
  - `docs/plans/2026-04-26-position-snapshot-ingest.md`
  - `docs/tasks/position-snapshot-ingest/`
  - `docs/verification-plan.md`
  - `scripts/verify_portfolio_review_bootstrap.sh`
  - `scripts/verify_position_snapshot_ingest.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/portfolio/`
  - `tests/fixtures/portfolio_positions_long_term_paper.csv`
  - `tests/test_ingest_cli.py`
  - `tests/test_position_snapshot_ingest.py`
- 수정 금지 파일:
  - portfolio review action rule unless only using the new ingest command in verify
  - recommendation score formula
  - thesis review rule
  - broker/trade execution path
  - secrets or live credentials
- 검증에 사용할 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n scripts/verify_position_snapshot_ingest.sh`
  - `bash -n scripts/verify_portfolio_review_bootstrap.sh`
  - `bash scripts/verify_position_snapshot_ingest.sh`
  - `bash scripts/verify_portfolio_review_bootstrap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task position-snapshot-ingest`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `src/stockanalysis/ingest/portfolio/position.py`
  - `tests/test_position_snapshot_ingest.py`
  - `tests/fixtures/portfolio_positions_long_term_paper.csv`
  - `scripts/verify_position_snapshot_ingest.sh`
  - `docs/position-snapshot-ingest.md`
  - `docs/tasks/position-snapshot-ingest/contract.md`
  - `docs/tasks/position-snapshot-ingest/plan.md`
  - `docs/tasks/position-snapshot-ingest/handoff.md`
  - `docs/tasks/position-snapshot-ingest/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] `portfolio-position-snapshot-upsert` CLI가 존재한다
- [x] CSV fixture가 `portfolio.position_snapshot`에 저장된다
- [x] 기존 portfolio review verify가 수동 SQL 삽입 대신 position snapshot ingest를 사용한다
- [x] 실거래 자동화가 범위 밖임이 문서화되어 있다

## Verification Plan

- 자동 검증: compileall, unittest, shell syntax, Docker integration verify, harness verify, placeholder 검색
- 수동 검증: `docs/position-snapshot-ingest.md`에서 CSV schema, boundary, next step이 명확한지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: Docker Postgres에서 CSV 기반 AAPL position snapshot 1건이 저장되고, active thesis가 연결되며, latest `portfolio_position_snapshot_upsert` pipeline run status가 `succeeded`다.

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: position snapshot module, CLI command, verify script, docs만 제거하면 이전 portfolio review 상태로 복귀한다.

## Open Questions

- 질문: 실제 broker API를 바로 연결할지
- 답: 이번 작업은 표준 CSV upsert만 만든다. broker-specific adapter는 후속 task로 분리한다.

- 질문: CSV row에 thesis id가 없으면 어떻게 연결할지
- 답: 해당 instrument의 latest active thesis를 자동 연결한다.
