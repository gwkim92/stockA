# Task Contract

## Task

- 이름: professional-equity-analysis-foundation
- 요청: 기존 뉴스·AI·사이클·추천 구조에 전문가식 기업 분석 기반을 추가한다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: SEC companyfacts와 기존 canonical DB를 기반으로 표준 재무지표, 피어 그룹, 상대 비교, 밸류에이션, AI 리서치 artifact를 저장할 수 있는 schema와 첫 read/write runner가 존재한다.
- 첫 실행 단위는 재무지표 정규화다. 추천 점수 weight는 변경하지 않고, 추천 상세에 반영하는 UI 확장은 후속 task로 둔다.

## Scope

- 포함:
  - professional equity analysis 저장 레이어 migration
  - 표준 재무지표 정규화 테이블과 runner
  - 피어 그룹/피어 상대 비교/밸류에이션/AI 리서치 artifact를 위한 canonical table foundation
  - `stockanalysis-operations financial-metric-normalization-run` CLI
  - unit/CLI tests와 하네스 handoff
- 제외:
  - 추천 score weight 변경
  - DCF/relative valuation 실제 총점 반영
  - Codex OAuth 리서치 리포트 생성
  - frontend redesign
  - broker live order submit

## Mutable Surface

- 수정 가능한 파일:
  - `db/migrations/0021_professional_equity_analysis.sql`
  - `src/stockanalysis/operations/professional_equity_analysis.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/ingest/sec/companyfacts.py`
  - `tests/test_professional_equity_analysis.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_data_operations_cadence.py`
  - `docs/tasks/professional-equity-analysis-foundation/*`
  - `docs/project-execution-roadmap.md`
- 수정 금지 파일:
  - 추천 scoring formula/weights
  - benchmark/evaluation split
  - broker/order submit path
  - repo 안 secret/env 값

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_sec_companyfacts tests.test_professional_equity_analysis tests.test_data_operations_cli tests.test_data_operations_cadence`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task professional-equity-analysis-foundation`

## Done Criteria

- 표준 재무지표 정규화 runner는 missing input을 환각하지 않고 `unavailable` 또는 `insufficient_history`로 남긴다.
- SEC companyfacts에서 무료 공개 데이터만 사용한다.
- 추천 weight는 바뀌지 않는다.
- 피어/밸류에이션/AI 리서치 테이블은 후속 task가 바로 이어서 사용할 수 있는 이름과 제약을 갖는다.
