# Task Contract

## Task

- 이름: intelligence-page-signal-density-pass
- 요청: `/intelligence` 화면이 무엇을 보여주려는지 한눈에 이해되지 않는다. 같은 설명, 검토 문구, 체크리스트가 반복되어 뉴스 묶음과 종목 관계가 묻힌다. 사람 검토가 필요한 곳은 어디서 무엇을 눌러 확인해야 하는지 분명해야 한다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/intelligence`는 운영자 로그가 아니라 오늘의 뉴스 판단 보드로 동작해야 한다. 사용자는 첫 화면에서 오늘 검토할 뉴스 흐름, 뉴스가 같이 묶인 이유, 직접 연결 종목 또는 시장/테마 흐름 여부, AI 후보 상세/종목 상세/원천 문서로 가는 다음 행동을 바로 구분할 수 있어야 한다.

## Why

- 현재 화면은 정보가 많지만 판단 순서가 반복 설명에 묻혀 있다.
- 사용자는 개발자 로그보다 “오늘 무엇을 봐야 하는가”와 “왜 이 뉴스가 이 종목과 연결됐는가”를 먼저 알아야 한다.

## Scope

- 포함:
  - `/intelligence` 화면 문구와 카드 구조 정리
  - 중복 체크리스트 축소
  - 각 뉴스 묶음 카드에 핵심 요약과 검토 링크만 남김
  - 화면에서 쓰지 않는 API 의존성 제거
- 제외:
  - AI 추출 로직, 뉴스 클러스터링 로직, DB schema 변경
  - 추천 점수 산식과 paper trading 로직 변경
  - write API, 감사 로그, 승인/반려 저장 기능

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/intelligence/page.tsx`
  - `apps/web/src/app/globals.css`
  - `apps/web/src/lib/frontend-api.ts`
  - `docs/tasks/intelligence-page-signal-density-pass/*`
- 수정 금지 파일:
  - `.env`/secret 값
  - DB migrations
  - backend AI extraction/scoring code

## Verification

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m awh verify --repo . --task intelligence-page-signal-density-pass`

## Done Criteria

- `/intelligence`에서 반복되는 per-cluster 검토 체크리스트가 제거되거나 압축된다.
- 각 뉴스 묶음은 제목, 뉴스 수, 원천 수, 방향, 연결 종목/시장 흐름, 왜 묶였는지, 대표 뉴스, 주요 이동 버튼을 한 카드 안에서 읽을 수 있다.
- “사람 검토”는 버튼 부재를 개발자식으로 설명하지 않고, 현재 가능한 행동과 미구현 저장 기능을 분리해서 설명한다.
- Next.js typecheck/build가 통과한다.
