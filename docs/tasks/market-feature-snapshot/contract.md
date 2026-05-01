# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: market-feature-snapshot
- 요청: strategy universe members에 대해 deterministic market features를 계산해 recommendation 이전의 feature snapshot boundary를 만든다.
- 담당: Codex
- 날짜: 2026-04-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `market-feature-snapshot` CLI가 `signal.strategy_universe_batch/member`를 입력으로 읽고 `signal.feature_definition`, `signal.instrument_feature_value`에 bootstrap feature set을 저장한다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: recommendation과 thesis는 같은 universe snapshot 위에서 feature를 읽어야 한다. universe slice 다음에 feature snapshot이 없으면 AI event path와 별개로 deterministic recommendation chain이 끊긴다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/signal/universe.py`
  - `src/stockanalysis/ingest/market/price.py`
  - `src/stockanalysis/ingest/cli.py`
- 관련 문서:
  - `docs/strategy-universe-slicing.md`
  - `docs/db-schema-design.md`
  - `docs/verification-plan.md`
  - `docs/tasks/strategy-universe-slicing/handoff.md`
- 이전 결정:
  - strategy universe snapshot이 recommendation 이전 boundary다.
  - AI path는 SEC event intelligence로 별도 진행 중이며, deterministic market path도 병렬로 이어가야 한다.

## Scope

- 포함:
  - feature definition schema
  - instrument feature snapshot schema
  - price history lookup from strategy universe snapshot
  - bootstrap deterministic features
  - cross-sectional zscore
  - CLI, tests, Docker verify, docs
- 제외:
  - recommendation score
  - cycle state snapshot
  - classification feature values
  - AI-derived ranking
  - live API calls

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `db/migrations/0006_market_feature_snapshot.sql`
  - `docs/db-schema-design.md`
  - `docs/market-feature-snapshot.md`
  - `docs/plans/2026-04-23-market-feature-snapshot.md`
  - `docs/tasks/market-feature-snapshot/`
  - `docs/verification-plan.md`
  - `scripts/verify_market_feature_snapshot.sh`
  - `src/stockanalysis/signal/__init__.py`
  - `src/stockanalysis/signal/features.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_market_feature_snapshot.py`
  - `tests/test_ingest_cli.py`
- 수정 금지 파일:
  - existing market price upsert logic
  - existing strategy universe runner behavior
  - AI event extraction path
  - recommendation logic
- 검증에 사용할 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n scripts/verify_market_feature_snapshot.sh`
  - `bash scripts/verify_market_feature_snapshot.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task market-feature-snapshot`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `db/migrations/0006_market_feature_snapshot.sql`
  - `src/stockanalysis/signal/features.py`
  - `tests/test_market_feature_snapshot.py`
  - `scripts/verify_market_feature_snapshot.sh`
  - `docs/market-feature-snapshot.md`
  - `docs/tasks/market-feature-snapshot/contract.md`
  - `docs/tasks/market-feature-snapshot/plan.md`
  - `docs/tasks/market-feature-snapshot/handoff.md`
  - `docs/tasks/market-feature-snapshot/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] strategy universe snapshot을 입력으로 사용한다
- [x] deterministic feature values가 `signal.instrument_feature_value`에 저장된다
- [x] 이전 AI event path와 deterministic market path를 함께 이어갈 수 있게 기록한다

## Verification Plan

- 자동 검증: compileall, unittest, shell syntax, Docker integration verify, harness verify, placeholder 검색
- 수동 검증: `docs/market-feature-snapshot.md`에서 bootstrap feature formulas와 current limits가 명확한지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: Docker Postgres에서 feature definition rows와 per-instrument feature rows가 생성되고 latest `market_feature_snapshot` pipeline run status가 `succeeded`다.

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `market-feature-snapshot` command, feature snapshot module, migration 0006, verify script만 제거하면 기존 universe path로 복귀한다.

## Open Questions

- 질문: 이후 feature set을 factor-style wider table로 확장할지
- 답이 없을 때 적용할 임시 가정: 현재는 bootstrap deterministic feature set만 canonical Postgres에 저장하고, wide research matrix는 나중에 Parquet/DuckDB로 뺀다.
