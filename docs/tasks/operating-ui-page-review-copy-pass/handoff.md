# Session Handoff

## Current Status

- 상태: deployed_and_smoked
- 기준일: 2026-05-22
- 완료:
  - 이전 패스에서 뉴스 원문/화면 해석 분리는 `/intelligence`, `/events`, `/ai-evidence`, `/stocks/[symbol]`에 적용됐다.
  - 이번 패스는 추천 상세와 원천 문서 상세까지 같은 기준을 확장한다.
  - 추천 상세의 직접 뉴스/상위 흐름 근거를 `NewsTitleBlock`으로 바꿔 원문 제목과 화면 해석을 분리했다.
  - 원천 문서 상세의 문서 제목과 연결 AI 근거 제목도 `NewsTitleBlock`으로 바꿨다.
  - “이 화면은...” 방어적 문구와 `broker/order flow` 같은 내부 표현을 주요 화면에서 줄였다.
  - backend guardrail copy도 `가상 거래(Paper) 미리보기 단계`, `거래 안전 상태를 점검하는 읽기 전용 단계`로 바꿨다.

## Page Review Notes

- route smoke: `/`, `/data-health`, `/intelligence`, `/events`, `/ai-evidence`, `/ai-evidence/ai-evidence-122`, `/stocks`, `/stocks/SPY`, `/recommendations`, `/recommendations/recommendation-52`, `/paper-trading`, `/trading-readiness`, `/cycles`, `/performance`, `/portfolio/coverage`, `/remediation`, `/theses/thesis-1`, `/themes/MACRO_RATES_FED`, `/source-documents/rss%3Amarketwatch-topstories%3Aae287c437c18fe4949bd5a99` 모두 200.
- 확인된 개선: `/recommendations/recommendation-52`는 이제 `원문 제목`, `화면 해석`을 포함한다.
- 확인된 개선: `/paper-trading`, `/trading-readiness` route body에서 검색어 `이 화면은`, `broker/order`, `fallback 사용`이 사라졌다.
- 남은 문제 1: 홈(`/`)은 여전히 “오늘의 운용 순서” 중심이라 첫 사용자가 전체 시스템 구조를 짧게 이해하기에는 약하다. 다음 pass에서 “지금 상태/뉴스 근거/추천/거래 안전” 4개 랜딩 카드로 더 단순화하는 것이 좋다.
- 남은 문제 2: `/data-health`는 정보량이 많다. 자동화 상태는 좋지만 일반 사용자는 systemd/profile/timer 세부를 한 번에 보기 어렵다. “정상/주의/실패” 요약 후 상세 접기 구조가 필요하다.
- 남은 문제 3: `/source-documents/[id]`는 원문 제목 분리는 됐지만 발췌 요약 자체가 영어일 수 있다. 이는 UI 문제가 아니라 저장된 요약 데이터 품질 문제라, 다음 단계에서 AI 한국어 summary artifact를 별도 필드로 저장하는 것이 맞다.
- 남은 문제 4: `/themes/[themeKey]`, `/cycles`, `/performance`는 200이지만 투자자가 다음 행동을 결정하기 위한 CTA가 약하다. 현재는 상태판에 가깝고 “그래서 뭘 볼지”가 덜 분명하다.

## Verification Log

- PASS: local `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v`.
- PASS: local `cd apps/web && npm run typecheck && npm run build`.
- PASS: local `git diff --check`.
- PASS: local `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task operating-ui-page-review-copy-pass`.
- PASS: commit/push `4e52efa`, then `83258a6`.
- PASS: EC2 pull to `83258a6`.
- PASS: EC2 `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter -v`.
- PASS: EC2 `stockanalysis-frontend-api.service` and `stockanalysis-web.service` active.
- PASS: local tunnel route smoke for 19 routes all returned 200.

## Exact Next Step

- exact next step: simplify `/` and `/data-health` information architecture so the first view answers “정상인가, 무엇이 중요 뉴스인가, 어떤 종목을 볼까, 거래는 막혀 있나” without exposing implementation details first.
