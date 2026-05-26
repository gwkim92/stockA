# valuation-target-range-foundation-v1 Handoff

## Status

- in progress: Implementation is locally complete and under final verification.

In progress.

## Current Status

Implementation is locally complete and under verification.

## Current Findings

- `market.valuation_snapshot` schema와 `valuation_snapshot` runner는 이미 존재한다.
- 포트폴리오 risk budget 쪽은 valuation snapshot을 일부 요약해 쓰고 있다.
- 종목 상세, 추천 상세, Thesis 상세 live adapter는 아직 valuation snapshot target range를 직접 반환하지 않는다.
- 화면은 equity research의 `valuation_sensitivity` 문구만 보여주므로 현재가 대비 목표가 범위, 상승여지, 안전마진을 투자자가 바로 읽기 어렵다.

## Implementation Notes

- 이번 task는 기존 산출물을 표시하는 read-only 연결 작업이다.
- 추천 산식, benchmark, evaluation split, broker/order boundary는 변경하지 않는다.
- 목표가 범위는 방법별 최신 snapshot을 모아 보수적으로 집계한다.

## Verification Log

- `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter` passed, 59 tests.
- `PYTHONPATH=src python3 -m compileall -q src tests` passed.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests` passed, 940 tests.
- `cd apps/web && npm run typecheck` passed.
- `cd apps/web && npm run build` passed.
- `bash scripts/verify_project_execution_roadmap.sh` passed.
- Initial `python3 -m unittest discover -s tests` with default Homebrew Python 3.14 failed because that interpreter has a known `pyexpat` dylib issue and lacks FastAPI. The Python 3.13 verify venv is the valid runtime for this project.

## Exact Next Step

- exact next step: Run AWH verification after the contract/handoff format update, then commit and deploy to EC2 if all local checks remain green.

Run AWH verification after the contract/handoff format update, then commit and deploy to EC2 if all local checks remain green.

## Remaining Risks

- Valuation snapshot 자체의 산식 품질은 이 task 범위 밖이다.
- 방법별 base price가 서로 다를 수 있어 집계 기준을 명확히 노출해야 한다.
- 실제 EC2 데이터에 valuation snapshot이 없는 종목은 `unavailable` 상태로 보여야 한다.
