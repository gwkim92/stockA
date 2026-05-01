# Task Directories

이 디렉터리는 작업별 아티팩트를 누적하기 위한 위치다.

각 작업은 아래처럼 자기 디렉터리를 가진다.

```text
docs/tasks/<task-slug>/
  contract.md
  handoff.md
  plan.md
  feature_list.json
  progress.md
  init.sh
  review.md
  qa.md
  roles.md
  topology.md
  evidence/manifest.json
  loop_contract.md
```

모든 파일이 항상 필요한 것은 아니다.

기본값:

- `contract.md`
- `handoff.md`

필요할 때 추가:

- `plan.md`
- `feature_list.json`
- `progress.md`
- `init.sh`
- `review.md`
- `qa.md`
- `roles.md`
- `topology.md`
- `evidence/manifest.json`
- `loop_contract.md`

새 작업 디렉터리는 `scripts/new-task.sh`로 생성하는 것을 권한다.

장기 작업에는 `feature_list.json`, `progress.md`, `init.sh`, `evidence/manifest.json`을 함께 두는 편이 좋다.

이미 존재하는 task에 plan, review, qa, long-running 문서를 나중에 추가하려면 `awh task augment <slug>`를 사용한다.

`awh task augment`는 기본적으로 missing 파일만 추가한다.

`awh verify`와 `awh export`는 파일 존재만이 아니라 핵심 내용이 실제로 채워졌는지도 본다.

특히 `feature_list.json`과 `evidence/manifest.json`이 있으면 placeholder 값이나 빈 필수값도 실패로 본다.

## Project Conventions

- task slug는 `kebab-case`를 사용한다.
- 문서/아키텍처 작업도 멀티파일이거나 다음 세션으로 이어질 가능성이 있으면 task를 만든다.
- 첫 task는 `foundation-architecture`이며, 현재 프로젝트 정체성, 하네스 도입, 다음 설계 단계 고정을 담당한다.
- 다음 큰 설계 작업은 `db-schema-design`, `data-backbone-bootstrap`, `cycle-engine-v1`처럼 결과물이 드러나는 이름을 권장한다.
