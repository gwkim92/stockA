# Task Contract

## Task

- 이름: frontend-api-server-deployment-boundary
- 요청: FastAPI read-only frontend API server의 배포/process/runtime env 경계를 고정한다.
- 담당: Codex
- 날짜: 2026-05-03

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 실제 secret이나 host deployment config를 repo에 두지 않으면서, production 후보 FastAPI server를 어떤 process/topology/env로 실행해야 하는지 검증 가능한 형태로 남긴다.

## Why

- API server는 구현됐지만, 어떤 host/port/profile/env/proxy 가정으로 운영해야 하는지 명시되지 않으면 이후 배포와 보안 경계가 흔들린다.
- secrets와 실제 배포 설정은 고위험 경로이므로 repo 밖 env file과 preflight gate로만 다뤄야 한다.

## Scope

- 포함:
  - deployment topology 문서
  - reverse proxy/TLS assumptions 문서
  - repo 밖 runtime env template renderer
  - runtime env preflight checker
  - env-based FastAPI server run wrapper
  - verification script
  - docs/task handoff 갱신
- 제외:
  - actual host service install
  - launchd/systemd/Docker/Kubernetes manifest 생성
  - reverse proxy config 파일 생성
  - TLS certificate/key 생성 또는 저장
  - production secret 저장
  - write endpoint
  - full auth/RBAC/session/actor identity
  - DB schema/scoring/benchmark/evaluation split 변경
  - broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `scripts/render_frontend_api_server_env_template.sh`
  - `scripts/check_frontend_api_server_runtime_env.sh`
  - `scripts/run_frontend_api_server.sh`
  - `scripts/verify_frontend_api_server_deployment_boundary.sh`
  - `docs/frontend-api-server-deployment-boundary.md`
  - `docs/frontend-api-server.md`
  - `docs/frontend-api-runtime-boundary.md`
  - `docs/frontend-architecture.md`
  - `docs/frontend-runtime-db-smoke.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/plans/2026-05-03-frontend-api-server-deployment-boundary.md`
  - `docs/tasks/frontend-api-server-deployment-boundary/`
- 수정 금지 파일:
  - DB migrations
  - scoring formula
  - benchmark/evaluation split
  - committed env files with real secrets
  - actual host service manager config
  - reverse proxy config
  - TLS keys/certificates
  - broker/order implementation

## Verification Commands

- 검증에 사용할 명령:
  - `bash -n scripts/render_frontend_api_server_env_template.sh`
  - `bash -n scripts/check_frontend_api_server_runtime_env.sh`
  - `bash -n scripts/run_frontend_api_server.sh`
  - `bash -n scripts/verify_frontend_api_server_deployment_boundary.sh`
  - `bash scripts/verify_frontend_api_server_deployment_boundary.sh`
  - `bash scripts/verify_frontend_api_server.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=src python3 -m unittest discover -s tests`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-server-deployment-boundary`
  - `git diff --check`

## Deliverables

- Runtime env template renderer
- Runtime env preflight checker
- Env-based run wrapper
- Deployment boundary docs
- Verification script
- Updated roadmap/handoff/review

## Completion Criteria

- [x] Env template renderer refuses repo-internal output.
- [x] Env checker refuses repo-internal env file.
- [x] Unedited template fails readiness.
- [x] Valid temp env passes readiness without DB connection.
- [x] Preflight output does not expose DB URL or read token.
- [x] Run wrapper supports `--preflight-only`.
- [x] Docs define loopback API behind TLS reverse proxy boundary.
- [x] Verification commands pass and evidence is recorded.

## Risks

- This slice does not prove a real host service manager or reverse proxy works.
- This slice validates DB URL shape but does not connect to the production DB.
- `read-token` remains a deployment seam, not full user identity/RBAC.
