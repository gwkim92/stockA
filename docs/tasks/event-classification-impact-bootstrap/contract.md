# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: event-classification-impact-bootstrap
- 요청: SEC event rows를 최소 classification taxonomy에 연결하는 bootstrap 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `event-classification-impact-bootstrap` CLI가 pending SEC events를 찾아 classification nodes와 event classification impacts를 bootstrap한다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: 이벤트가 분류 노드에 연결되어야 이후 cycle snapshot, thesis, recommendation 엔진이 이벤트를 테마/섹터 관점에서 읽을 수 있다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/sec/event_extract.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `db/migrations/0002_priority_1_tables.sql`
- 관련 문서:
  - `docs/sec-filings-event-extraction.md`
  - `docs/sec-filings-event-batch-extract.md`
  - `docs/verification-plan.md`
  - `docs/tasks/sec-filings-event-batch-extract/handoff.md`
- 이전 결정:
  - SEC event extraction은 deterministic heuristic path다.
  - batch event extraction은 pending SEC raw filings를 자동 discovery한다.
  - classification impact 첫 단계는 minimal internal taxonomy bootstrap으로 제한한다.

## Scope

- 포함:
  - pending SEC event discovery
  - minimal `internal_theme` taxonomy bootstrap
  - `event.event_classification_impact` upsert
  - CLI, tests, integration verify, task docs
- 제외:
  - instrument impact bootstrap
  - richer sector/theme taxonomy
  - retry policy
  - companyfacts ingest

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/event-classification-impact-bootstrap.md`
  - `docs/verification-plan.md`
  - `docs/plans/2026-04-20-event-classification-impact-bootstrap.md`
  - `docs/tasks/event-classification-impact-bootstrap/`
  - `docs/tasks/sec-filings-event-batch-extract/handoff.md`
  - `scripts/verify_event_classification_impact_bootstrap.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/sec/classification_impact.py`
  - `src/stockanalysis/ingest/sec/models.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_sec_classification_impact.py`
- 수정 금지 파일:
  - migrations and seeds
  - macro ingest code
- 검증에 사용할 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_event_classification_impact_bootstrap.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task event-classification-impact-bootstrap`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`

## Deliverables

- 필수 결과물:
  - `src/stockanalysis/ingest/sec/classification_impact.py`
  - `tests/test_sec_classification_impact.py`
  - `scripts/verify_event_classification_impact_bootstrap.sh`
  - `docs/event-classification-impact-bootstrap.md`
  - `docs/tasks/event-classification-impact-bootstrap/contract.md`
  - `docs/tasks/event-classification-impact-bootstrap/plan.md`
  - `docs/tasks/event-classification-impact-bootstrap/handoff.md`
- 선택 결과물:
  - `docs/tasks/event-classification-impact-bootstrap/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] pending SEC events가 classification node에 연결된다
- [x] minimal internal theme taxonomy가 bootstrap된다
- [x] fixture 기반 classification impact 검증 경로가 존재한다

## Verification Plan

- 자동 검증: `bash scripts/verify_event_classification_impact_bootstrap.sh`, `awh verify --task event-classification-impact-bootstrap`, placeholder 검색
- 수동 검증: `docs/event-classification-impact-bootstrap.md`가 node bootstrap과 event mapping을 분명히 설명하는지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: unit/integration 검증 통과, taxonomy node/edge 생성 확인, event classification impact 생성 확인, readiness 검증 통과

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `event-classification-impact-bootstrap` command와 classification bootstrap 코드만 제거하면 기존 event pipeline은 유지된다.

## Open Questions

- 질문: minimal reporting taxonomy를 언제 broader sector/theme taxonomy로 확장할지
- 답이 없을 때 적용할 임시 가정: 현재는 reporting/governance 중심 bootstrap만 먼저 도입한다.
