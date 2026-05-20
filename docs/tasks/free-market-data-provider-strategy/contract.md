# Task Contract

## Task

- 이름: free-market-data-provider-strategy
- 요청: Alpha Vantage 무료 한도가 broad universe 운영에 충분한지 확인하고, 무료 market data 대안을 정리한다.
- 담당: Codex
- 날짜: 2026-05-17

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: Alpha Vantage를 소형 우선순위 fallback으로 제한하고, broad universe 가격 수집을 위한 무료 provider pilot 순서를 문서로 고정한다.

## Why

- Alpha Vantage 공식 무료 한도는 25 requests/day로 하루 1회는 아니지만, 7,562개 canonical instrument 또는 수백 개 watchlist 운영에는 부족하다.
- 중장기 투자 시스템도 가격 freshness와 성과 측정이 필요하므로, 무료/저비용 가격 데이터 경로를 분리해야 한다.

## Scope

- Alpha Vantage 무료 한도와 현재 local ledger 상태를 정리한다.
- 무료 후보 provider를 최신 공식/준공식 자료 기준으로 비교한다.
- 첫 pilot provider와 fallback 원칙을 결정한다.

## Boundaries

- 이번 task에서는 새 API key를 요구하거나 provider call을 하지 않는다.
- `.env`와 repo-outside env secret 값은 읽거나 문서에 남기지 않는다.
- 가격 provider adapter 구현은 다음 task로 분리한다.
- broker/order flow, paper trading, scoring formula, DB schema는 바꾸지 않는다.

## Mutable Surface

- 수정 가능한 파일:
  - `docs/tasks/free-market-data-provider-strategy/`
  - `docs/plans/2026-05-17-free-market-data-provider-strategy.md`
  - `docs/tasks/local-live-mvp-runtime/handoff.md`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task free-market-data-provider-strategy`
  - `git diff --check`

## Done Criteria

- [x] Alpha Vantage 하루 1회 오해를 정정한다.
- [x] 무료 후보 provider를 비교한다.
- [x] 첫 provider pilot 순서를 고정한다.
- [x] 현재 runtime 상태와 다음 작업을 handoff에 남긴다.
