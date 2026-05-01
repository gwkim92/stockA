# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: thesis-review-bootstrap
- 요청: active investment thesis를 현재 recommendation/cycle evidence 기준으로 검토해 deterministic review row를 저장한다.
- 담당: Codex
- 날짜: 2026-04-26

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `thesis-review-bootstrap` CLI가 selected recommendation batch에 연결된 active thesis를 읽고 `signal.thesis_review`에 review action, health score, summary, next review date를 저장한다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: recommendation과 thesis만 있으면 최초 판단 근거는 남지만, 이후 계속 잘 투자하고 있는지 검토하는 이력이 없다. 중장기/장기 투자 시스템에서는 thesis health와 다음 검토일이 canonical state로 남아야 한다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/signal/thesis.py`
  - `src/stockanalysis/signal/recommendation.py`
  - `src/stockanalysis/signal/cycle.py`
  - `src/stockanalysis/signal/features.py`
- 관련 문서:
  - `docs/project-foundation.md`
  - `docs/db-schema-design.md`
  - `docs/recommendation-bootstrap.md`
  - `docs/thesis-bootstrap.md`
  - `docs/ai-intelligence-architecture.md`
- 이전 결정:
  - AI는 추천 rank를 직접 결정하지 않는다.
  - thesis prose도 아직 deterministic template만 사용한다.
  - review는 LLM이 아니라 검증 가능한 rule로 먼저 저장한다.

## Scope

- 포함:
  - `signal.thesis_review` migration
  - active recommendation에 연결된 active thesis 대상 review bootstrap
  - deterministic action/health score/next review date
  - CLI, tests, Docker verify, docs
- 제외:
  - LLM-generated review prose
  - investment thesis status 변경
  - portfolio action or trade automation
  - thesis factor table
  - recommendation score 변경

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `db/migrations/0007_thesis_review.sql`
  - `docs/db-schema-design.md`
  - `docs/thesis-bootstrap.md`
  - `docs/thesis-review-bootstrap.md`
  - `docs/plans/2026-04-26-thesis-review-bootstrap.md`
  - `docs/tasks/thesis-review-bootstrap/`
  - `docs/verification-plan.md`
  - `scripts/verify_thesis_review_bootstrap.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/signal/thesis_review.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_thesis_review_bootstrap.py`
- 수정 금지 파일:
  - existing recommendation scoring logic
  - existing thesis bootstrap logic except docs references
  - existing cycle snapshot logic
  - AI event extraction path
  - portfolio or trade logic
- 검증에 사용할 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n scripts/verify_thesis_review_bootstrap.sh`
  - `bash scripts/verify_thesis_review_bootstrap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task thesis-review-bootstrap`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `db/migrations/0007_thesis_review.sql`
  - `src/stockanalysis/signal/thesis_review.py`
  - `tests/test_thesis_review_bootstrap.py`
  - `scripts/verify_thesis_review_bootstrap.sh`
  - `docs/thesis-review-bootstrap.md`
  - `docs/tasks/thesis-review-bootstrap/contract.md`
  - `docs/tasks/thesis-review-bootstrap/plan.md`
  - `docs/tasks/thesis-review-bootstrap/handoff.md`
  - `docs/tasks/thesis-review-bootstrap/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] `signal.thesis_review` table이 실제 migration에 존재한다
- [x] active thesis review row가 저장된다
- [x] AI path와 deterministic path를 계속 병렬로 가져갈 수 있게 기록한다

## Verification Plan

- 자동 검증: compileall, unittest, shell syntax, Docker integration verify, harness verify, placeholder 검색
- 수동 검증: `docs/thesis-review-bootstrap.md`에서 review rule, action rule, current limits가 명확한지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: Docker Postgres에서 `signal.thesis_review` row가 생성 또는 갱신되고 latest `thesis_review_bootstrap` pipeline run status가 `succeeded`다.

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `0007_thesis_review.sql`, `thesis-review-bootstrap` command, thesis_review module, verify script, docs만 제거하면 이전 thesis 상태로 복귀한다.

## Open Questions

- 질문: review가 thesis status를 자동으로 invalidated/closed로 바꿀지
- 답이 없을 때 적용할 임시 가정: 이번 bootstrap은 review row만 저장하고 thesis status는 바꾸지 않는다.

- 질문: LLM으로 review summary를 바로 생성할지
- 답이 없을 때 적용할 임시 가정: 이번 bootstrap은 deterministic summary만 사용하고 LLM은 후속 review/report layer에서 붙인다.
