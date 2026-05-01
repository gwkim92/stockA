# Review Notes

이 문서는 generator와 분리된 evaluator artifact다.

코드, diff, 구조, 리스크 관점에서 변경을 검토할 때 사용한다.

## Review Scope

- 대상 task: `market-price-batch-ingest`
- 검토 대상 파일:
  - `src/stockanalysis/ingest/market/price.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_market_price.py`
  - `scripts/verify_market_price_batch_ingest.sh`
  - `docs/market-price-batch-ingest.md`
- 검토 기준: batch orchestration 안정성, fixture resolution, per-symbol runner 재사용, integration verify 신뢰성

## Claimed Outcome

- generator가 주장하는 완료 내용: `market-price-batch-upsert` CLI가 여러 symbol의 daily price bars를 canonical daily bar table에 적재한다.

## Evidence Checked

- 읽은 파일:
  - `src/stockanalysis/ingest/market/price.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_market_price.py`
  - `scripts/verify_market_price_batch_ingest.sh`
  - `docs/market-price-batch-ingest.md`
- 실행한 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n /Users/woody/ai/stockanalysis/scripts/verify_market_price_batch_ingest.sh`
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_market_price_batch_ingest.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task market-price-batch-ingest`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 확인한 로그 또는 산출물:
  - `compileall` 성공
  - 전체 `unittest` 78개 통과
  - docker verify 성공
  - readiness verify 성공
  - placeholder 검색 출력 없음

## Findings

심각도 순으로 적는다.

- blocking issue 없음

## Residual Risks

- 아직 남아 있는 위험:
  - explicit symbol list만 지원한다.
  - parent batch pipeline run이 없다.
  - live Alpha Vantage batch smoke가 없다.

## Open Questions

- 질문:
  - default universe를 SEC company tickers 기반으로 고정할지, 별도 curated watchlist를 둘지

## Verdict

- pass with risks
