# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: foundation-architecture
- 요청: 프로젝트 방향과 전체 아키텍처를 문서로 고정하고, `agent-work-harness`의 Level 1 운영 방식을 현재 저장소에 도입한다.
- 담당: Codex
- 날짜: 2026-04-18

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 프로젝트 정체성, 전체 아키텍처, 하네스 도입 판단이 repo 문서에 저장되어 있고, 다음 세션이 task 문서만 읽고도 바로 이어서 설계를 진행할 수 있다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: 이 프로젝트는 장기 연구·개발 성격이 강하므로, 초기에 제품 정체성과 검증 기준, 작업 상태 관리 방식을 고정하지 않으면 이후 추천 로직과 데이터 구조가 흔들릴 가능성이 크다.

## Inputs

- 관련 코드: 현재 없음
- 관련 문서: `README.md`, `docs/project-foundation.md`, `docs/agent-work-harness-evaluation.md`, `/tmp/agent-work-harness/README.md`
- 이전 결정: 이 프로젝트는 단순 종목 추천기가 아니라 섹터/테마 사이클 기반 중장기 투자 운영 시스템으로 정의한다. 하네스는 full 도입이 아니라 Level 1 중심 부분 도입을 선택한다.

## Scope

- 포함: repo-level 하네스 도입, 프로젝트 방향 문서 저장, verification plan 작성, 첫 task contract/handoff 정리
- 제외: 앱 코드 구현, 데이터 소스 연동, DB 스키마 설계, 백테스트 엔진 구현, 실거래 연동

## Mutable Surface

여러 경로가 있으면 값은 다음 줄 bullet list로 적어도 된다.

- 수정 가능한 파일:
  - `README.md`
  - `AGENTS.md`
  - `docs/project-foundation.md`
  - `docs/agent-work-harness-evaluation.md`
  - `docs/verification-plan.md`
  - `docs/escalation-rules.md`
  - `docs/tasks/README.md`
  - `docs/tasks/foundation-architecture/contract.md`
  - `docs/tasks/foundation-architecture/handoff.md`
  - `docs/tasks/foundation-architecture/review.md`
- 수정 금지 파일:
  - 아직 없는 앱 코드, 테스트, 데이터 파일 전부
  - 외부 하네스 원본 저장소(`/tmp/agent-work-harness`) 내부 파일
- 검증에 사용할 명령:
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo . --task foundation-architecture`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`
  - `find docs -maxdepth 3 -type f | sort`

## Deliverables

- 필수 결과물:
  - 프로젝트 방향과 아키텍처 문서
  - 하네스 도입 평가 문서
  - repo-level Level 1 하네스 문서
  - 현재 task의 contract와 handoff
- 선택 결과물:
  - 초기 self-review 메모

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다

작업 전용 체크를 아래에 추가한다.

- [x] `project-foundation.md`에 시스템 정체성과 아키텍처가 정리되어 있다
- [x] `agent-work-harness-evaluation.md`에 Level 1 도입 판단이 기록되어 있다
- [x] repo-level 하네스 문서와 first task 문서가 채워져 있다

## Verification Plan

- 자동 검증: `awh verify`, placeholder 검색, docs 파일 목록 확인
- 수동 검증: foundation 문서와 harness 평가 문서의 내용이 현재 합의와 일치하는지 확인
- 브라우저, 로그, metric 검증: 현재 없음. 문서 단계이므로 해당 없음
- 어떤 증거가 있어야 완료로 간주하는가: 하네스 검증 통과, placeholder 없음, 핵심 문서와 task 상태가 repo에 저장되어 있어야 한다

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: 새로 추가한 하네스 문서나 task 문서만 선택적으로 되돌리고, repo-level 문서는 최소 규칙만 남기는 방향으로 단순화한다.

## Open Questions

- 질문: 첫 구현 시장을 미국으로 할지 한국으로 할지
- 답이 없을 때 적용할 임시 가정: 데이터 접근성과 장기 종목 수급을 고려해 미국 대형주 중심으로 MVP를 설계한다.

- 질문: 추천 결과를 연구 도구로 둘지 실제 운용 보조 도구로 발전시킬지
- 답이 없을 때 적용할 임시 가정: 실거래는 제외하고 페이퍼트레이딩과 의사결정 지원 중심으로 설계한다.
