# Task Contract

## Task

- 이름: paper-validation-conflict-remediation
- 요청: 최신 paper validation conflict 3건을 data, thesis, risk-limit, recommendation-action 문제로 분류하고, 추천 weight 변경 전 차단 사유를 명확히 한다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations paper-validation-conflict-remediation-run --as-of-date YYYY-MM-DD`가 최신 `trading.paper_validation_run`과 연결된 `trading.order_intent_audit`를 읽고, conflict를 `portfolio_recommendation_coverage_gap`, `actionable_trade_block`, `safety_interlock`, `unknown_blocker`로 분류해 다음 remediation action을 반환한다.

## Scope

- 포함:
  - 최신 paper validation run 조회
  - `blocked_reasons` 파싱
  - AAPL/MSFT/TSLA 같은 보유 종목 coverage gap과 AEIS/ARM/QUBT/SPY 같은 safety interlock 분리
  - 주문 델타 0인 review-only gap과 실제 actionable trade block 분리
  - `--execute` 시 `ops.pipeline_run`에 분류 결과 기록
  - CLI와 unit/CLI tests
- 제외:
  - 추천 점수 산식/weight 변경
  - paper validation run 자체 수정
  - position snapshot/recommendation/thesis 자동 수정
  - kill switch 해제
  - human approval 우회
  - broker live submit

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/paper_validation_conflict_remediation.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_paper_validation_conflict_remediation.py`
  - `tests/test_data_operations_cli.py`
  - `docs/tasks/paper-validation-conflict-remediation/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
- 수정 금지 파일:
  - `src/stockanalysis/signal/recommendation.py` scoring weights
  - `trading.paper_validation_run` historical rows
  - broker/order submit path
  - `.env` secret values

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_paper_validation_conflict_remediation tests.test_data_operations_cli`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task paper-validation-conflict-remediation`

## Done Criteria

- conflict 3건이 단순 “주문 실패”로 뭉개지지 않고 보유 종목 coverage/thesis lifecycle 문제로 분류된다.
- kill switch와 human approval은 의도된 safety interlock으로 분리된다.
- runner는 추천, 보유, paper validation, broker submit 데이터를 변경하지 않는다.
- 다음 작업이 보유 종목 coverage 복구인지, safety policy 승인인지 명확히 보인다.
