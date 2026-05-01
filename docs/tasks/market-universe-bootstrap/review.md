# Review Notes

이 문서는 generator와 분리된 evaluator artifact다.

코드, diff, 구조, 리스크 관점에서 변경을 검토할 때 사용한다.

## Review Scope

- 대상 task: `market-universe-bootstrap`
- 검토 대상 파일:
  - `src/stockanalysis/ingest/sources/sec.py`
  - `src/stockanalysis/ingest/market/universe.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_market_universe.py`
  - `scripts/verify_market_universe_bootstrap.sh`
  - `docs/market-universe-bootstrap.md`
- 검토 기준: SEC source shape 반영 정확성, supported exchange filter, canonical ref upsert 안정성, integration verify 신뢰성

## Claimed Outcome

- generator가 주장하는 완료 내용: `market-universe-bootstrap` CLI가 SEC listed ticker/exchange payload에서 supported exchange universe를 canonical reference tables에 적재한다.

## Evidence Checked

- 읽은 파일:
  - `src/stockanalysis/ingest/sources/sec.py`
  - `src/stockanalysis/ingest/market/universe.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_market_universe.py`
  - `scripts/verify_market_universe_bootstrap.sh`
  - `docs/market-universe-bootstrap.md`
- 실행한 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n /Users/woody/ai/stockanalysis/scripts/verify_market_universe_bootstrap.sh`
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_market_universe_bootstrap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task market-universe-bootstrap`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 확인한 로그 또는 산출물:
  - `compileall` 성공
  - 전체 `unittest` 85개 통과
  - docker verify 성공
  - readiness verify 성공
  - placeholder 검색 출력 없음

## Findings

심각도 순으로 적는다.

- blocking issue 없음

## Residual Risks

- 아직 남아 있는 위험:
  - issuer CIK를 canonical ref tables에 저장하지 않는다.
  - `OTC`, `CBOE`는 skip된다.
  - security type 세분화가 없다.

## Open Questions

- 질문:
  - canonical bootstrap 이후 curated universe slicing을 어떤 기준으로 둘지

## Verdict

- pass with risks
