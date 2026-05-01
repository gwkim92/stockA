# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: thesis-bootstrap
- 요청: deterministic recommendation rows에 active investment thesis를 생성 또는 갱신해 recommendation과 연결한다.
- 담당: Codex
- 날짜: 2026-04-26

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `thesis-bootstrap` CLI가 selected recommendation batch의 active recommendation rows에 대해 `signal.investment_thesis`를 만들거나 갱신하고 `signal.recommendation.thesis_id`를 채운다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: recommendation row만 있으면 rank/action은 남지만 왜 보거나 매수 후보인지, 어떤 조건에서 무효화되는지 추적하기 어렵다. thesis가 연결되어야 보유 검토와 성과 분석이 같은 판단 근거를 재구성할 수 있다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/signal/recommendation.py`
  - `src/stockanalysis/signal/cycle.py`
  - `src/stockanalysis/signal/features.py`
  - `src/stockanalysis/signal/theme_enrichment.py`
- 관련 문서:
  - `docs/project-foundation.md`
  - `docs/db-schema-design.md`
  - `docs/recommendation-bootstrap.md`
  - `docs/cycle-state-snapshot.md`
- 이전 결정:
  - AI는 recommendation rank를 직접 결정하지 않는다.
  - recommendation bootstrap은 `thesis_id = null`로 시작했다.
  - thesis prose는 처음에는 deterministic template로 시작하고 LLM explanation은 후속 layer로 둔다.

## Scope

- 포함:
  - active recommendation rows 대상 thesis bootstrap
  - same instrument/node/thesis_type active thesis update-or-insert
  - recommendation `thesis_id` link
  - CLI, tests, Docker verify, docs
- 제외:
  - LLM-generated thesis
  - thesis factor table
  - thesis review scheduler
  - portfolio action or trade automation
  - recommendation score 변경

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/db-schema-design.md`
  - `docs/recommendation-bootstrap.md`
  - `docs/thesis-bootstrap.md`
  - `docs/plans/2026-04-26-thesis-bootstrap.md`
  - `docs/tasks/thesis-bootstrap/`
  - `docs/verification-plan.md`
  - `scripts/verify_thesis_bootstrap.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/signal/thesis.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_thesis_bootstrap.py`
- 수정 금지 파일:
  - existing recommendation scoring logic
  - existing cycle snapshot logic
  - AI event extraction path
  - portfolio or performance logic
- 검증에 사용할 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n scripts/verify_thesis_bootstrap.sh`
  - `bash scripts/verify_thesis_bootstrap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task thesis-bootstrap`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `src/stockanalysis/signal/thesis.py`
  - `tests/test_thesis_bootstrap.py`
  - `scripts/verify_thesis_bootstrap.sh`
  - `docs/thesis-bootstrap.md`
  - `docs/tasks/thesis-bootstrap/contract.md`
  - `docs/tasks/thesis-bootstrap/plan.md`
  - `docs/tasks/thesis-bootstrap/handoff.md`
  - `docs/tasks/thesis-bootstrap/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] active recommendation rows를 입력으로 사용한다
- [x] investment thesis와 recommendation link가 저장된다
- [x] AI path와 deterministic path를 계속 병렬로 가져갈 수 있게 기록한다

## Verification Plan

- 자동 검증: compileall, unittest, shell syntax, Docker integration verify, harness verify, placeholder 검색
- 수동 검증: `docs/thesis-bootstrap.md`에서 thesis template, invalidation rule, current limits가 명확한지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: Docker Postgres에서 `signal.investment_thesis` row가 생성 또는 갱신되고 `signal.recommendation.thesis_id`가 채워지며 latest `thesis_bootstrap` pipeline run status가 `succeeded`다.

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `thesis-bootstrap` command, thesis module, verify script, docs만 제거하면 이전 recommendation 상태로 복귀한다.

## Open Questions

- 질문: LLM으로 thesis prose를 바로 생성할지
- 답이 없을 때 적용할 임시 가정: 이번 bootstrap은 deterministic template만 사용하고 LLM은 후속 explanation/report layer에서 붙인다.

- 질문: thesis factor/review table을 지금 도입할지
- 답이 없을 때 적용할 임시 가정: 이번 bootstrap은 existing `signal.investment_thesis`와 `signal.recommendation.thesis_id`만 사용한다.
