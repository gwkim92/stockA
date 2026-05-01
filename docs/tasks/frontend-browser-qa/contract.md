# Task Contract

## Task

- 이름: frontend-browser-qa
- 요청: `apps/web` 프론트엔드의 주요 화면을 실제 브라우저에서 확인하고, 발견된 시각/정적 자산 문제를 수정한다.
- 담당: Codex
- 날짜: 2026-05-01

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 홈, recommendation detail, thesis detail, portfolio coverage 화면이 fixture API 기반으로 브라우저에서 열리고 콘솔 오류 없이 렌더링된다.

## Scope

- 포함:
  - Playwright 기반 브라우저 smoke QA
  - missing favicon/static icon 보강
  - review queue action row overflow 수정
  - 로컬 브라우저 산출물 ignore 처리
  - QA 증거와 handoff 기록
- 제외:
  - 도메인 DTO 변경
  - live DB adapter
  - auth/RBAC
  - write endpoint
  - 투자 추천 로직 변경

## Mutable Surface

- 수정 가능한 파일:
  - `.gitignore`
  - `apps/web/src/app/layout.tsx`
  - `apps/web/src/app/globals.css`
  - `apps/web/src/app/icon.svg`
  - `docs/tasks/frontend-browser-qa/`
  - `docs/tasks/frontend-detail-routes/handoff.md`
  - `docs/tasks/frontend-detail-routes/review.md`
- 수정 금지 파일:
  - DB migrations
  - secrets
  - live trading integrations
  - scoring/evaluation benchmark
- 검증에 사용할 명령:
  - `bash scripts/verify_frontend_detail_routes.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-browser-qa`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`
  - Playwright CLI browser smoke for `/`, `/recommendations/AAPL-2024-11-01`, `/theses/AAPL-bootstrap-v1`, `/portfolio/coverage`

## Completion Criteria

- [x] 브라우저에서 홈 화면이 콘솔 오류 없이 열린다.
- [x] 브라우저에서 recommendation detail 화면이 콘솔 오류 없이 열린다.
- [x] 브라우저에서 thesis detail 화면이 콘솔 오류 없이 열린다.
- [x] 브라우저에서 portfolio coverage 화면이 콘솔 오류 없이 열린다.
- [x] favicon/static icon 404가 재현되지 않는다.
- [x] review queue action row가 데스크톱/모바일 폭에서 텍스트 겹침 없이 렌더링된다.
- [x] 정식 verification script와 AWH 검증을 최신 변경 기준으로 다시 통과시킨다.

## Risks

- Playwright 확인은 fixture server와 Next dev server 기준이다. production build smoke는 `scripts/verify_frontend_detail_routes.sh`로 별도 보완한다.
- Next dev indicator는 개발 서버에서만 보이는 overlay라 production UI 판단 대상에서 제외한다.
