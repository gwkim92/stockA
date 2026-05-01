# Review Notes

이 문서는 generator와 분리된 evaluator artifact다.

코드, diff, 구조, 리스크 관점에서 변경을 검토할 때 사용한다.

## Review Scope

- 대상 task: `macro-ingest`
- 검토 대상 파일:
  - `docs/macro-ingest.md`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/macro/models.py`
  - `src/stockanalysis/ingest/macro/defaults.py`
  - `src/stockanalysis/ingest/macro/fred.py`
  - `src/stockanalysis/ingest/macro/sql.py`
  - `tests/test_macro_ingest.py`
  - `scripts/verify_macro_ingest.sh`
- 검토 기준: ingest bootstrap 아키텍처와의 정합성, fixture 기반 검증 가능성, SQL renderer의 경계 명확성, 다음 task로의 연결성

## Claimed Outcome

- generator가 주장하는 완료 내용: FRED macro ingest의 첫 end-to-end 경로가 구현되었고, CLI에서 정규화 요약과 SQL upsert 출력을 만들 수 있으며, deterministic 검증이 통과했다.

## Evidence Checked

- 읽은 파일:
  - `docs/ingest-bootstrap.md`
  - `docs/macro-ingest.md`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/macro/fred.py`
  - `src/stockanalysis/ingest/macro/sql.py`
  - `tests/test_macro_ingest.py`
  - `scripts/verify_macro_ingest.sh`
- 실행한 명령:
  - `bash -n /Users/woody/ai/stockanalysis/scripts/verify_macro_ingest.sh`
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_macro_ingest.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task macro-ingest`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 확인한 로그 또는 산출물:
  - unittest 14개 통과 로그
  - fixture 기반 `macro-sync`가 생성한 SQL output 파일
  - `Task macro-ingest passed readiness checks.` 출력
  - placeholder 검색 빈 결과

## Findings

심각도 순으로 적는다.

- Finding: direct DB execute가 아직 없어 SQL renderer가 중간 산출물 역할만 한다.
- Impact: 실제 pipeline run과 `source_run_id` 연결은 아직 비어 있다.
- Evidence: `src/stockanalysis/ingest/macro/sql.py`의 `released_at`, `source_run_id` null 처리와 `docs/macro-ingest.md`의 current implementation boundary
- Suggested fix: 다음 task에서 Postgres execute runner를 추가하고 `ops.pipeline_run`과 연결한다.

- Finding: FRED revision/vintage를 아직 반영하지 않는다.
- Impact: 시계열 revision 분석이나 point-in-time 백테스트에는 아직 부족하다.
- Evidence: `src/stockanalysis/ingest/macro/models.py`의 `revision_number=0` 고정, `docs/macro-ingest.md`의 미구현 항목
- Suggested fix: `ALFRED` 또는 revision-aware ingest task를 별도로 만든다.

## Residual Risks

- 아직 남아 있는 위험:
  - 기본 macro series 세트가 초기 시장 레짐 분류에 충분한지 아직 평가 전이다.
  - live API 환경에서 rate limit이나 payload edge case가 드러날 수 있다.

## Open Questions

- 질문:
  - SQL renderer를 유지한 채 direct execute를 추가할지, 한 경로로 통합할지

## Verdict

- pass with risks
