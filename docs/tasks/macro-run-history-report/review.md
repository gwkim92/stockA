# Review Notes

이 문서는 generator와 분리된 evaluator artifact다.

코드, diff, 구조, 리스크 관점에서 변경을 검토할 때 사용한다.

## Review Scope

- 대상 task: `macro-run-history-report`
- 검토 대상 파일:
  - `src/stockanalysis/ingest/macro/report.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_macro_report.py`
  - `scripts/verify_macro_run_history_report.sh`
  - `docs/macro-run-history-report.md`
- 검토 기준: recent run query 정확성, per-run observation 집계, CLI output 일관성, integration verify 신뢰성

## Claimed Outcome

- generator가 주장하는 완료 내용: `macro-run-history` CLI가 최근 macro upsert 이력을 JSON으로 반환하고, batch 적재 후 결과를 감사할 수 있다.

## Evidence Checked

- 읽은 파일:
  - `src/stockanalysis/ingest/macro/report.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_macro_report.py`
  - `scripts/verify_macro_run_history_report.sh`
  - `docs/macro-run-history-report.md`
- 실행한 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n /Users/woody/ai/stockanalysis/scripts/verify_macro_run_history_report.sh`
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_macro_run_history_report.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task macro-run-history-report`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 확인한 로그 또는 산출물:
  - unit test 25개 통과 로그
  - docker 기반 batch upsert + report verify 성공
  - report JSON에서 `run_count=2`, `status_counts.succeeded=2` 확인
  - placeholder 검색 빈 결과

## Findings

심각도 순으로 적는다.

- Finding: blocking finding 없음
- Impact: 현재 범위의 recent run audit query와 CLI output은 검증 기준을 충족한다.
- Evidence: `tests/test_macro_report.py`, `scripts/verify_macro_run_history_report.sh`, readiness 검증
- Suggested fix: 없음

- Finding: report는 batch parent entity나 장기 metric 없이 recent run audit에 집중한다.
- Impact: 운영 요약은 가능하지만 더 높은 수준의 batch/session analytics는 후속 task가 필요하다.
- Evidence: `docs/macro-run-history-report.md`의 current limits, `src/stockanalysis/ingest/macro/report.py`의 run-level query
- Suggested fix: batch/reporting 확장 task를 분리한다.

## Residual Risks

- 아직 남아 있는 위험:
  - live FRED payload 기반 history smoke는 아직 미검증이다.
  - 장기 집계 metric과 UI visualization은 없다.

## Open Questions

- 질문:
  - 향후 batch parent entity를 만들면 현재 report를 그대로 유지할지 별도 batch report를 나눌지

## Verdict

- pass with risks
