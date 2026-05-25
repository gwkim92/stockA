# Task Contract

## Task

- 이름: thesis-lifecycle-v2
- 요청: 종목별 thesis 상세에서 전문가식 투자 논리 생애주기를 강제하고, 최신 기업 리서치 artifact와 연결한다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/api/theses/{id}` live payload가 `왜 사는가`, `무엇이 맞아야 하는가`, `무엇이 틀리면 나가는가`, `밸류에이션 민감도`, `언제 재검토하는가`를 `lifecycle` DTO로 반환하고, Next.js thesis 상세 화면이 이 항목을 한국어로 분리해 보여준다.

## Scope

- 포함:
  - thesis detail live adapter SQL에 최신 `research.equity_research_artifact` 조회 추가
  - thesis detail DTO에 read-only `lifecycle` 추가
  - thesis 상세 화면의 생애주기 섹션 추가
  - live adapter contract test와 frontend type 갱신
  - 로컬 검증, AWH 검증, EC2 API/route smoke
- 제외:
  - 신규 DB schema/migration
  - thesis write API 또는 편집 버튼
  - recommendation score/weight 변경
  - valuation 계산식 변경
  - broker/live order submit
  - repo 안 secret/env 값

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/app/theses/[thesisId]/page.tsx`
  - `apps/web/src/lib/types.ts`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/thesis-lifecycle-v2/*`
- 수정 금지 파일:
  - 추천 scoring formula/weights
  - benchmark/evaluation split
  - broker/order submit path
  - repo 안 secret/env 값

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task thesis-lifecycle-v2`

## Done Criteria

- Thesis detail API는 기존 fields와 함께 `lifecycle`을 반환한다.
- Lifecycle은 thesis 원장, 최신 thesis review, 최신 equity research artifact를 결합하되, 누락된 항목은 환각하지 않고 `missing_items`로 남긴다.
- 화면은 사용자가 “왜 보유/추천하는지”, “무엇이 맞아야 하는지”, “무엇이 틀리면 빠지는지”, “밸류에이션 관점이 있는지”, “언제 다시 볼지”를 한 번에 읽을 수 있어야 한다.
- 화면은 이 판정이 자동 주문이 아니라 읽기 전용 투자 논리 품질 관리임을 유지한다.
