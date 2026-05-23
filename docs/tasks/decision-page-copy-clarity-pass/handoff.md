# Session Handoff

## Current Status

- 상태: completed
- current status: completed
- 완료: 추천, 뉴스·AI, 가상 거래, 홈/거래 안전/사이클 대표 진입 문구를 사용자 판단 흐름 중심으로 정리했다.
- 기준일: 2026-05-23

## Investigation

- `/recommendations`의 운영 흐름에는 `스케줄러`, `Postgres` 같은 내부 구현 문구가 전면에 나온다.
- `/intelligence`에는 `artifact`, `LLM`, `cluster`, `provider` 중심 표현이 섞여 있어 사용자가 “뉴스 수집, AI 분석, 검증, 추천 연결” 상태를 바로 읽기 어렵다.
- `/paper-trading`은 paper 후보와 실제 주문 가능 상태의 구분은 있으나, “현재 무엇이 되는지/안 되는지”를 더 직접적으로 보여줄 필요가 있다.
- 홈/거래 안전/사이클의 대표 문구에도 `paper`, `브로커`, `유니버스`, `gate` 같은 내부 표현이 남아 있어 같은 용어 체계로 정리했다.

## Mutable Surface

- `apps/web/src/app/recommendations/page.tsx`
- `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
- `apps/web/src/app/intelligence/page.tsx`
- `apps/web/src/app/paper-trading/page.tsx`
- `apps/web/src/app/page.tsx`
- `apps/web/src/app/trading-readiness/page.tsx`
- `apps/web/src/app/cycles/page.tsx`
- `apps/web/src/app/theses/[thesisId]/page.tsx`
- `apps/web/src/lib/korean-labels.ts`
- `src/stockanalysis/frontend/live_adapter.py`
- `tests/test_frontend_live_adapter.py`
- `docs/tasks/decision-page-copy-clarity-pass/*`

## Implemented

- `/recommendations`는 “추천 후보”, “판단 흐름”, “뉴스·공시·AI 근거” 중심으로 수정했다.
- `/recommendations/[id]`는 점수 항목, 종목군 순위, 뉴스·AI 근거, 실제 주문 전송 차단을 사용자가 읽는 문장으로 바꿨다.
- `/intelligence`는 “수집 → 1차 분류 → AI 분석 → 검증 → 추천 연결” 흐름을 전면에 두고, 내부 `artifact`/`LLM`/`validator` 표현을 축소했다.
- `/paper-trading`은 가상 주문 검증 단계, 실제 주문 전송 0건, 실거래 전환 조건을 분리했다.
- 홈/거래 안전/사이클/보유 논리 대표 문구에서 `paper`, `브로커`, `유니버스`, `gate`, `감사 로그`를 가상 거래, 증권사 연결, 종목군, 안전 조건, 검토 기록으로 바꿨다.

## Verification

- local verification:
  - `cd apps/web && npm run typecheck`: pass
  - `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter`: pass
  - `cd apps/web && npm run build`: pass
  - `git diff --check`: pass
- EC2 route smoke: pending after commit/push/deploy.

## Exact Next Step

- exact next step: commit/push the verified wording changes, deploy to EC2, then smoke `/`, `/cycles`, `/trading-readiness`, `/intelligence`, `/recommendations`, `/recommendations/recommendation-64`, `/paper-trading`.

## Remaining

- `/data-health`, `/ai-evidence`, `/events/classification`에는 아직 운영자용 세부 용어가 남아 있다. 다음 슬라이스에서 “모니터링 화면/AI 분석 화면” 정보 구조를 별도로 정리해야 한다.
