# Session Handoff

## Current Status

- 상태: completed
- completed: `/` 첫 화면의 정보 구조와 사용자-facing 문구를 정리하고 EC2 배포/브라우저 스모크를 완료했다.
- 기준일: 2026-05-23

## Investigation

- 첫 화면은 이미 “오늘의 운용 순서” 구조가 있으나 `파이프라인`, `뉴스 원장` 같은 내부 표현이 남아 있다.
- hero와 하단 “오늘의 핵심 판단”이 일부 중복되어, 사용자가 첫 화면에서 무엇을 눌러야 하는지 더 선명하게 만들 필요가 있다.
- 현재 가장 중요한 사용 흐름은 `수집 상태 확인 → 뉴스/AI 근거 확인 → 영향 종목 확인 → 추천/보유 검토 → 거래 안전 확인`이다.
- Playwright 확인 중 “첫 검토” 제목이 실제 조치와 무관하게 `투자 논리 공백`으로 고정되는 문제가 발견되어, 실제 `firstTicket.action` 기반 제목과 짧은 사유 문장으로 수정했다.

## Completed

- hero 제목을 “오늘 볼 것은 수집, 근거, 안전이다.”로 바꿔 첫 화면의 목적을 고정했다.
- 현재 결론 카드에 “지금 할 일”과 바로 갈 수 있는 CTA를 추가했다.
- 점검 순서를 `수집 → 뉴스 AI → 종목 → 추천/보유 → 거래 안전`으로 유지하면서 각 카드의 문구를 사용자 판단 기준으로 정리했다.
- 상세 화면 입구에서 `뉴스 원장`을 `수집 뉴스`로 바꾸고 내부 용어를 제거했다.
- 우선순위 표와 첫 검토 카드의 긴 시스템 사유를 “단일 종목 비중이 검토 기준보다 높다.” 같은 짧은 사유로 축약했다.

## Verification

- `git diff --check`: passed.
- `cd apps/web && npm run typecheck`: passed.
- `cd apps/web && npm run build`: passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task homepage-ia-clarity-pass`: passed.
- EC2 deploy: app reset to `cb911f2`, Next build passed, `stockanalysis-frontend-api.service` and `stockanalysis-web.service` active.
- EC2 `/` route smoke: 200, required text present, visible text leak check empty for `파이프라인`, `뉴스 원장`, `LLM`, `validator`, `artifact`, `smoke`, `stderr`, `systemd`, `Postgres`.
- Playwright snapshot: `http://127.0.0.1:13000/?refresh=cb911f2` shows hero, current action CTA, 5-step check sequence, route entry cards, simplified review reasons.

## Remaining

- 상세 페이지 전체 IA는 아직 다음 작업으로 남아 있다. 특히 `/intelligence`, `/events`, `/ai-evidence/[id]`, `/stocks/[symbol]`, `/recommendations/[id]`의 정보 흐름을 이어서 정리해야 한다.
- 현재 홈의 데이터 상태가 “주의 필요”로 보이는 이유는 실패 작업이 아니라 운영 전제/open condition 쪽일 가능성이 있어 별도 데이터 상태 의미 정리가 필요하다.

## Mutable Surface

- `apps/web/src/app/page.tsx`
- `apps/web/src/app/globals.css`
- `docs/tasks/homepage-ia-clarity-pass/*`

## Exact Next Step

- exact next step: 다음 작업은 뉴스/AI 상세 흐름(`/intelligence`, `/events`, `/ai-evidence/[id]`)을 한 묶음으로 정리해, 뉴스가 왜 묶였고 어떤 종목과 연결됐는지 더 직접적으로 보이게 한다.
