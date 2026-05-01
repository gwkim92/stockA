# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: recommendation-bootstrap
- 요청: selected strategy universe, market feature, direct theme membership, cycle snapshot을 이용해 deterministic recommendation batch를 저장한다.
- 담당: Codex
- 날짜: 2026-04-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `recommendation-bootstrap` CLI가 selected strategy universe 내 evidence-backed instruments에 대해 `signal.recommendation_batch`와 `signal.recommendation` rows를 deterministic하게 저장한다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: 지금까지는 universe, feature, theme, cycle 상태가 각각 저장되었다. 추천 운영 시스템으로 가려면 이 입력들을 하나의 추천 batch로 묶어 rank, bucket, action, score를 남겨야 이후 thesis/review/performance가 같은 판단 시점을 재구성할 수 있다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/signal/universe.py`
  - `src/stockanalysis/signal/features.py`
  - `src/stockanalysis/signal/theme_enrichment.py`
  - `src/stockanalysis/signal/cycle.py`
- 관련 문서:
  - `docs/project-foundation.md`
  - `docs/db-schema-design.md`
  - `docs/market-feature-snapshot.md`
  - `docs/instrument-theme-enrichment.md`
  - `docs/cycle-state-snapshot.md`
- 이전 결정:
  - AI는 추천 rank를 직접 결정하지 않는다.
  - strategy universe는 investable boundary다.
  - cycle state는 direct internal theme node 기준 bootstrap이다.
  - thesis creation은 recommendation 이후 별도 task로 분리한다.

## Scope

- 포함:
  - selected strategy universe 기준 recommendation batch
  - evidence-backed instrument-node candidates만 추천 row 생성
  - deterministic score, bucket, action, rank, optional recommended weight
  - CLI, tests, Docker verify, docs
- 제외:
  - AI recommendation ranking
  - investment thesis 생성
  - portfolio execution 또는 실거래
  - `signal.recommendation_score_component` migration
  - parent theme propagation

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/db-schema-design.md`
  - `docs/cycle-state-snapshot.md`
  - `docs/recommendation-bootstrap.md`
  - `docs/plans/2026-04-25-recommendation-bootstrap.md`
  - `docs/tasks/recommendation-bootstrap/`
  - `docs/verification-plan.md`
  - `scripts/verify_recommendation_bootstrap.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/signal/recommendation.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_recommendation_bootstrap.py`
- 수정 금지 파일:
  - existing event impact bootstrap logic
  - existing feature snapshot logic
  - existing cycle snapshot logic
  - AI event extraction path
- 검증에 사용할 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n scripts/verify_recommendation_bootstrap.sh`
  - `bash scripts/verify_recommendation_bootstrap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task recommendation-bootstrap`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `src/stockanalysis/signal/recommendation.py`
  - `tests/test_recommendation_bootstrap.py`
  - `scripts/verify_recommendation_bootstrap.sh`
  - `docs/recommendation-bootstrap.md`
  - `docs/tasks/recommendation-bootstrap/contract.md`
  - `docs/tasks/recommendation-bootstrap/plan.md`
  - `docs/tasks/recommendation-bootstrap/handoff.md`
  - `docs/tasks/recommendation-bootstrap/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] selected strategy universe를 입력으로 사용한다
- [x] cycle state와 market feature를 deterministic score로 결합한다
- [x] AI path와 deterministic path를 계속 병렬로 가져갈 수 있게 기록한다

## Verification Plan

- 자동 검증: compileall, unittest, shell syntax, Docker integration verify, harness verify, placeholder 검색
- 수동 검증: `docs/recommendation-bootstrap.md`에서 scoring rule, bucket/action rule, current limits가 명확한지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: Docker Postgres에서 `signal.recommendation_batch`와 `signal.recommendation` row가 생성되고 latest `recommendation_bootstrap` pipeline run status가 `succeeded`다.

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `recommendation-bootstrap` command, recommendation module, verify script, docs만 제거하면 이전 cycle snapshot 상태로 복귀한다.

## Open Questions

- 질문: thesis를 recommendation과 동시에 만들지
- 답이 없을 때 적용할 임시 가정: 이번 bootstrap은 `thesis_id = null`로 두고, thesis는 `thesis-bootstrap`에서 생성한다.

- 질문: score component table을 지금 도입할지
- 답이 없을 때 적용할 임시 가정: migration 없이 기존 `signal.recommendation`만 사용한다. component detail은 docs와 code constant로 고정한다.
