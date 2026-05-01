# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: db-schema-design
- 요청: 투자 운영 시스템의 canonical 데이터 저장 구조를 실제 개발 가능한 수준으로 설계하고, 운영 DB와 분석용 스토어의 역할을 분리한 문서를 저장한다.
- 담당: Codex
- 날짜: 2026-04-18

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 추천, thesis, cycle state, 이벤트, 포트폴리오, 성과 추적까지 이어지는 DB 스키마가 문서로 고정되어 있고, 다음 단계에서 바로 DDL skeleton과 ingest 설계로 내려갈 수 있다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: 이 프로젝트는 데이터 수집, 이벤트 해석, 테마/사이클 추적, 추천, 보유 검토, 성과 분석이 모두 연결된 구조라서, 초기에 스키마를 잘못 잡으면 나중에 추천 기록과 검토 이력을 재구성할 수 없게 된다.

## Inputs

- 관련 코드: 현재 없음
- 관련 문서:
  - `docs/project-foundation.md`
  - `docs/verification-plan.md`
  - `docs/tasks/foundation-architecture/handoff.md`
- 이전 결정:
  - canonical 운영 저장소는 Postgres 기준으로 간다.
  - 초기 프로젝트는 중장기 투자 운영 시스템이며, 실거래 자동화는 제외한다.
  - 멀티마켓을 지원하되 MVP 운영 범위는 한 시장으로 제한한다.

## Scope

- 포함:
  - Postgres schema 구분 제안
  - 핵심 테이블 정의와 주요 컬럼 설계
  - provenance, history, feature, thesis, recommendation, portfolio, performance 저장 방식 결정
  - MVP 우선순위 테이블 세트 정의
- 제외:
  - 실제 SQL migration 작성
  - ORM 모델 구현
  - 데이터 공급자별 필드 매핑 구현
  - 백테스트 엔진 구현

## Mutable Surface

여러 경로가 있으면 값은 다음 줄 bullet list로 적어도 된다.

- 수정 가능한 파일:
  - `README.md`
  - `docs/db-schema-design.md`
  - `docs/tasks/db-schema-design/contract.md`
  - `docs/tasks/db-schema-design/plan.md`
  - `docs/tasks/db-schema-design/handoff.md`
  - `docs/tasks/db-schema-design/review.md`
  - `docs/tasks/foundation-architecture/handoff.md`
- 수정 금지 파일:
  - 아직 없는 앱 코드와 migration 파일
  - 외부 하네스 원본 저장소(`/tmp/agent-work-harness`) 내부 파일
- 검증에 사용할 명령:
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task db-schema-design`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
  - `find /Users/woody/ai/stockanalysis/docs -maxdepth 3 -type f | sort`

## Deliverables

- 필수 결과물:
  - `docs/db-schema-design.md`
  - `docs/tasks/db-schema-design/contract.md`
  - `docs/tasks/db-schema-design/plan.md`
  - `docs/tasks/db-schema-design/handoff.md`
- 선택 결과물:
  - `docs/tasks/db-schema-design/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다

작업 전용 체크를 아래에 추가한다.

- [x] 운영용 canonical DB와 분석용 스토어의 역할이 분리되어 있다
- [x] 이벤트, 사이클, thesis, recommendation, portfolio, performance 흐름이 하나의 스키마로 연결된다
- [x] MVP 우선순위 테이블 세트가 정의되어 있다

## Verification Plan

- 자동 검증: `awh verify --task db-schema-design`, placeholder 검색, docs 파일 목록 확인
- 수동 검증: `docs/db-schema-design.md`가 foundation 문서의 아키텍처 요구사항을 실제 테이블 구조로 충분히 내려서 설명하는지 검토
- 브라우저, 로그, metric 검증: 현재는 문서 설계 단계라 해당 없음
- 어떤 증거가 있어야 완료로 간주하는가: task readiness 검증 통과, placeholder 없음, 스키마 문서에 테이블/관계/우선순위가 명시되어 있어야 한다

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: 스키마 문서를 더 작은 MVP 집합으로 축소하고, 불확실한 테이블은 deferred decisions로 이동한다.

## Open Questions

- 질문: 벤치마크를 종목/ETF로만 표현할지 별도 엔터티로 모델링할지
- 답이 없을 때 적용할 임시 가정: MVP에서는 `benchmark_code` 텍스트 또는 `instrument` 기반 표현으로 충분하다고 본다.

- 질문: full text 검색과 embedding 저장을 운영 DB에 둘지 분리할지
- 답이 없을 때 적용할 임시 가정: 운영 DB에는 메타데이터와 포인터만 두고, 대규모 본문 검색/embedding은 나중에 분리한다.
