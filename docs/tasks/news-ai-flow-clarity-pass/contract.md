# Task Contract

## Task

- 이름: news-ai-flow-clarity-pass
- request: `/intelligence`, `/events`, `/ai-evidence/[id]`에서 뉴스가 왜 묶였고 어떤 종목/테마와 연결됐는지 사용자에게 직접적으로 보이게 정리한다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- goal: 뉴스/AI 화면들이 `수집 뉴스 → 1차 분류 → AI 후보 → 묶음/상세 근거 → 종목/추천 연결` 흐름으로 읽힌다.
- 사용자는 뉴스 묶음 기준, 종목 직접 연결 여부, 상위 흐름 전파 여부, 추천 입력 가능 여부를 화면에서 즉시 구분할 수 있다.
- 사용자-facing 영역에서 `원장`, `validator`, `LLM`, `artifact`, `smoke`, `stderr`, `pipeline`, `systemd`, `Postgres`, `관문` 같은 내부 용어를 제거한다.

## Scope

- 포함:
  - `/intelligence` 문구/흐름 정리
  - `/events` 문구/요약/다음 화면 안내 정리
  - `/ai-evidence/[id]` 상세 문구의 내부 용어 제거
  - task handoff/review
- 제외:
  - API response shape 변경
  - DB schema/migration
  - 뉴스 수집/AI 분석 runner 변경
  - 추천 산식 변경
  - 데이터 삭제/재수집

## Mutable Surface

- mutable surface: `apps/web/src/app/intelligence/page.tsx`, `apps/web/src/app/events/page.tsx`, `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`, `docs/tasks/news-ai-flow-clarity-pass/*`.
- 수정 금지:
  - `.env`
  - backend API contracts
  - DB migrations/schema
  - scheduler/timer 설정
  - AI provider runtime

## Acceptance Criteria

- `/intelligence`는 뉴스 처리 흐름과 묶음 기준/종목 연결 이유를 사용자 문장으로 보여준다.
- `/events`는 “수집 뉴스” 화면으로 보이고, 판단 화면이 아니라 수집/분류/AI 연결 확인 화면임을 설명한다.
- `/ai-evidence/[id]`는 추천 입력 상태와 검증 이유를 내부 용어 없이 설명한다.
- EC2에서 `/intelligence`, `/events`, 대표 `/ai-evidence/[id]`가 200으로 렌더링된다.

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task news-ai-flow-clarity-pass`
- verification command: EC2 route smoke for `/intelligence`, `/events`, representative `/ai-evidence/[id]`
- verification command: Playwright snapshot for `/intelligence`
