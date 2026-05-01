# Review Notes

이 문서는 generator와 분리된 evaluator artifact다.

코드, diff, 구조, 리스크 관점에서 변경을 검토할 때 사용한다.

## Review Scope

- 대상 task: `market-price-ingest`
- 검토 대상 파일:
  - `src/stockanalysis/ingest/market/price.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_market_price.py`
  - `scripts/verify_market_price_ingest.sh`
  - `docs/market-price-ingest.md`
- 검토 기준: daily price normalize 정확성, symbol lookup 보수성, daily bar upsert, pipeline_run lifecycle, integration verify 신뢰성

## Claimed Outcome

- generator가 주장하는 완료 내용: `market-price-upsert` CLI가 selected daily price bars를 canonical daily bar table에 적재한다.

## Evidence Checked

- 읽은 파일:
  - `src/stockanalysis/ingest/market/price.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_market_price.py`
  - `scripts/verify_market_price_ingest.sh`
  - `docs/market-price-ingest.md`
- 실행한 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n /Users/woody/ai/stockanalysis/scripts/verify_market_price_ingest.sh`
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_market_price_ingest.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task market-price-ingest`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 확인한 로그 또는 산출물:
  - 전체 unit test 75개 통과
  - docker verify에서 `daily_price_bar` 2건 확인
  - latest adjusted close 1건, latest volume 1건, non-null `source_run_id` 2건 확인
  - latest pipeline run status `succeeded` 확인
  - readiness 검증 통과, placeholder 미검출

## Findings

심각도 순으로 적는다.

- Finding: blocking issue 없음
- Impact: 현재 범위인 market price ingest는 goal과 completion criteria를 충족한다.
- Evidence: fixture 기반 unit/integration 검증, canonical daily bar linkage, readiness 검증이 모두 통과했다.
- Suggested fix: 없음. 다음 task에서 batch ingest 또는 cycle snapshot bootstrap으로 확장하면 된다.

## Residual Risks

- 아직 남아 있는 위험:
  - single-symbol ingest만 지원한다.
  - turnover_value, market_cap enrichment가 없다.
  - live Alpha Vantage smoke가 없다.

## Open Questions

- 질문:
  - next step을 batch ingest와 retry policy 중 어디에 둘지

## Verdict

- pass with risks
