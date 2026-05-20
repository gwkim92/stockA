# Task Contract

## Task

- 이름: hosted-database-runtime-decision
- 요청: 무료 조건에서 외부 scheduler를 가능하게 할 hosted DB/runtime 경로를 결정한다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 현재 local-only DB/runtime 상태에서 무엇을 선택해야 외부 scheduler가 가능해지는지, 어떤 무료 후보가 현실적인지, 어떤 준비물이 필요한지 secret-free decision packet으로 확인할 수 있다.

## Why

- server scheduler target decision은 외부 scheduler 배포를 `hosted_database_not_configured`와 `runtime_host_not_available`로 차단했다.
- 사용자는 무료 조건을 명시했다.
- 외부 scheduler가 로컬 `127.0.0.1` Postgres에 접근하는 것처럼 설계하면 실제 자동화가 실패한다.

## Scope

- 포함:
  - hosted DB/runtime decision builder
  - `stockanalysis-operations hosted-database-runtime-decision` CLI
  - Supabase Free, existing host, Render Free Postgres, local-only candidate matrix
  - GitHub Actions worker readiness 판단
  - tests, verify script, docs/handoff/review
- 제외:
  - Supabase/Neon/Render 프로젝트 생성
  - DB URL/secret 등록
  - GitHub Actions workflow 생성
  - migration 실행
  - scheduler 배포
  - 실거래/broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/hosted_runtime_decision.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_hosted_runtime_decision.py`
  - `tests/test_data_operations_cli.py`
  - `scripts/verify_hosted_database_runtime_decision.sh`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `AGENTS.md`
  - task docs
- 수정 금지 파일:
  - `.env` secret values
  - `.github/workflows/*`
  - DB migrations
  - scheduler host install files
  - scoring/evaluation benchmark

## Boundaries

- decision packet은 DB URL/API key/token/password를 포함하지 않는다.
- 이 작업은 DB/provider 계정을 만들지 않는다.
- 실제 migration/seed/worker smoke는 다음 setup packet 이후에만 수행한다.
- 무료 조건을 깨는 후보는 추천하지 않는다.

## Verification Commands

- 검증에 사용할 명령:
- `PYTHONPATH=src python3 -m unittest tests.test_hosted_runtime_decision tests.test_data_operations_cli.DataOperationsCliTests.test_hosted_database_runtime_decision_command_writes_output_and_markdown tests.test_data_operations_cli.DataOperationsCliTests.test_hosted_database_runtime_decision_rejects_repo_inside_output`
- `bash scripts/verify_hosted_database_runtime_decision.sh`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task hosted-database-runtime-decision`
- `git diff --check`

## Done Criteria

- [x] Default decision recommends Supabase Free Postgres setup packet before GitHub Actions scheduler.
- [x] Hosted DB configured state becomes ready for migration/smoke.
- [x] Existing host state prefers existing host path.
- [x] Local-only accepted state remains explicit and does not claim external scheduler readiness.
- [x] Verification evidence is recorded in handoff/review.
