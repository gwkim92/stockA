# Task Contract

## Task

- 이름: full-site-ia-regression-pass
- request: 전체 주요 화면을 실제 사용자 동선으로 순회해 중복, 어색한 문구, 빈 값, 에러성 표시를 정리한다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- goal: 홈에서 시작해 수집, 뉴스·AI, 종목, 추천·보유, 거래 안전까지 한 번에 이해되는 정보 구조를 만든다.
- 사용자는 첫 화면에서 지금 볼 것과 다음 행동을 알 수 있다.
- 각 주요 화면은 내부 용어 대신 사용자 문장으로 상태, 근거, 다음 조치를 설명한다.
- 빈 값, 에러처럼 보이는 값, 중복된 안내 문구를 줄인다.

## Scope

- 포함:
  - 배포된 EC2 화면 기준 visible text 점검
  - 홈, 수집, 뉴스·AI, 종목, 추천·보유, 거래 안전 주요 동선 점검
  - 발견된 사용자-facing 문구/링크/empty state/중복 표시 수정
  - task handoff/review
- 제외:
  - API response shape 변경
  - DB schema/migration
  - scheduler cadence 변경
  - AI runtime/provider 변경
  - broker/order execution logic 변경

## Mutable Surface

- mutable surface: `apps/web/src/app/**/page.tsx`, `apps/web/src/components/*`, `apps/web/src/lib/korean-labels.ts`, `docs/tasks/full-site-ia-regression-pass/*`.
- 수정 금지:
  - `.env`
  - backend API contracts
  - DB migrations/schema
  - scheduler/timer 설정
  - broker/order execution logic

## Acceptance Criteria

- 주요 라우트가 200으로 렌더링된다.
- visible text에서 `Server Components render`, `투자 운영 데이터를 불러오지 못했다`, `pipeline`, `systemd`, `Postgres`, `stderr`, `artifact`, `smoke`, `validator`, `RAG`, `LLM`, `secret`, `원장`, `문서 조각`, `검색 준비`, `품질 점검`, `관문` 같은 내부/에러성 표현이 노출되지 않는다.
- 홈, 수집, 뉴스·AI, 종목, 추천·보유, 거래 안전 흐름에서 중복 CTA와 어색한 empty state를 발견하면 정리한다.

## Verification Commands

- verification command: `git diff --check`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task full-site-ia-regression-pass`
- verification command: EC2 route smoke for representative top-level and detail routes
- verification command: Playwright snapshot text check for representative top-level and detail routes
