# Portfolio Attribution Bootstrap Plan

## Context

현재 프로젝트는 추천과 thesis의 장기 outcome을 `performance.recommendation_outcome`, `performance.thesis_outcome`에 저장할 수 있다. 다음 단계는 보유 포트폴리오가 어떤 종목과 테마 노출 때문에 성과를 냈는지 설명 가능한 attribution으로 저장하는 것이다.

## Decision

- attribution v1은 `position_weighted_alpha_v1` 방법론으로 시작한다.
- 입력은 portfolio snapshot과 thesis outcome이다.
- LLM은 사용하지 않는다. 계산은 deterministic rule로 수행하고, AI는 이후 report generation에서 attribution 결과를 설명하는 역할로 제한한다.
- schema는 `performance.attribution_run`, `performance.attribution_component`를 추가한다.

## Scope

- portfolio snapshot date와 measurement end date를 받아 attribution run을 생성한다.
- security selection component는 보유 weight와 thesis alpha를 곱해 contribution bps를 계산한다.
- theme exposure component는 thesis primary classification node 기준으로 contribution bps를 집계한다.
- cash timing component는 미투자 weight를 0 bps 기여로 기록한다.
- Docker 검증은 기존 fixture의 AAPL long horizon alpha `0.060000`과 portfolio weight `0.0500`을 사용해 `30.0000` bps를 확인한다.

## Non-goals

- 실거래 체결 PnL
- Brinson-Fachler full allocation/selection decomposition
- macro/cycle attribution 자동 분해
- 추천 점수나 thesis 생성 로직 변경
- 실거래 자동화

## Verification

- `python3 -m compileall src tests`
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- `bash -n scripts/verify_portfolio_attribution_bootstrap.sh`
- `bash scripts/verify_portfolio_attribution_bootstrap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-attribution-bootstrap`
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`
