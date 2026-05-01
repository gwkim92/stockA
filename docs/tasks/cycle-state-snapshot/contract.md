# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: cycle-state-snapshot
- 요청: selected strategy universe의 direct theme memberships와 deterministic feature/event evidence를 이용해 node-level cycle state snapshot을 저장한다.
- 담당: Codex
- 날짜: 2026-04-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `cycle-state-snapshot` CLI가 selected `internal_theme` nodes에 대해 `signal.cycle_state_snapshot` rows를 deterministic하게 저장한다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: theme membership까지만 있으면 `어떤 종목이 어떤 노드에 연결되는지`만 안다. 중장기 추천과 보유 검토로 가려면 node마다 현재 국면을 판정한 canonical cycle snapshot이 필요하다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/signal/features.py`
  - `src/stockanalysis/signal/theme_enrichment.py`
  - `src/stockanalysis/signal/universe.py`
  - `src/stockanalysis/ingest/sec/classification_impact.py`
  - `src/stockanalysis/ingest/sec/instrument_impact.py`
- 관련 문서:
  - `docs/project-foundation.md`
  - `docs/db-schema-design.md`
  - `docs/market-feature-snapshot.md`
  - `docs/instrument-theme-enrichment.md`
- 이전 결정:
  - strategy universe는 investable boundary다.
  - feature snapshot은 instrument-level deterministic 숫자 경계다.
  - theme enrichment는 direct internal theme membership만 만든다.
  - AI path와 deterministic path를 병렬로 유지한다.

## Scope

- 포함:
  - selected strategy universe 기준 node-level cycle snapshot
  - `internal_theme` taxonomy만 대상
  - `trend_score`, `breadth_score`, `event_heat_score`, `cycle_score`, `cycle_state`
  - CLI, tests, Docker verify, docs
- 제외:
  - parent theme propagation
  - `signal.classification_feature_value` 도입
  - sector/industry cycle
  - AI state inference
  - recommendation logic

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/cycle-state-snapshot.md`
  - `docs/db-schema-design.md`
  - `docs/instrument-theme-enrichment.md`
  - `docs/plans/2026-04-23-cycle-state-snapshot.md`
  - `docs/tasks/cycle-state-snapshot/`
  - `docs/verification-plan.md`
  - `scripts/verify_cycle_state_snapshot.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/signal/cycle.py`
  - `tests/test_cycle_state_snapshot.py`
  - `tests/test_ingest_cli.py`
- 수정 금지 파일:
  - existing event impact bootstrap logic
  - existing feature snapshot logic
  - existing AI event extraction path
  - recommendation logic
- 검증에 사용할 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n scripts/verify_cycle_state_snapshot.sh`
  - `bash scripts/verify_cycle_state_snapshot.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task cycle-state-snapshot`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `src/stockanalysis/signal/cycle.py`
  - `tests/test_cycle_state_snapshot.py`
  - `scripts/verify_cycle_state_snapshot.sh`
  - `docs/cycle-state-snapshot.md`
  - `docs/tasks/cycle-state-snapshot/contract.md`
  - `docs/tasks/cycle-state-snapshot/plan.md`
  - `docs/tasks/cycle-state-snapshot/handoff.md`
  - `docs/tasks/cycle-state-snapshot/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] selected strategy universe를 입력으로 사용한다
- [x] direct internal theme memberships를 node-level cycle snapshot으로 집계한다
- [x] AI path와 deterministic path를 계속 병렬로 가져갈 수 있게 기록한다

## Verification Plan

- 자동 검증: compileall, unittest, shell syntax, Docker integration verify, harness verify, placeholder 검색
- 수동 검증: `docs/cycle-state-snapshot.md`에서 current state mapping과 current limits가 명확한지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: Docker Postgres에서 `signal.cycle_state_snapshot` row가 생성되고 latest `cycle_state_snapshot` pipeline run status가 `succeeded`다.

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `cycle-state-snapshot` command, cycle module, verify script, docs만 제거하면 이전 feature/theme enrichment 상태로 복귀한다.

## Open Questions

- 질문: parent theme propagation을 지금 넣을지
- 답이 없을 때 적용할 임시 가정: 이번 bootstrap은 direct theme node만 계산하고 parent propagation은 recommendation 또는 classification-feature task에서 검토한다.

- 질문: classification-level feature table을 지금 도입할지
- 답이 없을 때 적용할 임시 가정: 이번 bootstrap은 `signal.cycle_state_snapshot`과 `evidence_json`만 사용하고 별도 classification feature table은 미룬다.
