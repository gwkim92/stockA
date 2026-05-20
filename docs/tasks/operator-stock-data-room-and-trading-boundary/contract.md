# Task Contract

## Task

- 이름: operator-stock-data-room-and-trading-boundary
- 요청: 실제 추천 품질, AI RAG/ontology, paper trading, real trading, scheduler 실제 활성화, 데이터 수집 상황 확인실, 수집된 데이터 차트, 종목 목록/상세 화면, 사람이 이해할 수 있는 워딩을 요구했다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/stocks`에서 수집된 종목, 최신 가격, 가격 수집 범위, 추천/보유 상태를 볼 수 있다.
  - `/stocks/[symbol]`에서 수집된 가격 차트와 종목별 추천/포지션/이벤트를 볼 수 있다.
  - read-only API server가 `/api/stocks`와 `/api/stocks/{symbol}`을 live DB에서 반환한다.
  - 실거래와 scheduler 실제 활성화는 안전 조건과 승인 경계를 문서에 남긴다.

## Why

- 현재 화면은 추천/논리/성과 일부를 보여주지만, 사용자가 가장 먼저 찾는 “각 주식은 어디 있고, 수집된 가격 차트는 어디 있나”에 답하지 못한다.
- 실거래와 scheduler는 안전장치 없이 바로 켤 수 없으므로, 먼저 수집 데이터와 종목별 상태를 사람이 확인할 수 있어야 한다.
- 개발자식 DTO/runner 워딩은 운영자가 이해하기 어렵기 때문에, 화면入口부터 한국어 운용 문맥으로 정리해야 한다.

## Scope

- 수집된 canonical 가격 데이터를 사람이 확인할 수 있는 종목 목록 화면을 추가한다.
- 종목별 상세 화면에 가격 차트, 수집 범위, 최신 추천, 보유 상태, 관련 이벤트를 표시한다.
- FastAPI read-only backend DTO에 `/api/stocks`와 `/api/stocks/{symbol}`을 추가한다.
- 기존 fixture contract에도 같은 DTO 예시를 등록해 local fixture/smoke가 깨지지 않게 한다.
- 화면 워딩은 운용자가 바로 이해할 수 있는 한국어를 우선한다.

## Boundaries

- 실거래 주문 실행은 이번 slice에서 구현하거나 활성화하지 않는다. broker 선택, 계좌 권한, 주문 제한, kill switch, 감사 로그, dry-run/paper 검증, 명시적 승인 없이는 켜면 안 된다.
- scheduler 실제 `launchctl bootstrap` 또는 host LaunchAgents write는 현재 repository rule상 금지다. exact command, repo 밖 env, dry-run evidence, 사용자 명시 승인 후 별도 단계로만 진행한다.
- AI RAG/ontology는 추천 판단의 직접 결정자가 아니라 문서 해석, 이벤트 구조화, 증거 검색/요약 계층으로 다룬다. 이번 slice에서는 화면과 데이터 확인 경로를 먼저 연다.
- 추천 품질 고도화와 paper trading 체결/주문 장부는 다음 backend slice로 분리한다.

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `src/stockanalysis/frontend/pagination.py`
  - `apps/web/src/app/layout.tsx`
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/app/stocks/page.tsx`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/app/globals.css`
  - `apps/web/src/lib/frontend-api.ts`
  - `apps/web/src/lib/types.ts`
  - `docs/api/frontend/contract-index.json`
  - `docs/api/frontend/examples/stock-list.json`
  - `docs/api/frontend/examples/stock-detail.json`
  - `docs/frontend-api-contract.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `tests/test_frontend_api_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `tests/test_frontend_fixture_server.py`
  - `docs/tasks/operator-stock-data-room-and-trading-boundary/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_api_adapter tests.test_frontend_live_adapter`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`
  - `python3 -m json.tool docs/api/frontend/contract-index.json`
  - `python3 -m json.tool docs/api/frontend/examples/stock-list.json`
  - `python3 -m json.tool docs/api/frontend/examples/stock-detail.json`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - live HTTP smoke for `/api/stocks`, `/stocks`, and `/stocks/AAPL`
  - Playwright snapshot for `/stocks` and `/stocks/AAPL`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task operator-stock-data-room-and-trading-boundary`
  - `git diff --check`

## Done Criteria

- `/stocks`에서 수집된 종목, 최신 가격, 가격 수집 범위, 추천/보유 상태를 볼 수 있다.
- `/stocks/[symbol]`에서 수집된 가격 차트와 종목별 추천/포지션/이벤트를 볼 수 있다.
- read-only API server가 `/api/stocks`와 `/api/stocks/{symbol}`을 live DB에서 반환한다.
- contract index, fixture examples, unit tests, Next typecheck/build가 갱신된다.
- 남은 실거래/scheduler/AI 품질 범위와 차단 조건이 handoff에 기록된다.
