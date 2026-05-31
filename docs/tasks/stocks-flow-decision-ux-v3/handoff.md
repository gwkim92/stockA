# stocks-flow-decision-ux-v3 Handoff

## Status

- completed: `/stocks`와 `/stocks/[symbol]` UX copy/refactor를 구현하고 EC2 반영·route smoke까지 완료했다.

## Completed

- completed: task contract를 생성했다.
- completed: `/stocks` hero, 우선순위 카드, 종목 목록 안내를 사용자용 한국어로 다듬었다.
- completed: `/stocks/[symbol]`의 현재 결론, 투자 판단 사용 여부, 뉴스/흐름 연결, 투자 논리, 가상 매매/실거래 상태 문구를 정리했다.
- completed: 종목 상세에서 같이 렌더링되는 밸류에이션 카드의 `forecast`, `SOTP`, `footnote`, `True`, `proxy` 같은 내부 표현을 사용자용 한국어로 치환했다.
- completed: 저장 데이터에서 내려오는 `thesis`, `accumulate_candidate`, `paper validation`, `source blocker`, `fund company financial model not applicable` 같은 표현도 화면 표시 직전에 사용자용 한국어로 정리했다.
- completed: 추천 산식, 포트폴리오, DB/API, scheduler, AI batch, 실거래 주문 경계는 변경하지 않았다.

## Boundaries

- recommendation weight, scoring formula, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- API, DB schema, scheduler, AI batch는 변경하지 않는다.

## Verification Log

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task stocks-flow-decision-ux-v3`
- passed: `git diff --check`
- passed: EC2 deploy from `origin/codex/local-mvp-runtime-aws-bootstrap`, Next typecheck/build, and `stockanalysis-web.service` restart.
- passed: `http://127.0.0.1:13000/stocks`, `/stocks/SPY`, `/stocks/AAPL` returned 200.
- passed: Playwright snapshot smoke for `/stocks` confirmed `종목 지도`, `종목 우선순위`, `판단이 이미 걸린 종목부터 연다`, `종목명과 버튼으로 필요한 화면만 연다`.
- passed: Playwright snapshot smoke for `/stocks/SPY` confirmed `실거래 차단`, `가상 매매 검증`, `투자 판단 사용 여부`, `ETF·펀드라 기업 재무 모델 비적용`, `기준 시나리오`, `상승 시나리오`, and no targeted `accumulate_candidate`, `base case`, `upside case`, `confidence`, `fund company financial model not applicable`, `fund/ETF source layer`, `source blocker`, `paper validation`, `주문 경계`, `AI 근거`.
- passed: Playwright snapshot smoke for `/stocks/AAPL` confirmed `사업부 가치합산`, `재무 추정 입력`, `SEC 사업부 주석 근거`, `투자 논리 생애주기`, `가상 매매·실거래 상태`, and no targeted `SOTP`, `재무 forecast`, `footnote`, `True`, `False`, `단일 기간 proxy`, `Thesis`, `paper validation`, `주문 경계`, `AI 근거`.

## Exact Next Step

- exact next step: continue page-by-page UX refactor with recommendation detail or portfolio coverage pages, because stock pages now route users into those decision views.
