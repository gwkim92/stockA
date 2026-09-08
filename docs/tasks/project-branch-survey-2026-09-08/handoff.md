# 조사 인계

- 사용자 요청: `gwkim92/stockA` 프로젝트 이해와 모든 브랜치 조사.
- 초기 폴더는 비어 있었다. HTTPS clone 후 기존 정책의 통합 기준인 `develop`을 checkout했다. 현재 HEAD는 `1d9d8dcc3699152a1fe435a304d95d96d930b9b1`이다.
- 결과: `report.md`에 아키텍처·동작·저장·운영·리스크·검증 범위, `branches.md`에 원격 51개 브랜치 전체 목록을 기록했다.
- Git 분류: 46 ancestor, 3 squash merged with identical merge tree, 1 integration baseline, 1 pending. Pending은 PR #49, head `745bef3340f316bb843bc4e1d50fe33d39f553b0`, develop +13/-0이다.
- GitHub 현재-head check: PR #49 두 workflow 모두 성공. 이력 API만 구현, UI·hash 재검증·나중 outcome 비교는 남아 있다.
- 로컬 검증: analysis integrity 93 + CLI 107 + guarded research display 123 = 323개 통과. Python 3.14.5. 로그와 JSON을 같은 폴더에 보관했다. Display runner는 결과 출력 ROOT만 조사 폴더로 지정했으며 소스 코드는 수정하지 않았다.
- 수행하지 않은 것: 기능 코드 수정, merge/push, dependency 설치, 웹 build/browser QA, 실DB/EC2 접속, 모델·공급자 호출, 스케줄러 실행, 거래. 실제 운영 상태는 확인하지 않았다.
- 저장소의 `AGENTS.md`·로드맵에는 과거 상태가 누적되어 있다. 후속 live 작업은 현재 개인 AWS 계정·환경·배포 ref를 별도 확인해야 하며 과거 IP·성과일·gate 수치를 현재 값으로 사용하면 안 된다.
- 변경 범위: 이 조사 task 폴더만 untracked 상태로 남긴다. 커밋·배포하지 않는다. 원격 refs와 증거 파일을 사용하면 기능 브랜치를 다시 checkout하지 않고 다음 작업을 이어갈 수 있다.
