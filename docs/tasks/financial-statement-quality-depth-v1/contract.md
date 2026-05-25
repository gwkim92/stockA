# Task Contract

## Task

- 이름: financial-statement-quality-depth-v1
- 요청: 전문 애널리스트식 재무제표 품질 분석을 강화하기 위해 earnings quality와 현금흐름 품질 지표를 추가한다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `financial-metric-normalization-run`이 기존 표준 지표에 더해 `free_cash_flow_to_net_income`, `accrual_ratio`, `capex_intensity`, `liabilities_to_assets`를 계산 또는 `unavailable`로 저장하고, 추천 fundamental component는 새 earnings quality 지표를 zero-weight 입력으로 활용한다.

## Scope

- 포함:
  - standard financial metric list 확장
  - financial metric normalization SQL에 earnings quality 지표 추가
  - recommendation fundamental component input에 새 지표 반영
  - peer relative analysis는 확장된 metric universe를 그대로 사용
  - unit tests 갱신
- 제외:
  - DB schema 변경
  - SEC 유료 데이터 provider
  - footnote 전문 텍스트 파싱
  - 추천 score/weight 변경
  - broker/order submit

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/professional_equity_analysis.py`
  - `src/stockanalysis/operations/recommendation_fundamental_components.py`
  - `tests/test_professional_equity_analysis.py`
  - `tests/test_recommendation_fundamental_components.py`
  - `docs/tasks/financial-statement-quality-depth-v1/*`
- 수정 금지 파일:
  - DB migrations
  - recommendation scoring formula/weights
  - broker/order submit path
  - `.env` secret values

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_professional_equity_analysis tests.test_recommendation_fundamental_components`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task financial-statement-quality-depth-v1`

## Done Criteria

- [ ] normalization SQL includes the four new metrics.
- [ ] missing inputs remain `unavailable`; no fabricated values are created.
- [ ] recommendation fundamental component reads the new earnings quality metrics.
- [ ] all recommendation component weights remain `0.0000`.
- [ ] no DB schema or recommendation formula mutation is introduced.

