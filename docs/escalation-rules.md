# Escalation Rules

이 문서는 guided single-agent로는 부족한 작업을 상위 하네스로 승격할 때 기준으로 사용한다.

## Default Policy

- 기본값은 현재 구조를 유지하는 것이다
- 병목이 드러날 때만 승격한다
- 승격 전에는 관련 task 문서를 먼저 만든다

## Add `docs/tasks/<task-slug>/plan.md` When

아래 중 둘 이상이면 `plan.md`를 추가한다.

- 작업이 하루 이상 이어질 것 같다
- milestone이 둘 이상이다
- 변경 파일이 많다
- 순차 의존 단계가 명확하다
- 중간 점검 없이 끝내기 위험하다
- 세션이 끊기면 상태 복구 비용이 크다

## Add Evaluator Artifacts When

아래 중 하나라도 강하면 evaluator artifact를 추가한다.

- agent가 완료를 자주 낙관적으로 말한다
- 테스트는 통과하지만 실제 동작이 어긋난다
- UI나 런타임 상태가 중요하다
- 로그, trace, browser evidence가 필요하다

추가할 파일:

- `review.md`
- `qa.md`

## Add Multi-Agent Docs When

아래 중 둘 이상이면 multi-agent 문서를 추가 검토한다.

- 병렬 가능한 독립 흐름이 둘 이상 있다
- planner, generator, evaluator, specialist 같은 역할 분리가 유익하다
- ownership이 없으면 충돌 가능성이 높다
- review 관점을 별도 역할로 떼야 한다

추가할 파일:

- `roles.md`
- `topology.md`

추가 규칙:

- 가능하면 먼저 evaluator artifact를 분리하고 실제 검증 내용까지 채워 둔다
- 기본 추천 패턴은 `planner -> generator -> evaluator` 또는 `coordinator + specialists`다
- `parallel specialists -> integrator`는 ownership 분리가 문서로 명확할 때만 쓴다
- final gate와 handoff artifact가 없으면 아직 multi-agent-ready가 아니다

## Add Automation Contract When

아래 중 둘 이상이면 automation 계약을 추가 검토한다.

- 반복 작업이다
- keep/discard 기준이 있다
- 예산 제한이 있다
- rollback이 가능하다
- 로그나 metric으로 상태를 본다

추가할 파일:

- `loop_contract.md`

## Agent Behavior

- agent는 승격 필요성을 제안할 수 있다
- agent는 관련 task 문서를 scaffold할 수 있다
- agent는 승격 이유를 contract와 handoff에 기록해야 한다

실행 정책은 별도다.

- 실제 multi-agent 실행
- 실제 automation 활성화

이 둘은 프로젝트 정책과 호스트 정책을 따른다.
