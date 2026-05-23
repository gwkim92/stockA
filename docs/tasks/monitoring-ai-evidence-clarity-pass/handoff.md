# Session Handoff

## Current Status

- 상태: completed
- completed: 수집 상태와 뉴스 AI 근거 화면의 사용자-facing 문구 정리, EC2 배포, 핵심 라우트 스모크 확인을 완료했다.
- 기준일: 2026-05-23

## Investigation

- `/data-health`는 상단 요약은 개선되어 있으나 상세 summary와 일부 카드에 `LLM`, `validator`, `artifact`, `smoke`, `stderr`, `gate`, `pipeline`, `systemd`, `Postgres` 같은 내부 표현이 남아 있다.
- `/events/classification` switchboard에 `LLM 후보 확인`이 노출되어 있고, 1차 분류가 “AI 전 검수 단계”라는 설명이 더 선명해야 한다.
- `/ai-evidence`와 하위 화면은 후보/통과/차단의 의미는 있으나 `validator`, `confidence gate`, `provider` 같은 내부 용어가 남아 있다.
- EC2 route smoke에서 `/data-health`의 운영자 상세가 원본 실행 ID와 서버 파일 경로를 노출하던 문제가 추가로 확인되어, 화면에서는 실행 번호·증거 연결 여부·오류 로그 존재 여부로 축약했다.

## Completed

- `/data-health` 상단을 “전체 상태 → 실패 작업 → 반복 실행 → 열린 조건 → 호출 예산”으로 정리했다.
- 수집/분석별 상태 카드에 주식 캔들, 뉴스 원문, 1차 분류, Codex OAuth 분석, AI 결과 검증, 추천 신호, 보유 검토의 사용처를 명시했다.
- `/events/classification`의 수집 원장/LLM 표현을 수집 뉴스/AI 후보 표현으로 바꿨다.
- `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked`에서 후보, 통과 결과, 차단 후보 의미가 구분되도록 문구를 정리했다.
- `korean-labels.ts`에서 검증 차단, DB 저장소, 서버 반복 실행기, 자동 실행 승인 조건, 가격 API 예산 기록 번역을 보강했다.

## Verification

- `git diff --check`: 통과.
- `cd apps/web && npm run typecheck`: 통과.
- `cd apps/web && npm run build`: 통과.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task monitoring-ai-evidence-clarity-pass`: 통과.
- EC2 deploy: `/opt/stockanalysis/app`를 `6033b17`로 reset, `npm --prefix apps/web run build`, `stockanalysis-frontend-api.service`와 `stockanalysis-web.service` active 확인.
- EC2 route smoke: `/data-health`, `/events/classification`, `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked` 모두 200, 필수 문구 존재, visible text 기준 `LLM/validator/artifact/smoke/stderr/pipeline/파이프라인/관문/systemd/Postgres/top story/confidence` 누출 없음.
- Playwright snapshot: `http://127.0.0.1:13000/data-health?refresh=6033b17`에서 상단 요약과 수집/분석별 상태 카드 렌더링 확인.

## Remaining

- 전체 사이트 UX는 아직 한 번 더 큰 IA 정리가 필요하다. 이번 작업은 모니터링과 뉴스 AI 증거 화면의 문구/표현 정리에 한정했다.
- `/data-health`의 무료 API 예산은 현재 `0/0`으로 보인다. 이는 Twelve Data 예산 기록이 화면 데이터에 연결되는 방식 별도 점검이 필요하다.

## Mutable Surface

- `apps/web/src/app/data-health/page.tsx`
- `apps/web/src/app/events/classification/page.tsx`
- `apps/web/src/app/ai-evidence/page.tsx`
- `apps/web/src/app/ai-evidence/results/page.tsx`
- `apps/web/src/app/ai-evidence/blocked/page.tsx`
- `apps/web/src/components/news-event-card.tsx`
- `apps/web/src/lib/korean-labels.ts`
- `docs/tasks/monitoring-ai-evidence-clarity-pass/*`

## Exact Next Step

- exact next step: 다음 작업은 전체 IA 재정리 또는 `/data-health`의 무료 API 예산 `0/0` 표시 원인 점검 중 하나를 선택해서 새 task contract로 진행한다.
