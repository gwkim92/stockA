# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: instrument-theme-enrichment
- 요청: strategy universe instruments를 existing event impact evidence와 연결해 internal theme memberships를 bootstrap한다.
- 담당: Codex
- 날짜: 2026-04-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `instrument-theme-enrichment` CLI가 selected strategy universe instruments에 대해 `ref.instrument_classification_membership`의 `derived_theme` rows를 deterministic하게 저장한다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: cycle engine은 classification node 기준으로 돌고, recommendation은 instrument와 theme/sector 관계를 읽어야 한다. feature snapshot 다음에 instrument-theme 연결이 없으면 cycle state와 thesis/recommendation으로 자연스럽게 이어지기 어렵다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/signal/universe.py`
  - `src/stockanalysis/signal/features.py`
  - `src/stockanalysis/ingest/sec/classification_impact.py`
  - `src/stockanalysis/ingest/sec/instrument_impact.py`
- 관련 문서:
  - `docs/strategy-universe-slicing.md`
  - `docs/market-feature-snapshot.md`
  - `docs/event-classification-impact-bootstrap.md`
  - `docs/event-instrument-impact-bootstrap.md`
  - `docs/db-schema-design.md`
- 이전 결정:
  - strategy universe snapshot이 recommendation 이전 investable boundary다.
  - feature snapshot이 그 다음 deterministic 수치 경계다.
  - AI event path와 deterministic market path를 병렬로 유지한다.

## Scope

- 포함:
  - selected strategy universe instruments만 대상
  - internal theme taxonomy만 대상
  - `derived_theme` membership bootstrap
  - CLI, tests, Docker verify, docs
- 제외:
  - fuzzy matching
  - external taxonomy ingestion
  - sector/industry enrichment
  - AI semantic node selection
  - recommendation logic

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/db-schema-design.md`
  - `docs/instrument-theme-enrichment.md`
  - `docs/market-feature-snapshot.md`
  - `docs/plans/2026-04-23-instrument-theme-enrichment.md`
  - `docs/tasks/instrument-theme-enrichment/`
  - `docs/verification-plan.md`
  - `scripts/verify_instrument_theme_enrichment.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/signal/theme_enrichment.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_instrument_theme_enrichment.py`
- 수정 금지 파일:
  - existing event impact bootstrap logic
  - existing strategy universe runner behavior
  - existing AI event extraction path
  - recommendation logic
- 검증에 사용할 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n scripts/verify_instrument_theme_enrichment.sh`
  - `bash scripts/verify_instrument_theme_enrichment.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task instrument-theme-enrichment`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `src/stockanalysis/signal/theme_enrichment.py`
  - `tests/test_instrument_theme_enrichment.py`
  - `scripts/verify_instrument_theme_enrichment.sh`
  - `docs/instrument-theme-enrichment.md`
  - `docs/tasks/instrument-theme-enrichment/contract.md`
  - `docs/tasks/instrument-theme-enrichment/plan.md`
  - `docs/tasks/instrument-theme-enrichment/handoff.md`
  - `docs/tasks/instrument-theme-enrichment/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] strategy universe snapshot을 입력으로 사용한다
- [x] event impacts를 internal theme membership으로 연결한다
- [x] AI path와 deterministic path를 계속 병렬로 가져갈 수 있게 기록한다

## Verification Plan

- 자동 검증: compileall, unittest, shell syntax, Docker integration verify, harness verify, placeholder 검색
- 수동 검증: `docs/instrument-theme-enrichment.md`에서 current bootstrap rule과 current limits가 명확한지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: Docker Postgres에서 `ref.instrument_classification_membership` rows가 생성되고 latest `instrument_theme_enrichment` pipeline run status가 `succeeded`다.

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `instrument-theme-enrichment` command, signal module, verify script, docs만 제거하면 이전 event impact + feature snapshot 상태로 복귀한다.

## Open Questions

- 질문: parent theme propagation을 지금 넣을지
- 답이 없을 때 적용할 임시 가정: 이번 bootstrap은 direct event-linked internal theme/subtheme만 연결하고 parent propagation은 cycle-state task에서 검토한다.
