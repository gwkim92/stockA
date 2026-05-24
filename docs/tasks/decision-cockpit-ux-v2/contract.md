# Task Contract

## Task

- 이름: decision-cockpit-ux-v2
- 요청: 홈, 데이터 상태, 인텔리전스, 사이클맵, 페이퍼 거래 화면을 "오늘 무엇을 봐야 하는가" 중심으로 재구성한다.
- 담당: Codex
- 날짜: 2026-05-24

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 투자자가 첫 화면과 핵심 상세 화면에서 `수집 상태 -> 뉴스/AI 근거 -> 상위 흐름 -> 추천/보유 -> 페이퍼 안전` 순서로 무엇을 확인해야 하는지 이해할 수 있다.

## Scope

- 포함:
  - 공통 판단 흐름 컴포넌트 추가
  - `/`, `/data-health`, `/intelligence`, `/cycle-map`, `/paper-trading` 상단 정보 구조 정리
  - 운영자 로그성 문구를 접힌 상세나 data-health 하위 영역으로 밀기
  - 페이퍼 거래가 실거래가 아니라 검증 단계임을 더 명확히 표시
  - 한국어 사용자 문구 정리
- 제외:
  - API DTO shape 변경
  - 추천 scoring weight 변경
  - DB schema 변경
  - 실거래 broker submit
  - 저장형 승인/반려 write API

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/components/*`
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/app/intelligence/page.tsx`
  - `apps/web/src/app/cycle-map/page.tsx`
  - `apps/web/src/app/paper-trading/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/decision-cockpit-ux-v2/*`
- 수정 금지 파일:
  - backend API DTO contract
  - recommendation scoring logic
  - database migrations
  - broker/order submit path
  - secret/env files

## Verification

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task decision-cockpit-ux-v2`

## Done Criteria

- 홈과 핵심 4개 상세 화면이 같은 판단 순서를 공유한다.
- 각 화면에서 "이 화면에서 먼저 볼 것"이 상단에 보인다.
- 사용자가 실거래 상태와 페이퍼 검증 상태를 혼동하지 않는다.
- 운영자/개발자용 세부 정보는 기본 판단 흐름보다 뒤에 위치한다.
- 추천 산식, 데이터 수집 주기, broker 동작은 변경하지 않는다.
