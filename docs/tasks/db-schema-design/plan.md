# Task Plan

이 문서는 guided single-agent보다 더 구조화된 실행이 필요한 작업에서 사용한다.

## Task

- 이름: db-schema-design
- 요청: 투자 운영 시스템의 canonical DB 구조와 분석용 저장 구조를 설계한다.
- 담당: Codex
- 날짜: 2026-04-18

## Goal

- 이 작업이 끝났을 때 달성되어야 하는 상태: foundation 문서의 개념적 아키텍처가 실제 테이블, 관계, provenance, MVP 우선순위까지 포함한 데이터 모델 문서로 내려와 있다.

## Why This Needs A Plan

- 왜 `contract.md`만으로 부족한가: 이 작업은 단순 문서 하나 추가가 아니라, 기준정보/문서/시계열/이벤트/추천/포트폴리오/성과를 한 번에 연결하는 설계이므로 구조적 단계와 tradeoff를 먼저 잠그는 편이 안전하다.

## Architecture Or Approach

- 접근 방식:
  - `foundation` 문서의 레이어를 데이터 관점으로 재해석한다.
  - canonical 상태는 Postgres에 두고, 대량 연구용 계산은 Parquet/DuckDB 보조 스토어로 분리한다.
  - stable concept는 typed table로, 실험적 provenance는 JSONB로 제한한다.
- 핵심 tradeoff:
  - 지나치게 범용적인 polymorphic 구조를 피하고, 중복이 조금 생기더라도 관계형 무결성이 강한 쪽을 택한다.
- 피해야 할 함정:
  - 모든 걸 giant JSON table로 저장하는 설계
  - 추천 기록과 이후 성과가 연결되지 않는 설계
  - 현재 상태만 저장하고 history를 잃는 설계

## Milestones

### Milestone 1

- 목표: 저장 토폴로지와 schema 분리를 결정한다.
- 산출물: `docs/db-schema-design.md`의 storage topology, schema inventory 초안
- 검증: foundation 문서의 레이어가 schema 단위로 모두 대응되는지 수동 확인

### Milestone 2

- 목표: 핵심 테이블과 관계를 정의한다.
- 산출물: 기준정보, ingest, market, macro, event, signal, portfolio, performance, ops 테이블 정의
- 검증: 이벤트 -> 사이클 -> thesis -> recommendation -> portfolio -> performance 연결이 문서에서 끊기지 않는지 수동 검토

### Milestone 3

- 목표: MVP 우선순위와 다음 구현 순서를 정한다.
- 산출물: MVP table set, deferred decisions, recommended next step
- 검증: 다음 task가 DDL skeleton 또는 ingest bootstrap으로 바로 이어질 수 있는지 확인

## Dependencies

- 선행 조건:
  - `foundation-architecture` task 완료
  - `docs/project-foundation.md` 존재
- 순서 제약:
  - storage topology 결정 없이 테이블 정의로 바로 내려가지 않는다
  - provenance 정책 결정 없이 signal/performance 테이블을 설계하지 않는다

## Ownership

- 한 번에 누가 무엇을 책임지는가: 현재는 단일 agent가 문서 초안, 관계 정리, 위험 평가를 모두 책임진다.
- 병렬 가능한가: 지금 단계에서는 병렬화 이득이 작아 단일 흐름이 낫다.

## Checkpoints

- 언제 상태를 다시 평가할 것인가: schema inventory 초안이 나온 뒤 한 번, MVP table set을 정한 뒤 한 번
- 언제 handoff를 갱신할 것인가: 설계 문서 저장 직후

## Verification Gates

- milestone별 통과 조건:
  - topology가 명확하다
  - 핵심 테이블이 문서화되어 있다
  - MVP 우선순위가 정리되어 있다
- 최종 통과 조건:
  - `awh verify --task db-schema-design` 통과
  - placeholder 없음
  - 다음 단계가 DDL skeleton으로 이어질 수 있다

## Rollback

- 어느 지점까지 되돌릴 수 있는가: schema 구성이 과도하다고 판단되면 `performance/ops` 일부와 우선순위 3 영역을 deferred decisions로 밀어낼 수 있다.

## Open Questions

- 질문:
  - portfolio와 trade 모델을 초기 MVP부터 넣을지 recommendation outcome만으로 시작할지
- 임시 가정:
  - 페이퍼트레이딩과 보유 검토가 핵심이므로 최소 `portfolio`, `position_snapshot`은 MVP에 포함한다.
