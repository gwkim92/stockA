# Session Handoff

## Current Status

- 완료: 첫 화면 정보 구조 정리, paper 거래 상태 문구 보강, 뉴스 카드 문구 보정, `/data-health` 요약 우선 구조, `/intelligence` 묶음 설명 보강, 로컬/EC2 검증 완료.
- 기준일: 2026-05-22

## Implemented

- `/` 첫 화면에서 중복되던 12개 기능 지도와 하단 상세 화면 반복 목록을 제거했다.
- `/` 첫 화면을 “오늘의 점검 순서”, “상세 화면 입구”, “오늘의 핵심 판단”으로 정리했다.
- 상세 화면 입구는 세 그룹으로 묶었다:
  - 수집/분석 상태
  - 뉴스/종목 관계
  - 판단/거래 안전
- `/paper-trading` 상단 문구를 “현재는 실거래가 아니라 Paper 검증 단계”로 명확히 바꿨다.
- `/paper-trading` 현재 단계 카드에 가상 후보 생성, 실제 주문 제출, Paper 검증, 실거래 전환 조건을 분리 표시했다.
- 뉴스 카드의 “종목 미분류”를 “시장/테마 뉴스”로 바꿔 거시/테마 뉴스가 오류처럼 보이지 않게 했다.
- 뉴스 카드 버튼 문구를 `종목 상세`, `테마 흐름`, `원문`으로 구체화했다.
- `/data-health`에 사용자용 판단 카드 3개를 추가했다: 지금 판단, 자동화, 무료 API 예산.
- `/data-health`의 운영자용 상세, 실행 로그, 예산 상세를 접힘 패널로 이동해 첫 화면에서 로그처럼 보이지 않게 했다.
- `/intelligence` 뉴스 묶음 카드에 `묶인 기준`, `종목 관계`, `추천 영향` 설명을 추가했다.
- `/intelligence`에서 직접 종목 뉴스와 시장/테마 흐름 뉴스가 왜 다르게 연결되는지 카드 상단에서 먼저 보이게 했다.

## Verification

- 통과: local `cd apps/web && npm run typecheck`
- 통과: local `cd apps/web && npm run build`
- 통과: local `git diff --check`
- 통과: EC2 deploy to commit `ff33094`
- 통과: EC2 deploy to commit `2e06379`
- 통과: EC2 `npm --prefix apps/web run typecheck`
- 통과: EC2 `npm --prefix apps/web run build`
- 통과: EC2 `stockanalysis-frontend-api.service` active, `stockanalysis-web.service` active
- 통과: EC2 route smoke returned HTTP `200` for `/`, `/data-health`, `/intelligence`, `/events`, `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked`, `/stocks`, `/recommendations`, `/paper-trading`, `/trading-readiness`
- 통과: rendered HTML contains:
  - `첫 화면에서는 세 가지 질문만 확인한다`
  - `데이터가 믿을 만한가`
  - `뉴스가 어디에 영향을 주나`
  - `추천을 실행해도 되는가`
  - `현재는 실거래가 아니라 Paper 검증 단계다`
  - `실거래 전환 조건`
- 통과: rendered HTML contains:
  - `데이터 수집 판단 요약`
  - `운영자용 상세 보기`
  - `실행 로그와 예산 상세`
  - `묶인 기준`
  - `종목 관계`
  - `추천 영향`
- 통과: Playwright snapshot verified `/` and `/paper-trading` through the EC2 tunnel at `http://127.0.0.1:13000`.
- 통과: Playwright snapshot verified `/data-health` and `/intelligence` through the EC2 tunnel at `http://127.0.0.1:13000`.

## Remaining Work

- `/ai-evidence/[id]`는 근거가 많지만 여전히 사용자가 어떤 증거를 우선 봐야 하는지 압축이 필요하다.
- `/intelligence`는 카드별 설명은 개선됐지만, 일부 기존 뉴스 묶음은 상위 테마 분류 품질 자체를 더 개선해야 한다.
- `/recommendations/[id]`와 `/stocks/[symbol]`에서 뉴스 -> 상위 흐름 -> 종목 -> 추천 점수 경로를 더 짧은 문장으로 정리해야 한다.
- Paper 거래 테이블은 후보가 많아 보일 수 있다. 다음 slice에서 “실제 조치 필요”, “관찰”, “문제 없음”으로 필터를 나눈다.

## Exact Next Step

- exact next step: `/stocks/[symbol]`, `/recommendations/[id]`, `/ai-evidence/[id]`에서 뉴스 -> 상위 흐름 -> 종목 -> 추천 점수 경로를 더 짧은 사용자 문장으로 정리하고, 기존 뉴스 묶음의 상위 테마 오분류 잔여 케이스를 추가 점검한다.
