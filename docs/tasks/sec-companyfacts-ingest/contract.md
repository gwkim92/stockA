# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: sec-companyfacts-ingest
- 요청: SEC companyfacts JSON을 canonical financial schema에 적재하는 첫 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `sec-companyfacts-upsert` CLI가 selected SEC companyfacts facts를 canonical instrument에 연결하고 `market.financial_statement_period`, `market.financial_metric_value`를 upsert한다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: 추천과 thesis 엔진이 사용할 기본 재무 팩트가 canonical DB에 있어야 이후 실적 추세, quality, earnings revision 기반 분석이 가능해진다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/sources/sec.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `db/migrations/0002_priority_1_tables.sql`
- 관련 문서:
  - `docs/sec-filings-ingest.md`
  - `docs/event-instrument-impact-bootstrap.md`
  - `docs/verification-plan.md`
  - `docs/tasks/event-instrument-impact-bootstrap/handoff.md`
- 이전 결정:
  - SEC ingest는 official `data.sec.gov` source를 사용한다.
  - canonical instrument linkage는 exact-match lookup을 우선한다.
  - first-step companyfacts ingest는 deterministic metric subset만 다룬다.

## Scope

- 포함:
  - companyfacts payload normalize
  - selected USD `us-gaap` metrics ingest
  - exact-match canonical instrument lookup
  - `financial_statement_period`, `financial_metric_value` upsert
  - CLI, tests, integration verify, task docs
- 제외:
  - fuzzy instrument resolution
  - all taxonomy concepts ingest
  - estimate snapshot generation
  - earnings revision logic

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/plans/2026-04-20-sec-companyfacts-ingest.md`
  - `docs/sec-companyfacts-ingest.md`
  - `docs/tasks/event-instrument-impact-bootstrap/handoff.md`
  - `docs/tasks/sec-companyfacts-ingest/`
  - `docs/verification-plan.md`
  - `scripts/verify_sec_companyfacts_ingest.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/sec/companyfacts.py`
  - `src/stockanalysis/ingest/sec/models.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_sec_companyfacts.py`
  - `tests/fixtures/sec_companyfacts_CIK0000320193.json`
- 수정 금지 파일:
  - migrations and seeds
  - macro ingest code
- 검증에 사용할 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_companyfacts_ingest.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task sec-companyfacts-ingest`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`

## Deliverables

- 필수 결과물:
  - `src/stockanalysis/ingest/sec/companyfacts.py`
  - `tests/test_sec_companyfacts.py`
  - `tests/fixtures/sec_companyfacts_CIK0000320193.json`
  - `scripts/verify_sec_companyfacts_ingest.sh`
  - `docs/sec-companyfacts-ingest.md`
  - `docs/tasks/sec-companyfacts-ingest/contract.md`
  - `docs/tasks/sec-companyfacts-ingest/plan.md`
  - `docs/tasks/sec-companyfacts-ingest/handoff.md`
- 선택 결과물:
  - `docs/tasks/sec-companyfacts-ingest/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] selected companyfacts facts가 canonical financial schema에 적재된다
- [x] fixture 기반 companyfacts integration verify 경로가 존재한다

## Verification Plan

- 자동 검증: `bash scripts/verify_sec_companyfacts_ingest.sh`, `awh verify --task sec-companyfacts-ingest`, placeholder 검색
- 수동 검증: `docs/sec-companyfacts-ingest.md`가 supported metric map과 current limits를 분명히 설명하는지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: unit/integration 검증 통과, annual/quarterly period row와 metric row 생성 확인, readiness 검증 통과

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `sec-companyfacts-upsert` command와 companyfacts ingest 코드만 제거하면 기존 SEC/event pipeline은 유지된다.

## Open Questions

- 질문: first metric subset 이후 어떤 us-gaap/ifrs metric을 우선 확장할지
- 답이 없을 때 적용할 임시 가정: 현재는 10-K/10-Q의 핵심 USD duration metrics만 먼저 적재한다.
