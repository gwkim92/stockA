# Review Notes

이 문서는 generator와 분리된 evaluator artifact다.

코드, diff, 구조, 리스크 관점에서 변경을 검토할 때 사용한다.

## Review Scope

- 대상 task: `seed-bootstrap`
- 검토 대상 파일:
  - `db/seeds/README.md`
  - `db/seeds/0001_reference_seed.sql`
  - `db/seeds/0002_data_sources_seed.sql`
  - `scripts/verify_migrations.sh`
  - `scripts/verify_seed_bootstrap.sh`
  - `docs/tasks/seed-bootstrap/contract.md`
  - `docs/tasks/seed-bootstrap/handoff.md`
- 검토 기준:
  - seed 범위 적절성
  - idempotent upsert 여부
  - migration 재사용성
  - 후속 ingest task와의 경계

## Claimed Outcome

- generator가 주장하는 완료 내용: 미국 시장 MVP 기준 최소 reference/data_source seed와 seed 검증 경로가 repo에 추가되었다.

## Evidence Checked

- 읽은 파일:
  - `db/README.md`
  - `db/seeds/README.md`
  - `db/seeds/0001_reference_seed.sql`
  - `db/seeds/0002_data_sources_seed.sql`
  - `scripts/verify_migrations.sh`
  - `scripts/verify_seed_bootstrap.sh`
- 실행한 명령:
  - `/tmp/agent-work-harness/scripts/new-task.sh backend /Users/woody/ai/stockanalysis seed-bootstrap --with-plan`
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_seed_bootstrap.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task seed-bootstrap`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 확인한 로그 또는 산출물:
  - seed-bootstrap task scaffold 로그
  - seed SQL 파일
  - migration + seed 적용 로그
  - seeded row count 출력
  - `Task seed-bootstrap passed readiness checks.`

## Findings

심각도 순으로 적는다.

- Finding: 현재 seed는 미국 시장만 포함한다.
- Impact: 한국 시장 우선으로 방향이 바뀌면 별도 seed 추가가 필요하다.
- Evidence: `db/seeds/0001_reference_seed.sql`
- Suggested fix: 필요 시 `0003_kr_reference_seed.sql` 같은 후속 seed 파일을 추가한다.

- Finding: data_source seed는 공식/공용 소스 중심이라 실제 가격 공급자는 아직 확정되지 않았다.
- Impact: market data ingest 구현 직전에 공급자 선택이 한 번 더 필요하다.
- Evidence: `db/seeds/0002_data_sources_seed.sql`
- Suggested fix: 다음 `ingest-bootstrap` task에서 실제 market data vendor를 결정한다.

## Residual Risks

- 아직 남아 있는 위험:
  - instrument universe seed 미구현
  - 실제 market data vendor는 아직 확정되지 않았다

## Open Questions

- 질문:
  - 다음 task를 `ingest-bootstrap`으로 갈지 `universe-bootstrap`으로 갈지

## Verdict

- pass with risks
