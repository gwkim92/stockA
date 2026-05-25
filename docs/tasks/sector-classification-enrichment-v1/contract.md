# Task Contract

## Task

- 이름: sector-classification-enrichment-v1
- 요청: 포트폴리오 위험 예산 v2에서 드러난 `sector exposure count = 0` 문제를 해소한다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 주요 미국 주식/ETF가 `ref.classification_node.node_type='sector'` 노드와 `ref.instrument_classification_membership.membership_type='sector_membership'`으로 연결되고, `/api/portfolio/{portfolio}/coverage`가 섹터 노출을 0이 아닌 값으로 반환한다.

## Scope

- 포함:
  - sector classification node seed 추가
  - core universe instrument/ETF sector membership seed 추가
  - sector-to-theme/domain edge seed 추가
  - seed file idempotency 검증 테스트
  - EC2 seed apply와 포트폴리오 coverage smoke
- 제외:
  - 외부 유료 sector provider 도입
  - GICS 전체 universe 구축
  - 추천 score/weight 변경
  - broker/order submit
  - repo 안 secret/env 값

## Mutable Surface

- 수정 가능한 파일:
  - `db/seeds/0005_sector_classification_seed.sql`
  - `db/README.md`
  - `db/seeds/README.md`
  - `tests/test_sector_classification_seed.py`
  - `docs/tasks/sector-classification-enrichment-v1/*`
- 수정 금지 파일:
  - 추천 scoring formula/weights
  - benchmark/evaluation split
  - broker/order submit path
  - repo 안 secret/env 값

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_sector_classification_seed tests.test_frontend_live_adapter`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `bash scripts/verify_seed_bootstrap.sh`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task sector-classification-enrichment-v1`

## Done Criteria

- Seed는 재실행해도 중복 membership을 만들지 않는다.
- 주요 현재 보유/분석 대상인 `AAPL`, `MSFT`, `NVDA`, `TSLA`, `XOM`, `SPY`, `QQQ`, `TLT`, `XLF`, `XLE`, `QUBT`, `BABA`에 sector membership이 생긴다.
- 포트폴리오 coverage에서 sector exposure가 0이 아니어야 한다.
- 미분류 노출이 실제 미분류 종목에만 남아야 한다.
