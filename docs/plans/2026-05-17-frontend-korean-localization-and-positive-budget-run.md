# 2026-05-17 Frontend Korean Localization And Positive Budget Run

## Decision

로컬 live MVP의 다음 범위는 한국어 사용성 개선과 무료 provider budget의 실제 positive-budget 소비 상태 가시화로 고정한다.

## Rationale

현재 시스템은 FastAPI + Next.js + Postgres로 로컬 live MVP가 구동되지만, 화면 문구가 영어 중심이라 사용자가 운영 상태를 빠르게 판단하기 어렵다. 또한 무료 provider는 비용 제약 때문에 quota 소비가 투자 운영 리스크이므로 화면과 task handoff에 명시해야 한다.

## Scope

- cockpit UI 문구 한국어 전환
- common status/action/risk/code label helper 추가
- positive-budget 실제 호출 결과 기록
- Next.js 검증

## Out Of Scope

- schema/scoring/evaluation 변경
- broad market backfill
- scheduler host activation
- paper/live trading
