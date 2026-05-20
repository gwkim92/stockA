# Session Handoff

## Active Task

- 이름: hosted-database-runtime-decision
- 담당: Codex
- 날짜: 2026-05-20

## Current Status

- 완료:
  - task contract and implementation plan created.
  - `stockanalysis.operations.hosted_runtime_decision` report builder and markdown renderer added.
  - `stockanalysis-operations hosted-database-runtime-decision` CLI added.
  - default decision recommends `supabase_free_postgres_plus_github_actions_worker` with `setup_required_for_hosted_database`.
  - hosted DB configured state moves to `ready_for_hosted_database_migration_smoke`.
  - existing runtime host state prefers `existing_host_postgres_plus_systemd_worker`.
  - local-only accepted state remains explicit and not external scheduler ready.
  - focused unit/CLI tests and verification script added.
  - roadmap, AGENTS, and verification plan updated.
- 막힌 점:
  - 실제 hosted DB는 아직 생성되지 않았다.
  - DB URL/GitHub Secrets는 아직 제공되지 않았다.

## Exact Next Step

- 다음 세션은 이것부터 시작: `supabase-free-postgres-setup-packet`에서 사용자가 Supabase에서 무엇을 만들고, 어떤 connection string/secret 이름을 repo-outside env와 GitHub Secrets에 넣을지 정확히 정리한다.
- 금지: 이 handoff만으로 Supabase 프로젝트 생성, DB URL 저장, GitHub Actions workflow 생성, migration 실행, scheduler 배포를 하지 않는다.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_hosted_runtime_decision tests.test_data_operations_cli.DataOperationsCliTests.test_hosted_database_runtime_decision_command_writes_output_and_markdown tests.test_data_operations_cli.DataOperationsCliTests.test_hosted_database_runtime_decision_rejects_repo_inside_output`
- `bash scripts/verify_hosted_database_runtime_decision.sh`
- `bash scripts/verify_project_execution_roadmap.sh`
- `python3 -m compileall src tests`
- `git diff --check`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task hosted-database-runtime-decision`

## Risks

- Supabase Free는 500MB DB size, inactivity pause, production-grade backup 부재 같은 제약이 있다.
- GitHub Actions worker는 hosted DB secret이 있어야만 실제 수집 결과를 저장할 수 있다.
- Render Free Postgres는 30일 만료라 지속 운영 DB로 부적합하다.
