# Task Contract

## Task

- 이름: events-default-decision-scope
- 요청: `/events` 기본 화면에서 raw 원장과 투자 판단용 AI 후보가 섞여 보이는 문제를 줄인다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/events` 첫 목록은 개별 `news_event_candidate` 중심으로 보여준다.
  - 기본 목록은 낮은 신뢰도, 종목 미분류 일반 뉴스, 개인 재무성 top story 잡음을 후순위로 내린다.
  - raw 이벤트 원장은 숨기지 않고 별도 접힘 영역에서 확인할 수 있다.
  - 뉴스 묶음 근거와 미검토 raw row를 개별 AI 후보처럼 읽지 않도록 문구를 정리한다.
  - 기존 `/api/events` contract와 DTO shape는 바꾸지 않는다.

## Scope

- 포함:
  - `/events` page의 기본 데이터 조회를 `news_event_candidate`와 전체 원장 조회로 분리
  - 기본 목록에서 저신뢰·무종목 broad candidate를 후순위 처리
  - metric copy와 section title을 “기본 판단 목록”과 “원장 전체” 기준으로 정리
  - raw 원장 목록을 보조 영역으로 이동
  - Next.js typecheck/build와 EC2 render smoke
- 제외:
  - DB schema 변경
  - API DTO 변경
  - 뉴스 provider/source filtering 변경
  - 추천 점수 산식 변경
  - scheduler/service unit 변경
  - 실거래 또는 broker order flow

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/events/page.tsx`
  - `docs/tasks/events-default-decision-scope/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations/schema
  - scheduler systemd units or host launch agents
  - recommendation scoring weights

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task events-default-decision-scope`
  - EC2 `/events` render smoke

## Done Criteria

- [ ] `/events` 기본 목록은 개별 AI 후보를 우선 보여준다.
- [ ] `/events` 기본 목록은 저신뢰 broad/no-symbol 후보를 먼저 보여주지 않는다.
- [ ] `/events` raw 원장은 접힘 영역에서 확인할 수 있다.
- [ ] 페이지 문구가 “무엇을 봐야 하는지”를 명확히 설명한다.
- [ ] local verification과 EC2 render smoke가 통과한다.
