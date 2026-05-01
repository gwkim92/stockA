# Repository Working Map

## Purpose

이 저장소의 목적은 거시경제, 정치, 기술, 산업, 기업 흐름을 지속적으로 해석하고 섹터/테마 사이클을 추적하여 중장기 투자 thesis, 추천, 보유 검토, 성과 분석을 지원하는 AI 기반 투자 운영 시스템을 개발, 유지보수, 검증하는 것이다.

에이전트는 아래를 우선한다.

- 낙관보다 정확성
- 큰 수정보다 작고 검토 가능한 변경
- 완료 주장보다 검증 증거

## Repository Map

- 앱 코드: 아직 없음. 초기 구현 후 `src/` 또는 `app/` 아래에 확정한다.
- 테스트: 아직 없음. 구현 후 `tests/` 아래에 확정한다.
- 문서와 설계 노트: `README.md`, `docs/project-foundation.md`, `docs/agent-work-harness-evaluation.md`, `docs/verification-plan.md`, `docs/tasks/`
- 스크립트와 툴링: 아직 repo-local 스크립트 없음. 필요 시 `scripts/` 디렉터리를 도입한다.
- 민감하거나 고위험인 경로: 향후 추가될 실거래 연동, API 키, 배포 설정, 데이터 소스 자격증명 파일

## Core Commands

- 설치: 현재 없음. 초기 Python 프로젝트 골격을 만들 때 확정한다.
- 개발 서버 또는 실행: 현재 없음. 현재 단계는 설계와 작업 하네스 정리 단계다.
- 테스트: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task foundation-architecture`
- 린트: 현재 없음.
- 타입체크 또는 빌드: 현재 없음.
- E2E 또는 스모크: 현재 없음.

## Boundaries

- 생성 파일은 명시적으로 요구될 때만 수정한다.
- 시크릿, 배포 설정, 과금 로직은 명시적 승인 없이 바꾸지 않는다.
- 각 작업은 자기 task directory 범위 안에서 상태를 관리한다.
- 위험한 기술 도입은 직접 치환보다 내부 어댑터와 파일럿 도입을 우선한다.
- 투자 추천 로직은 설명 가능한 규칙과 검증 가능한 평가 체계를 먼저 갖춘 뒤에만 고도화한다.
- 백테스트 기준, benchmark, schema, 평가용 데이터 분할은 명시 없이 바꾸지 않는다.
- 실거래 자동화는 별도 승인 전까지 범위 밖이다.

## Working Rules

- 현재 작업에 필요한 최소한의 문서만 읽는다.
- 멀티파일, 위험 작업, 장기 작업은 먼저 `docs/tasks/<task-slug>/contract.md`를 만든다.
- 세션을 끊기기 전 `docs/tasks/<task-slug>/handoff.md`를 갱신한다.
- 프로젝트 차원의 완료 기준은 `docs/verification-plan.md`로 판단한다.
- `docs/escalation-rules.md`가 있으면 planner, multi-agent, automation 승격 여부를 그 문서로 판단한다.
- UI 작업은 가능하면 실제 브라우저 경로로 검증한다.
- benchmark, schema, evaluation 기준을 건드리면 그 사실을 반드시 명시한다.
- LLM은 추천을 직접 결정하는 존재가 아니라 문서 해석, 이벤트 구조화, 리포트 생성 역할을 우선한다.
- 추천 또는 보유 판단은 당시 입력 데이터, 점수, thesis, 무효화 조건을 함께 저장하는 방향으로 설계한다.
- 문서 단계에서도 다음 구현 단계가 바로 이어질 수 있을 정도로 결정 사항을 명확히 남긴다.

## Definition Of Done

작업은 아래가 모두 충족될 때만 완료다.

- 요청한 변화가 실제로 존재한다
- 필요한 검증이 수행되었다
- 남은 위험과 미검증 영역이 적혀 있다
- 현재 task directory가 다음 사람이 이어받을 수 있을 만큼 갱신되어 있다
- 아키텍처 또는 규칙 변경이면 관련 설계 문서와 task handoff가 함께 갱신되어 있다
