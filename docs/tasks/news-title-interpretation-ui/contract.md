# Task Contract

## Task

- 이름: news-title-interpretation-ui
- 요청: 영어 원문 뉴스 제목과 raw 코드가 투자 판단 화면을 흐리지 않도록, 원문 제목과 한국어 해석/분류를 분리해 표시한다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 뉴스 제목을 그대로 한국어 제목처럼 보여주지 않는다.
  - 영어 원문 뉴스는 `원문 제목`으로 명확히 표시한다.
  - AI 요약이 있는 화면은 요약을 우선 보여주고 원문 제목을 보조 정보로 둔다.
  - AI 요약이 없는 화면은 종목, 테마, 영향 방향, 영향도 기반의 한국어 `화면 해석`을 함께 표시한다.
  - 데이터 계약과 DB schema는 바꾸지 않는다.

## Scope

- 포함:
  - 공용 뉴스 제목 표시 컴포넌트 추가
  - `/ai-evidence`, `/events`, `/intelligence`, `/ai-evidence/[evidenceId]`, `/stocks/[symbol]` 적용
  - long title overflow 대응 CSS 추가
  - task handoff 및 검증 기록 갱신
- 제외:
  - LLM 번역 batch 추가
  - DB schema/API contract 변경
  - 추천 점수 산식 변경
  - 원문 제목 삭제

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/components/news-title-block.tsx`
  - `apps/web/src/app/globals.css`
  - `apps/web/src/app/ai-evidence/page.tsx`
  - `apps/web/src/app/events/page.tsx`
  - `apps/web/src/app/intelligence/page.tsx`
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `docs/tasks/news-title-interpretation-ui/*`
- 수정 금지 파일:
  - DB migrations/schema
  - backend API contract
  - scheduler cadence
  - recommendation scoring
  - secrets/env files

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task news-title-interpretation-ui`

## Done Criteria

- [ ] 공용 뉴스 제목 표시가 추가된다.
- [ ] 주요 뉴스 화면에서 원문 제목과 한국어 해석이 분리된다.
- [ ] 긴 영어 제목이 레이아웃을 깨지 않는다.
- [ ] 로컬 검증이 통과한다.
- [ ] EC2 배포와 route smoke가 통과한다.
