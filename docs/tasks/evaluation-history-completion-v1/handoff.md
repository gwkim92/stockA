# 평가 이력 마무리 및 브랜치 정리

2026-09-08 사용자 요청: 완료 브랜치 정리, 조사에서 확인한 남은 작업 마무리.

## 완료 범위

- PR #49를 `develop`에 merge했다 (`44e7f4058fc6c5ecd915a24f75d4659e197d93b5`). 전체 사전 Git bundle을 만들고 검증한 후, 도달 가능한 이력 또는 동일한 squash tree가 확인된 기능 브랜치 49개를 expected-SHA lease와 atomic push로 삭제했다. `main`/`develop`은 유지했다. 삭제 전 이름·SHA·근거는 `deleted-branches.json`에 있다.
- 백업은 이 로컬 checkout의 `.git/stocka-before-branch-cleanup-2026-09-08.bundle`에 있다. 복구할 때는 이 bundle의 `refs/remotes/origin/<branch>`를 별도 로컬 브랜치로 fetch할 수 있다. 원래 기록은 `docs/tasks/project-branch-survey-2026-09-08/`에 유지했다.
- 기존 평가 이력 API의 frozen-only 계약은 유지했다. 현재 상태를 읽는 경로는 별도 `GET /api/recommendation-evaluation-comparisons/eval-run-<ID>?limit=25&after=<snapshot ID>`로 추가했다.
- `/performance/evaluations` 목록, `/performance/evaluations/[runId]` 상세를 추가하고 보유·성과 탭에서 연결했다. 목록/상세의 keyset 페이지 이동, 잘못된 ID, 없는 평가, legacy 상세 없음, 기록 수 불일치, 현재 원천 누락/사용 불가, 손상 상태를 구분한다.
- writer와 같은 canonical JSON 규칙으로 받은 페이지의 snapshot SHA-256을 다시 계산한다. 복사된 점수/판단/원천 식별자가 hashed payload와 충돌해도 불일치 처리한다. 검증되지 않은 기록으로는 현재 비교를 표시하지 않는다.
- 추천 판단·점수·상태·제안 비중·thesis 연결과 thesis 제목·요약·상태·확신도·무효화 조건을 비교한다. 현재 자료 조회가 실패해도 frozen 기록과 hash 검증 결과는 유지한다.
- 후속 성과는 평가 기준일 이후 종료되고 미래가 아닌 동일 관찰 기간의 최신 결과다. snapshot에 선택된 outcome 기간이 있으면 그 기간, 없으면 평가 run의 horizon을 사용한다. 두 시점 사이의 추가 수익률로 해석하지 않도록 기간·benchmark·초과수익(%p)을 함께 표시한다.

## 검증

- Python 3.13 / backend unit·HTTP·기존 reader·API server: 72개 통과.
- 기존 analysis integrity 93개 + 운영 CLI 107개 통과.
- 별도 생성한 로컬 PostgreSQL 16에 기존 migration 35개를 적용: 실제 pool·읽기 권한·쓰기 거부·source 변경/삭제·해시 불일치·현재 읽기 실패·미래/다른 기간 outcome 제외 포함 10개 통과.
- 웹 Vitest: 40개 파일, 517개 테스트 통과.
- Next.js production build 및 typecheck 통과.
- 실제 Chromium: 17개 상태 × 1440/768/390 너비 = 51개 화면, 목록·상세 페이지 이동, bigint 링크, 펼치기, 오류/누락/무결성 상태, axe 접근성, 가로 overflow, GET-only 요청 확인.
- 기존 보유/성과 브라우저 회귀: desktop/mobile 36개 통과.
- visual-qa 두 독립 read-only 검토가 전체 캡처를 직접 확인했다. 스크롤 캡처의 고정 header 위치는 scroll reset으로 보완했고, 경고 문구의 CSS 우선순위를 수정했다.
- 신규 Python 및 브라우저 검증을 기존 GitHub workflow에 연결했다. 로컬 검증은 `verification.json`, 최종 원격 반영·CI 결과는 GitHub PR과 로컬 `artifacts/evaluation-history/integration.json`에 기록한다.

브라우저 증거는 로컬 `artifacts/evaluation-history/browser/`에 있으며 CI에서도 artifact로 보관한다. reference 화면은 기존 성과 화면의 디자인 체계 기준이다. 다른 페이지 본문과의 pixel diff 53/100은 새 화면의 구조 차이를 수치화한 값이며 동일 화면 복제 점수가 아니다.

## 수정 과정과 범위

초기 검증에서 typed Next 링크, 새 PostgreSQL fixture의 issuer/exchange 필수값, API 테스트 factory 인자명, Playwright/axe context 생성 및 브라우저 설치 요구를 확인하고 수정했다. 실패를 최종 통과로 합산하지 않았다. 마지막 작은 화면 수정 후 build/type/전체 웹 단위/51상태 캡처를 다시 실행했다.

실서버 배포·실DB migration·runtime 데이터 갱신·모델 호출·주문·추천 weight/benchmark/schema 변경은 수행하지 않았다. 실운영 데이터 커버리지와 성과의 유효성을 확인한 결과로 확대 해석하면 안 된다. 비교는 명시한 필드 범위이며 raw snapshot 자체는 별도로 보존된다. 해시는 현재 저장 payload의 동일성 검증으로, 추천 생성 당시 provenance 또는 외부 공증을 제공하지 않는다.

계정 선택: 기본 gh 계정은 woodyBlocks였다. 기존에 로그인된 gwkim92 credential을 명령 범위에만 사용했고 전역 활성 계정은 바꾸지 않았다. repo 지정 SSH 키는 `IdentitiesOnly=yes`와 함께 사용해야 ssh-agent의 다른 계정 키가 먼저 선택되지 않는다.
