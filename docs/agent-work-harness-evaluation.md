# Agent Work Harness Evaluation

## Evaluation Target

- Repository: `https://github.com/gwkim92/agent-work-harness`
- Inspected branch: `main`
- Inspected commit: `b9063f849ff7746fd701ab98e2d9473a3021ed50`

## What It Is

`agent-work-harness`는 투자 분석 시스템의 런타임 프레임워크가 아니다.

이 저장소는 `개발 워크플로 하네스`다.

주요 목적:

- 저장소 수준 작업 규칙 고정
- task별 상태를 채팅이 아니라 파일로 축적
- contract, handoff, review, qa 같은 작업 아티팩트 표준화
- planner, evaluator, multi-agent, automation 승격 기준 명문화
- CLI로 템플릿 설치와 검증 자동화

즉, 이것을 이식한다고 해서 우리 프로젝트가 바로 시장 분석을 잘하게 되는 것은 아니다.
대신 `AI와 사람이 이 프로젝트를 개발하는 방식`이 더 구조화된다.

## What It Would Add To This Repository

repo-level 기본 파일:

- `AGENTS.md`
- `docs/verification-plan.md`
- `docs/escalation-rules.md`
- `docs/tasks/README.md`

task-level 공통 파일:

- `contract.md`
- `handoff.md`
- 필요 시 `plan.md`
- 필요 시 `review.md`, `qa.md`
- 장기 작업 시 `progress.md`, `feature_list.json`, `evidence/manifest.json`
- 멀티에이전트 필요 시 `roles.md`, `topology.md`
- 자동 루프 전환 시 `loop_contract.md`

## Why It Fits This Project

우리 프로젝트는 아래 특징을 가진다.

- 장기적인 그린필드 프로젝트다
- 리서치, 데이터, 백엔드, 평가가 모두 섞인다
- 작업이 세션을 넘어 이어질 가능성이 크다
- 추천 품질보다 평가 체계가 더 중요하다
- 실험과 규칙 변경이 누적될 가능성이 높다

이 특성은 `agent-work-harness`가 해결하려는 문제와 잘 맞는다.

특히 좋은 점:

1. 작업 상태를 채팅 의존이 아니라 파일로 남길 수 있다.
2. 각 태스크의 범위와 수정 가능 표면을 먼저 고정할 수 있다.
3. 추천/평가 로직 작업에서 검증 기준을 미리 문서화할 수 있다.
4. 장기 작업에서 handoff 품질이 좋아진다.
5. 나중에 multi-agent나 automation으로 커져도 승격 경로가 있다.

## Where It Does Not Fit Perfectly

이 하네스는 `개발 관리 도구`이지, 우리 제품의 핵심 도메인 로직은 아니다.

따라서 아래 오해는 피해야 한다.

- 이 하네스를 넣는다고 투자 모델 품질이 올라가는 것은 아니다.
- 이 하네스를 넣는다고 데이터 파이프라인이 생기는 것은 아니다.
- 이 하네스를 넣는다고 사이클 엔진이 만들어지는 것은 아니다.

또한 초기에 너무 무겁게 쓰면 오버헤드가 생긴다.

위험:

- 아직 작은 작업에도 plan/review/qa를 모두 강제하면 속도가 느려진다.
- verification-plan이 비어 있으면 문서만 많고 품질은 안 올라간다.
- 실제 제품 설계보다 하네스 정리에 시간이 더 들어갈 수 있다.

## Practical Fit Assessment

이 프로젝트는 `research/ML` 성격과 `long-running product build` 성격을 동시에 가진다.

하네스 저장소 자체 가이드 기준으로도 이런 프로젝트에는 보통 아래가 권장된다.

- 기본 도입 레벨: `Level 1`
- 강한 검증 기준 필요 시 부분적으로 `Level 2`
- 자동화와 long-running loop는 검증 기준이 안정화된 뒤

우리 프로젝트에 그대로 옮기면 가장 적절한 도입 수준은 아래다.

### Adopt Now

- repo-level 문서
- task-level `contract.md`
- task-level `handoff.md`
- 큰 작업에서만 `plan.md`

### Adopt Selectively

- 데이터 파이프라인 검증, 백테스트 검증, 대시보드 검증이 생기면 `review.md` 또는 `qa.md`
- 장기 스프린트나 실험 루프가 생기면 `progress.md`, `feature_list.json`, `evidence/manifest.json`

### Defer

- `roles.md`
- `topology.md`
- `loop_contract.md`

이 세 가지는 실제로 병렬 에이전트 운영이나 자동 루프가 필요해질 때 도입하는 편이 맞다.

## Decision

결론은 `부분 도입은 이득`, `풀 하네스 즉시 이식은 과함`이다.

좀 더 명확히 말하면:

- `AGENTS.md`, `docs/verification-plan.md`, `docs/tasks/README.md`, `docs/escalation-rules.md`는 지금 도입할 가치가 높다.
- task-level `contract.md`, `handoff.md`는 큰 작업마다 쓰는 것이 유리하다.
- 하지만 처음부터 모든 task에 planner, evaluator, multi-agent, automation 문서를 다 붙이는 것은 비효율적이다.

## Final Recommendation

권장안:

1. 현재 저장소에는 `Level 1` 중심으로 도입한다.
2. 검증이 중요한 작업부터 `Level 2` 문서를 선택적으로 추가한다.
3. 추천/백테스트/리포트 루프가 안정화되기 전에는 `Level 4~5`로 가지 않는다.
4. 하네스는 `제품 자체`가 아니라 `개발 운영 체계`로 다룬다.

요약하면, 이 하네스는 이 프로젝트의 핵심 기능을 대신해주지는 않지만, 장기 개발과 리서치 작업을 덜 흔들리게 만드는 데는 분명히 도움이 된다.
