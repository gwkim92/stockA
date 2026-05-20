# Task Contract

## Task

- 이름: data-operations-runtime-env-readiness
- 요청: data operations scheduler 활성화 전에 repo 밖 runtime env readiness를 검증하는 템플릿, checker, CLI, 문서를 구현한다.
- 담당: Codex
- 날짜: 2026-05-04

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: database, FRED, Alpha Vantage, SEC identity, portfolio snapshot source, LLM provider, artifact root에 필요한 runtime env가 repo 밖 파일로 준비됐는지 secret-free JSON으로 판정할 수 있다.

## Why

- 반복 운영 루프는 real credentials, input file, artifact root 없이 scheduler만 켜면 실패와 비밀 유출 위험이 커진다.
- cadence registry와 artifact runner 다음에는 각 cadence job이 요구하는 env group을 자동으로 검증해야 한다.
- env readiness는 실제 네트워크/API 호출이 아니라 activation gate다. 값 존재, placeholder 제거, repo-outside 경로, 최소 형식만 검증한다.

## Scope

- 포함:
  - env readiness Python module
  - `stockanalysis-ingest data-operations-env-readiness` CLI
  - repo-outside env template renderer
  - trusted env file checker
  - unit/CLI/script verification
  - roadmap, README, AGENTS, verification plan, task handoff 갱신
- 제외:
  - actual scheduler activation
  - cron/launchd/GitHub Actions 설치
  - real credentials 생성/저장
  - provider network smoke
  - DB schema changes
  - write APIs, RBAC, audit write model
  - broker/order flow
  - benchmark/scoring/evaluation split 변경
  - unrelated `ai-retrieval-graph-foundation` local documents

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/env_readiness.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_data_operations_env_readiness.py`
  - `tests/test_ingest_cli.py`
  - `scripts/render_data_operations_env_template.sh`
  - `scripts/check_data_operations_runtime_env.sh`
  - `scripts/verify_data_operations_runtime_env_readiness.sh`
  - `docs/data-operations-runtime-env-readiness.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `scripts/verify_data_operations_artifact_runner.sh`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/plans/2026-05-04-data-operations-runtime-env-readiness.md`
  - `docs/tasks/data-operations-runtime-env-readiness/`
- 수정 금지 파일:
  - `db/migrations/`
  - production env/secrets/deployment files
  - benchmark/evaluation/scoring files
  - broker/order implementation
  - unrelated `ai-retrieval-graph-foundation` local documents

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_data_operations_runtime_env_readiness.sh`
  - `bash scripts/verify_data_operations_artifact_runner.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=src python3 -m unittest discover -s tests`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task data-operations-runtime-env-readiness`
  - `git diff --check`

## Deliverables

- Env readiness module and CLI
- Repo-outside env template renderer
- Runtime env checker
- Unit tests and verification script
- Task docs and roadmap updates

## Completion Criteria

- [x] checker refuses repo-inside env files.
- [x] renderer refuses repo-inside output paths.
- [x] unedited template fails because placeholders remain.
- [x] valid temp env produces secret-free `runtime_env_readiness=passed`.
- [x] missing/invalid database, provider, snapshot, LLM, artifact root env fail with actionable messages.
- [x] CLI prints no secret values.
- [x] roadmap moves fixed next task after completion.
- [x] verification commands pass and evidence is recorded.

## Risks

- This does not prove provider credentials are accepted by remote APIs.
- This does not activate scheduling.
- Operators must still store the actual env file outside git and provision secrets in the runtime host.
