# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: foundation-architecture
- 담당: Codex
- 날짜: 2026-04-18

## Current Status

- 완료:
  - 프로젝트 정체성과 전체 아키텍처를 `docs/project-foundation.md`에 저장했다.
  - `agent-work-harness`의 목적과 도입 범위를 검토해 `docs/agent-work-harness-evaluation.md`에 저장했다.
  - repo-level Level 1 하네스 문서를 scaffold하고 주요 placeholder를 프로젝트 내용으로 치환했다.
  - `awh verify --task foundation-architecture` 검증을 통과했다.
- 진행 중:
  - 다음 설계 작업으로 `db-schema-design` task를 진행 중이다.
- 막힌 점:
  - 데이터 소스, 대상 시장, 초기 유니버스가 아직 사용자 확정 전이다.

## Files Touched

- 생성:
  - `AGENTS.md`
  - `docs/verification-plan.md`
  - `docs/escalation-rules.md`
  - `docs/tasks/README.md`
  - `docs/tasks/foundation-architecture/contract.md`
  - `docs/tasks/foundation-architecture/handoff.md`
  - `docs/tasks/foundation-architecture/review.md`
- 수정:
  - `README.md`
  - `docs/project-foundation.md`
  - `docs/agent-work-harness-evaluation.md`
- 의도적으로 안 건드린 것:
  - 앱 코드, 테스트, 데이터 파이프라인, DB 설계

## Decisions

- 결정:
  - 하네스는 full 도입이 아니라 Level 1 중심으로 사용한다.
  - 이 프로젝트는 단순 추천 앱이 아니라 사이클 기반 중장기 투자 운영 시스템으로 정의한다.
  - 실거래 자동화는 초기 범위에서 제외한다.
- 이유:
  - 현재 단계는 장기 그린필드 설계이므로 상태 관리와 검증 기준은 필요하지만, multi-agent/automation까지는 오버헤드가 크다.

## Verification Already Run

- 명령: `/tmp/agent-work-harness/scripts/scaffold.sh default /Users/woody/ai/stockanalysis`
- 관찰한 결과: repo-level Level 1 문서가 생성되었다.

- 명령: `/tmp/agent-work-harness/scripts/new-task.sh research /Users/woody/ai/stockanalysis foundation-architecture`
- 관찰한 결과: task-level contract, handoff, review 템플릿이 생성되었다.

- 명령: `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task foundation-architecture`
- 관찰한 결과: `Task foundation-architecture passed readiness checks.`

## Still Unverified

- 항목: 다음 task의 범위 확정
- 왜 중요한가: `db-schema-design` 이후에 DDL skeleton과 데이터 파이프라인 bootstrap을 어떻게 쪼갤지 정해야 한다.

## Exact Next Step

- 다음 세션은 이것부터 시작: `docs/tasks/db-schema-design/`와 `docs/db-schema-design.md`를 읽고, MVP 우선순위 테이블을 기준으로 DDL skeleton task를 시작한다.

## Risks

- 위험:
  - 문서가 많아졌지만 실제 데이터/코드 구조는 아직 없는 상태다.
  - 초기 시장과 데이터 소스가 확정되지 않으면 DB 설계가 흔들릴 수 있다.
- 대응:
  - 다음 task에서 시장 범위와 데이터 모델을 먼저 고정한다.
  - 실거래 기능은 의도적으로 뒤로 미루고 페이퍼트레이딩 관점으로 설계를 시작한다.

## Useful Context

- 파일:
  - `docs/project-foundation.md`
  - `docs/agent-work-harness-evaluation.md`
  - `AGENTS.md`
  - `docs/verification-plan.md`
- 명령:
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo . --task foundation-architecture`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`
- 다시 찾기 싫은 배경지식:
  - 하네스 repo는 제품 런타임이 아니라 개발 운영 체계다.
  - 현재 프로젝트에는 Level 1만 도입하고, review/qa/automation은 필요해질 때만 올린다.
