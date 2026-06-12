# Task Contract

## Task

- 이름: cross-asset-market-map-validation-v1
- 요청: `/market-map`이 지수·금리·달러·원자재·변동성 흐름을 투자 판단용으로 제대로 보여주는지 검증하고, 부족한 UX/UI·문구·데이터 배치를 개선한다.
- 담당: Codex
- 날짜: 2026-06-12

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/market-map`이 “오늘 시장에서 무엇을 먼저 봐야 하는가”를 상단에서 명확히 말하고, 시장 지표 묶음·시장 체제·뉴스 연결·추천 영향·데이터 품질을 사용자용 한국어로 구분해 보여준다.

## Why

- cross-asset 수집과 스케줄은 정상화됐지만, 화면이 투자자가 판단 순서를 이해하게 만들지 못하면 데이터가 쌓여도 의미가 없다.
- 이 프로젝트 목표는 거시·섹터·테마·종목 사이클을 연결하는 중장기 투자 운영 시스템이므로, 시장 지도는 사이클/추천 화면으로 들어가는 첫 관문이어야 한다.

## Scope

- 포함:
  - `/market-map` 실제 화면/API 점검
  - 시장 압력·체제·뉴스 연결·추천 영향·품질 경고의 정보 구조 개선
  - 사용자용 한국어 문구 개선
  - route smoke와 Next.js 검증
  - task handoff 기록
- 제외:
  - DB schema 변경
  - provider/API 추가
  - 추천 scoring weight 변경
  - broker/order flow
  - production secret/env 변경

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/market-map/page.tsx`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/frontend-api.ts`
  - 관련 frontend tests 또는 smoke script
  - `docs/tasks/cross-asset-market-map-validation-v1/`
- 수정 금지 파일:
  - repo 밖 runtime env/secrets
  - `db/migrations/`
  - recommendation scoring/benchmark/evaluation split
  - broker/order implementation

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task cross-asset-market-map-validation-v1`
  - EC2/local route smoke: `/market-map`, `/data-health`, `/cycle-map`

## Completion Criteria

- [ ] `/market-map` 상단에서 현재 시장 상태, 우선 확인 영역, 다음 행동이 즉시 보인다.
- [ ] 지표 묶음과 regime이 중복 문구 없이 구분된다.
- [ ] 뉴스-지표 연결은 인과 단정이 아니라 동시 근거 후보임을 명확히 표시한다.
- [ ] 데이터 stale/missing은 투자 판단에서 어떻게 제외되는지 보인다.
- [ ] Next.js typecheck/build와 route smoke가 통과한다.

