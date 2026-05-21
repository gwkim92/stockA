# Task Contract

## Task

- 이름: data-health-operating-flow-visibility
- 요청: `/data-health`에서 자동 수집/뉴스 분석/후속 의사결정 흐름과 EC2 scheduler 상태를 사람이 이해할 수 있게 보여준다.
- 담당: Codex
- 날짜: 2026-05-21

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/data-health`가 뉴스 수집 이후 이벤트 구조화, AI evidence, 신호/추천, thesis/review, 포트폴리오 검토로 이어지는 흐름을 보여준다.
  - `/data-health`가 EC2 profile scheduler timer 수, active 수, 각 timer의 다음 실행과 마지막 결과를 보여준다.
  - 화면 문구가 더 이상 “로컬 반복 실행만”을 전제로 설명하지 않고, EC2 systemd 설치 상태를 정확히 설명한다.

## Scope

- 포함:
  - Next.js `/data-health` 화면의 운영 플로우 섹션 확장
  - `DataHealthData.scheduler.profile_scheduler` 타입 정의 추가
  - scheduler/timer/뉴스 후속 단계용 한국어 라벨 보강
  - task handoff/review와 검증 증거 기록
- 제외:
  - DB schema 변경
  - API DTO shape 변경
  - scheduler 재설치/타이머 변경
  - 신규 provider/유료 API 도입
  - 추천 scoring 변경
  - broker/order submission

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/app/globals.css`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/korean-labels.ts`
  - `docs/tasks/data-health-operating-flow-visibility/*`
- 수정 금지 파일:
  - `db/migrations/`
  - `.env` or repo-inside secret files
  - `src/stockanalysis/operations/operating_data_profile_scheduler.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - broker/order implementation

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `curl -fsS -o /private/tmp/stockanalysis-runtime/data-health-operating-flow.html -w '%{http_code}' http://127.0.0.1:13000/data-health`
  - `rg "뉴스 분석 이후 운영 흐름|EC2 systemd 반복 실행기|AI evidence|추천·투자 논리" /private/tmp/stockanalysis-runtime/data-health-operating-flow.html`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task data-health-operating-flow-visibility`
  - `git diff --check`

## Done Criteria

- [x] `/data-health` has a news-after-analysis flow section.
- [x] `/data-health` has a profile scheduler timer status section.
- [x] TypeScript typecheck and build pass.
- [x] Route smoke confirms the new Korean labels render.
- [x] Handoff and review are updated.
