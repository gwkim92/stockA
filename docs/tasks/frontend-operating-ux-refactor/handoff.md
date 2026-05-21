# Session Handoff

## Active Task

- 이름: frontend-operating-ux-refactor
- 담당: Codex
- 날짜: 2026-05-21

## Current Status

- 완료:
  - 전체 페이지를 `agent-browser`로 열어 스크린샷을 확보했다.
  - 개별 뉴스 후보 분석은 `news-rss-ai-extract-run`이 만들고, `ai.extraction_artifact.artifact_type='news_event_candidate'`에 저장되며, `/events`의 뉴스 AI 후보 링크와 `/ai-evidence/:id`에서 확인하는 구조임을 확인했다.
  - 첫 리팩터링 범위를 전역 헤더, 전역 줄바꿈/오버플로우, 주요 분석/이벤트/AI 근거 문구로 잡았다.
  - 헤더를 운영/분석/투자/거래 그룹으로 재구성했다.
  - 전역 제목/카드 텍스트의 줄바꿈과 오버플로우를 harden했다.
  - `/events`, `/intelligence`, `/ai-evidence/:id`, `/data-health`, `/remediation`, `/cycles`, 홈 화면의 주요 문구를 운영자 관점으로 정리했다.
  - `/ai-evidence` 목록 화면을 추가해 “개별 뉴스 후보 분석”의 고정 진입점을 만들었다.
  - `AI 후보` 내비게이션을 특정 artifact ID가 아니라 `/ai-evidence` 목록으로 연결했다.
  - 모바일 폭에서 `/intelligence` trace chain, `/ai-evidence/:id` trace chain, `/stocks` 종목 표가 화면 밖으로 밀리는 문제를 수정했다.
  - `news_event_candidate`의 향후 Codex OAuth 프롬프트는 사람이 읽는 자연어 필드를 한국어로 쓰도록 변경했고, prompt template version을 `2026-05-21-ko-v2`로 올렸다.

## Exact Next Step

- exact next step: 기존 영어 AI 산출물을 한국어 산출물로 바꾸려면 별도 데이터 재생성 task에서 기존 `news_event_candidate` artifact 정리와 재실행 절차를 안전하게 수행한다.

## Verification

- `cd apps/web && npm run typecheck`: pass.
- `cd apps/web && npm run build`: pass.
- `git diff --check`: pass.
- `PYTHONPATH=src python3 -m unittest tests.test_news_rss_ai_extract`: pass.
- EC2 frontend deploy completed, then browser smoke on `http://127.0.0.1:13000` passed for `/`, `/data-health`, `/intelligence`, `/events`, `/ai-evidence`, `/ai-evidence/ai-evidence-15`, `/stocks`, `/recommendations`.
- Browser smoke result: no Server Components render error, no fallback loading state, no page-level horizontal overflow on checked pages.

## Risks

- 이번 작업은 read-only frontend UX 리팩터링이며 데이터 수집, 추천 산식, 거래 실행 로직은 바꾸지 않는다.
- 이미 생성된 AI artifact 안의 영어 뉴스 제목과 영어 요약은 기존 DB 데이터다. 프롬프트 변경은 향후 생성분부터 적용된다.
- 넓은 데이터 테이블은 표 내부 가로 스크롤을 유지한다. 페이지 전체 가로 오버플로는 제거했지만, 모든 표를 카드형으로 바꾸는 작업은 별도 UX hardening slice로 남긴다.
