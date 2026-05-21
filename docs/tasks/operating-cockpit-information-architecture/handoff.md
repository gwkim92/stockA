# Session Handoff

## Active Task

- 이름: operating-cockpit-information-architecture
- 담당: Codex
- 날짜: 2026-05-21

## Current Status

- 완료:
  - 홈/헤더/분석 화면을 daily operating flow 기준으로 재정렬한다.
  - 기존 `news_event_candidate` artifact가 새 한국어 prompt template version 재실행을 막지 않도록 후보 선택 SQL을 보강한다.
  - `news_event_candidate` 후보 SQL이 하나의 이벤트를 theme/instrument join 곱으로 중복 반환하지 않도록 lateral single-pick 방식으로 보강한다.
  - EC2에 배포했고, `codex_oauth` batch로 2026-05-21 기준 남아 있던 24개 뉴스 후보를 새 한국어 prompt version으로 재생성했다.
  - 분석 지도 상단 보유 커버리지는 빈 coverage endpoint가 아니라 cockpit dashboard 운영 metric을 사용하도록 맞췄다.

## Exact Next Step

- exact next step: 다음 slice에서 `/intelligence`의 저장된 뉴스 묶음 카드와 임시 로컬 뉴스 묶음 카드 중복을 더 줄이고, AI 후보 상세 화면을 종목/추천 연결 중심으로 재배치한다.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_news_rss_ai_extract`: pass, 11 tests.
- `cd apps/web && npm run typecheck`: pass.
- `cd apps/web && npm run build`: pass.
- `git diff --check`: pass.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task operating-cockpit-information-architecture`: pass.
- EC2 deploy at `9cf96a1`: `npm --prefix apps/web run build` pass, `stockanalysis-web.service` active, `stockanalysis-frontend-api.service` active.
- `news-rss-ai-extract-run --as-of-date 2026-05-21 --provider codex_oauth --execute`: runs 38, 39, 40 succeeded. Inserted 24 new `news_event_candidate` artifacts with prompt template version `2026-05-21-ko-v2`.
- Final dry-run for the same date returned `requested_event_count: 0`, so no remaining candidates are blocked by old English artifacts.
- Browser/HTTP smoke: `/`, `/intelligence`, `/ai-evidence`, `/ai-evidence/ai-evidence-47` render through the EC2 tunnel at `http://127.0.0.1:13000`.

## Risks

- 이번 task는 UX 정보 구조와 AI 후보 재생성 boundary 작업이다. 추천 품질 산식, broker/order flow, DB schema는 바꾸지 않는다.
