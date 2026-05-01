# Task Contract

## Task

- 이름: project-execution-roadmap
- 요청: 현재까지의 진행상황을 재판단하고 흔들리지 않을 작업 순서와 근거를 하네스에 남긴다.
- 담당: Codex
- 날짜: 2026-05-01

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 프로젝트 진행 순서와 각 단계의 근거가 repo 문서와 task handoff에 고정되어 다음 작업이 같은 기준으로 이어진다.

## Why

- 최근 작업 흐름이 프론트, 백엔드, AI, 하네스 사이에서 흔들렸다.
- 다음 작업을 계속 진행하려면 “무엇이 먼저인가”를 구두가 아니라 repo-local artifact로 남겨야 한다.

## Scope

- 포함:
  - 현재 진행상황 요약
  - 남은 작업 구분
  - 고정 실행 순서
  - 순서별 근거와 guardrail
  - AGENTS repo map 최신화
  - verification script
  - task handoff/review
- 제외:
  - live read endpoint 구현
  - production API server 구현
  - auth/RBAC 구현
  - DB schema/scoring/benchmark 변경

## Mutable Surface

- 수정 가능한 파일:
  - `AGENTS.md`
  - `README.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `docs/tasks/project-execution-roadmap/`
  - `scripts/verify_project_execution_roadmap.sh`
- 수정 금지 파일:
  - DB migrations
  - application runtime code
  - benchmark/scoring formula
  - secrets/env files
- 검증에 사용할 명령:
  - `bash -n scripts/verify_project_execution_roadmap.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task project-execution-roadmap`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`
  - `git diff --check`

## Deliverables

- 필수 결과물:
  - `docs/project-execution-roadmap.md`
  - task contract/plan/handoff/review
  - verification script
  - updated repo map and verification plan

## Completion Criteria

- [x] 현재 구현 상태와 미완료 영역이 문서화된다.
- [x] 우선순위 1부터 6까지 고정된다.
- [x] immediate next task가 `frontend-live-read-expansion`으로 명시된다.
- [x] 하네스 검증이 통과한다.

## Risks

- roadmap이 너무 상세하면 다시 구현 대신 문서 작업으로 흐를 수 있다.
- roadmap은 방향을 고정하지만 구현 완료를 의미하지 않는다.
