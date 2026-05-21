# frontend-operating-ui-qa-hardening handoff

## Status

- 2026-05-21 작업 진행.
- EC2 tunnel 기준 `http://127.0.0.1:13000` 실제 운영 프론트에 수정본 반영 완료.
- EC2 `stockanalysis-web.service`, `stockanalysis-frontend-api.service` active 확인.

## Implemented

- 프론트 고정 과거 날짜를 제거하고 `/cycles`, `/themes/[themeKey]`, `/portfolio/coverage`, `/performance`가 현재 운영 기준일을 조회하게 변경했다.
- 포트폴리오 커버리지 read adapter가 요청 기준일 exact snapshot만 찾던 문제를 보완했다. 요청일에 스냅샷이 없으면 요청일 이하 최신 보유 스냅샷으로 fallback한다.
- 데이터가 없는 화면은 실패처럼 보이지 않도록 empty state 설명을 추가했다.
- `RAG`, `stale`, `operating-data-profile-scheduler`, `sensitivity=`, `exposure=`, `Rule-based`, `not requested`, `skipped:*` 같은 내부 표현을 운영자용 한국어 표현으로 정리했다.
- 이벤트 원장의 약한 `same_theme` 관계는 숨기고 직접 종목/강한 관계 위주로 보이게 했다.
- SPY처럼 가격 캔들은 없지만 상위 흐름 근거가 있는 종목은 “가격 분석 화면”이 아니라 “시장 흐름 노출 화면”으로 설명한다.
- 성과 측정 화면은 성과 데이터가 없는 상태를 실패/0%가 아니라 “측정 전”으로 표시한다.

## Verification

- Local: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter` 통과.
- Local: `cd apps/web && npm run typecheck` 통과.
- Local: `cd apps/web && npm run build` 통과.
- EC2: `cd /opt/stockanalysis/app/apps/web && npm run typecheck && npm run build` 통과.
- EC2: `/opt/stockanalysis/venv/bin/python -m py_compile /opt/stockanalysis/app/src/stockanalysis/frontend/live_adapter.py` 통과.
- Playwright browser sweep: `/`, `/data-health`, `/intelligence`, `/events`, `/ai-evidence`, `/stocks`, `/stocks/SPY`, `/recommendations`, `/recommendations/recommendation-2`, `/cycles`, `/themes/MACRO_RATES_FED`, `/portfolio/coverage`, `/performance`, `/trading-readiness`, `/paper-trading`, `/remediation` 모두 HTTP 200, bad wording scan 0, server error text 0, page errors 0.
- Playwright console check: warning/error 0.

## Remaining

- `/portfolio/coverage`의 0% 커버리지는 화면 오류가 아니라 현재 운영 데이터상 4개 보유 포지션 중 3개 투자 논리 누락, 1개 성과 측정 누락 때문에 발생하는 실제 상태다.
- `/cycles`는 현재 `US_MARKET_BREADTH` 1개 사이클만 존재한다. 더 많은 테마 사이클은 추천/사이클 배치 입력 데이터가 늘어나야 한다.
- 이번 작업은 UI hardening과 read adapter fallback이다. 신규 추천 품질 개선, AI 모델 고도화, 거래 실행 로직은 건드리지 않았다.
