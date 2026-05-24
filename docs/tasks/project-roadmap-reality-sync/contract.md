# Task Contract

## Task

- 이름: project-roadmap-reality-sync
- 요청: 현재 EC2/systemd 운영 후보와 계층형 사이클/AI 구현 상태에 맞게 프로젝트 로드맵과 에이전트 작업 기준을 현실 동기화한다.
- 담당: Codex
- 날짜: 2026-05-24

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `AGENTS.md`, `docs/project-execution-roadmap.md`, 검증 스크립트가 더 이상 Supabase/local-first를 immediate next로 강제하지 않고, 다음 순서를 `quality-and-evaluation-hardening`으로 고정한다.

## Scope

- 포함:
  - 현재 구현 상태와 gap을 roadmap에 명시
  - 다음 5개 task 순서 고정
  - stale immediate next task 정리
  - roadmap verification script 갱신
  - 관련 task handoff 정리
- 제외:
  - 신규 runtime 배포 대상 변경
  - scoring weight 변경
  - broker live submit 활성화
  - 유료 외부 RAG/Graph/vector DB 도입

## Mutable Surface

- 수정 가능한 파일:
  - `AGENTS.md`
  - `docs/project-execution-roadmap.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/project-roadmap-reality-sync/*`
  - 관련 stale handoff 문서
- 수정 금지 파일:
  - `.env` secret values
  - EC2 runtime env files
  - DB schema
  - recommendation scoring formula

## Verification

- 검증에 사용할 명령:
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task project-roadmap-reality-sync`

## Done Criteria

- `AGENTS.md` immediate next가 `quality-and-evaluation-hardening`으로 바뀐다.
- roadmap immediate next가 EC2/systemd reality, current state, gap, next 5 tasks를 설명한다.
- verification script가 새 immediate next를 검증한다.
- task handoff가 다음 사람이 이어받을 수 있을 정도로 남는다.
