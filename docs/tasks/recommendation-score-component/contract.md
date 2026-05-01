# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: recommendation-score-component
- 요청: recommendation total score를 구성하는 component score와 weight를 canonical DB에 저장한다.
- 담당: Codex
- 날짜: 2026-04-26

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `recommendation-bootstrap` CLI가 recommendation row와 함께 `signal.recommendation_score_component` rows를 저장한다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: total score만 저장하면 추천이 왜 해당 bucket/action이 되었는지 나중에 재구성하기 어렵다. component score와 weight가 남아야 추천 품질, 실패 원인, scoring 변경 영향 분석을 할 수 있다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/signal/recommendation.py`
  - `src/stockanalysis/signal/cycle.py`
  - `src/stockanalysis/signal/features.py`
- 관련 문서:
  - `docs/recommendation-bootstrap.md`
  - `docs/db-schema-design.md`
  - `docs/verification-plan.md`
- 이전 결정:
  - AI는 추천 rank를 직접 결정하지 않는다.
  - recommendation score는 deterministic component score 합산으로 계산한다.
  - score component table은 아직 migration에 없어서 이번 작업에서 추가한다.

## Scope

- 포함:
  - `signal.recommendation_score_component` migration
  - recommendation bootstrap 중 component rows insert
  - component score, component weight, deterministic explanation 저장
  - tests, Docker verify, docs
- 제외:
  - recommendation score formula 변경
  - AI recommendation ranking
  - thesis/review logic 변경
  - portfolio execution 또는 실거래
  - live data smoke

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `db/migrations/0008_recommendation_score_component.sql`
  - `docs/db-schema-design.md`
  - `docs/recommendation-bootstrap.md`
  - `docs/recommendation-score-component.md`
  - `docs/plans/2026-04-26-recommendation-score-component.md`
  - `docs/tasks/recommendation-score-component/`
  - `docs/verification-plan.md`
  - `scripts/verify_recommendation_score_component.sh`
  - `src/stockanalysis/signal/recommendation.py`
  - `tests/test_recommendation_bootstrap.py`
- 수정 금지 파일:
  - recommendation formula constants unless documenting existing weights
  - cycle snapshot logic
  - thesis or thesis review runner logic
  - AI event extraction path
  - portfolio or trade logic
- 검증에 사용할 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n scripts/verify_recommendation_score_component.sh`
  - `bash scripts/verify_recommendation_score_component.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task recommendation-score-component`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `db/migrations/0008_recommendation_score_component.sql`
  - `scripts/verify_recommendation_score_component.sh`
  - `docs/recommendation-score-component.md`
  - `docs/tasks/recommendation-score-component/contract.md`
  - `docs/tasks/recommendation-score-component/plan.md`
  - `docs/tasks/recommendation-score-component/handoff.md`
  - `docs/tasks/recommendation-score-component/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] `signal.recommendation_score_component` table이 실제 migration에 존재한다
- [x] recommendation-bootstrap이 component rows를 저장한다
- [x] AI path와 deterministic path를 계속 병렬로 가져갈 수 있게 기록한다

## Verification Plan

- 자동 검증: compileall, unittest, shell syntax, Docker integration verify, harness verify, placeholder 검색
- 수동 검증: `docs/recommendation-score-component.md`에서 component score, weight, current limits가 명확한지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: Docker Postgres에서 `signal.recommendation_score_component` row가 생성되고 latest `recommendation_bootstrap` pipeline run status가 `succeeded`다.

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `0008_recommendation_score_component.sql`과 recommendation component insert 변경, verify script, docs만 제거하면 이전 total score-only recommendation 상태로 복귀한다.

## Open Questions

- 질문: component explanations를 LLM으로 생성할지
- 답: 이번 작업은 deterministic explanation만 저장한다. LLM explanation/report layer는 별도 task로 분리한다.

- 질문: score formula를 지금 바꿀지
- 답: 기존 formula와 weight를 유지하고 저장만 추가한다.
