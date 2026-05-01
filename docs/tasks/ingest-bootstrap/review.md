# Review Notes

이 문서는 generator와 분리된 evaluator artifact다.

코드, diff, 구조, 리스크 관점에서 변경을 검토할 때 사용한다.

## Review Scope

- 대상 task: `ingest-bootstrap`
- 검토 대상 파일:
  - `docs/ingest-bootstrap.md`
  - `src/stockanalysis/ingest/`
  - `tests/test_ingest_cli.py`
  - `tests/test_ingest_sources.py`
  - `scripts/verify_ingest_bootstrap.sh`
  - `db/seeds/0002_data_sources_seed.sql`
- 검토 기준:
  - collector 계층 분리
  - source selection 근거
  - request builder correctness
  - 검증 가능성

## Claimed Outcome

- generator가 주장하는 완료 내용: ingest bootstrap code skeleton과 source selection 문서, 테스트, verification 경로가 repo에 추가되었다.

## Evidence Checked

- 읽은 파일:
  - `docs/ingest-bootstrap.md`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/registry.py`
  - `src/stockanalysis/ingest/sources/sec.py`
  - `src/stockanalysis/ingest/sources/fred.py`
  - `src/stockanalysis/ingest/sources/alpha_vantage.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_ingest_sources.py`
- 실행한 명령:
  - `/tmp/agent-work-harness/scripts/new-task.sh backend /Users/woody/ai/stockanalysis ingest-bootstrap --with-plan`
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_ingest_bootstrap.sh`
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_seed_bootstrap.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task ingest-bootstrap`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 확인한 로그 또는 산출물:
  - ingest-bootstrap task scaffold 로그
  - ingest package source files
  - unit test 8개 통과 로그
  - `list-sources` 출력
  - seed 재검증 row count 출력
  - `Task ingest-bootstrap passed readiness checks.`

## Findings

심각도 순으로 적는다.

- Finding: collector는 아직 request build/fetch entrypoint까지만 있고 DB upsert는 없다.
- Impact: 실제 적재 파이프라인은 후속 task가 필요하다.
- Evidence: `src/stockanalysis/ingest/` 구조와 `docs/ingest-bootstrap.md`
- Suggested fix: 다음 task를 source별 raw fetch/store/upsert로 분리한다.

- Finding: Alpha Vantage 선택은 bootstrap 용도 판단이며 장기 scale 적합성은 아직 확정되지 않았다.
- Impact: 시장 데이터 source는 추후 교체될 수 있다.
- Evidence: `docs/ingest-bootstrap.md`
- Suggested fix: `market-data-ingest` 또는 vendor-evaluation task에서 재평가한다.

## Residual Risks

- 아직 남아 있는 위험:
  - 실제 live fetch smoke는 key/header 환경변수 없이는 못 돌린다
  - DB upsert 계층 미구현

## Open Questions

- 질문:
  - 다음을 `universe-bootstrap`으로 갈지, `macro-ingest`로 갈지, `sec-filings-ingest`로 갈지

## Verdict

- pass with risks
