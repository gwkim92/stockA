# Session Handoff

## Active Task

- 이름: frontend-operating-ux-refactor
- 담당: Codex
- 날짜: 2026-05-21

## Current Status

- 진행 중:
  - 전체 페이지를 `agent-browser`로 열어 스크린샷을 확보했다.
  - 개별 뉴스 후보 분석은 `news-rss-ai-extract-run`이 만들고, `ai.extraction_artifact.artifact_type='news_event_candidate'`에 저장되며, `/events`의 뉴스 AI 후보 링크와 `/ai-evidence/:id`에서 확인하는 구조임을 확인했다.
  - 첫 리팩터링 범위를 전역 헤더, 전역 줄바꿈/오버플로우, 주요 분석/이벤트/AI 근거 문구로 잡았다.
  - 헤더를 운영/분석/투자/거래 그룹으로 재구성했다.
  - 전역 제목/카드 텍스트의 줄바꿈과 오버플로우를 harden했다.
  - `/events`, `/intelligence`, `/ai-evidence/:id`, `/data-health`, `/remediation`, `/cycles`, 홈 화면의 주요 문구를 운영자 관점으로 정리했다.

## Exact Next Step

- exact next step: EC2에 배포한 뒤 브라우저 smoke로 새 헤더와 핵심 문구가 렌더링되는지 확인한다.

## Verification

- `cd apps/web && npm run typecheck`: pass.
- `cd apps/web && npm run build`: pass.
- `git diff --check`: pass.

## Risks

- 이번 작업은 read-only frontend UX 리팩터링이며 데이터 수집, 추천 산식, 거래 실행 로직은 바꾸지 않는다.
