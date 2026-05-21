# Session Handoff

## Active Task

- 이름: frontend-recommendation-index-flow
- 담당: Codex
- 날짜: 2026-05-21

## Current Status

- 완료:
  - `/api/recommendations` contract/example을 추가했다.
  - live adapter에 recommendation list SQL/DTO 변환을 추가했다.
  - pagination collection spec에 recommendation list를 등록했다.
  - Next.js `/recommendations` page를 추가하고 nav를 index route로 바꿨다.
  - focused contract, adapter, fixture, live adapter, build 검증을 진행했다.
  - EC2에 최신 commit을 배포하고 FastAPI/Next.js 서비스를 재시작했다.
  - EC2 live API와 로컬 SSH tunnel 화면에서 `/recommendations`를 확인했다.
- 막힌 점:
  - 없음.

## Exact Next Step

- exact next step: 뉴스 전용 AI evidence UX를 개선해 `/events`와 `/intelligence`에서 개별 `news_event_candidate` 근거 상세로 더 명확히 진입하게 한다.

## Verification

- `bash scripts/verify_frontend_api_contract.sh`: pass.
- `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter tests.test_frontend_api_adapter tests.test_frontend_fixture_server -v`: pass, 77 tests.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest tests.test_frontend_api_server -v`: pass, 13 tests.
- `bash scripts/verify_frontend_api_adapter.sh`: pass.
- `bash scripts/verify_frontend_fixture_server.sh`: pass.
- `cd apps/web && npm run build`: pass.
- `cd apps/web && npm run typecheck`: pass after `next build` generated `.next/types`.
- `git diff --check`: pass.
- EC2 DB direct SQL smoke for `render_frontend_recommendation_list_state_sql`: pass, returned the current live recommendation batch.
- EC2 deploy: `git pull --ff-only`, `/opt/stockanalysis/venv/bin/python -m pip install -e .`, `npm --prefix apps/web run build`, service restart all passed.
- EC2 API smoke: authorized `GET /api/recommendations` returned `count=1`, first `TSLA:recommendation-1`, quality `ready_for_human_review`.
- Local tunnel web smoke: `GET http://127.0.0.1:13000/recommendations` returned 200 and contained `추천 상황실`, `최신 추천 배치`, `추천 상세`, `종목 상세`, `AI 근거`.
- EC2 timers: 8 `stockanalysis-operating-data-*` timers listed active.
- Default `PYTHONPATH=src python3 -m unittest tests.test_frontend_api_server -v`: failed because default Homebrew Python lacks FastAPI, then passed with `/private/tmp/stockanalysis-runtime/verify-venv/bin/python`.

## Risks

- 추천 목록은 read-only view이며 추천 생성/점수 산식은 바꾸지 않는다.
- 뉴스 AI 후보별 전용 화면은 아직 개선 여지가 있다.
