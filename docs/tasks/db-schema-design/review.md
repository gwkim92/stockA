# Review Notes

이 문서는 generator와 분리된 evaluator artifact다.

코드, diff, 구조, 리스크 관점에서 변경을 검토할 때 사용한다.

## Review Scope

- 대상 task: `db-schema-design`
- 검토 대상 파일: `docs/db-schema-design.md`, `docs/tasks/db-schema-design/contract.md`, `docs/tasks/db-schema-design/plan.md`, `docs/tasks/db-schema-design/handoff.md`
- 검토 기준: foundation 문서와의 정합성, canonical vs analytical 저장 분리, history/provenance 보존, 다음 구현 단계 연결성

## Claimed Outcome

- generator가 주장하는 완료 내용: 투자 운영 시스템의 DB 스키마가 구현 가능한 수준의 문서로 저장되었고, 다음 단계에서 DDL skeleton을 바로 작성할 수 있는 상태가 되었다.

## Evidence Checked

- 읽은 파일:
  - `docs/project-foundation.md`
  - `docs/db-schema-design.md`
  - `docs/tasks/foundation-architecture/handoff.md`
  - `docs/tasks/db-schema-design/contract.md`
  - `docs/tasks/db-schema-design/plan.md`
  - `docs/tasks/db-schema-design/handoff.md`
- 실행한 명령:
  - `/tmp/agent-work-harness/scripts/new-task.sh research /Users/woody/ai/stockanalysis db-schema-design --with-plan`
  - `find /Users/woody/ai/stockanalysis/docs/tasks -maxdepth 3 -type f | sort`
- 확인한 로그 또는 산출물:
  - task scaffold 결과
  - 설계 문서 초안

## Findings

심각도 순으로 적는다.

- Finding: 공급자별 데이터 모델 차이는 아직 문서 수준에서 추상화되어 있다.
- Impact: 실제 수집 단계에서 `estimate_snapshot`, `investor_flow_daily`, `financial_metric_value` 컬럼이 약간 조정될 수 있다.
- Evidence: `docs/db-schema-design.md`의 deferred decisions와 market schema 설명
- Suggested fix: DDL skeleton task에서 초기 공급자를 하나 정하고 vendor mapping note를 함께 작성한다.

- Finding: full text 검색, 국가/정책 전용 엔터티, embedding 저장 전략은 후순위로 미뤄졌다.
- Impact: 이벤트 검색과 고급 LLM retrieval은 초기 MVP에서 단순화된다.
- Evidence: `docs/db-schema-design.md`의 deferred decisions 섹션
- Suggested fix: MVP 이후 `event-search-and-retrieval` 설계 task를 별도로 만든다.

## Residual Risks

- 아직 남아 있는 위험:
  - 첫 시장과 데이터 공급원 미확정
  - benchmark 모델링 세부 미정

## Open Questions

- 질문:
  - 우선순위 1 테이블을 한 번에 migration할지, `ref/ops/market`과 `signal/portfolio`로 나눌지

## Verdict

- pass with risks
