# project-roadmap-reality-sync-v2 Contract

## Task Request

- request: 최근 완료한 운영 gate, internal RAG, AI evidence visibility, cycle audit, professional quality, recommendation boundary 작업을 프로젝트 로드맵과 AGENTS 기준에 반영하고 다음 실행 순서를 고정한다.

## Goal

- goal: `docs/project-execution-roadmap.md`와 `AGENTS.md`가 현재 EC2 운영 후보 상태, 완료된 guardrail/visibility 작업, 남은 전문 분석 품질 순서를 정확히 설명한다.

## Mutable Surface

- mutable surface:
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `docs/tasks/project-roadmap-reality-sync-v2/*`

## Invariants

- Do not change application code, DB schema, scoring weights, benchmark definitions, portfolio positions, broker/order flow, or secrets.
- Do not mark recommendation weight review as allowed before outcome maturity evidence exists.
- Keep live broker submit excluded.

## Scope

- Update roadmap current-state table.
- Update latest status notes with recent commits and EC2 smoke evidence.
- Replace stale remaining-task wording with the next ordered sequence.
- Update AGENTS repository instruction snapshot so future sessions do not restart already completed gates.

## Verification

- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task project-roadmap-reality-sync-v2`
- verification command: `git diff --check`

## Done Criteria

- [x] Roadmap reflects `open_gates=[]` and the latest auth/alert/RAG/evidence/audit/professional-quality work.
- [x] AGENTS reflects the same current state and next task order.
- [x] Next task sequence is fixed to professional recommendation coverage audit before UI detail expansion.
- [x] Verification passes.
