# 검토

- 9월 10일 인계에는 동일 서버 빌드 무응답과 외부 빌드 사용 지시가 있다. 9월 11일 그 운영 지침을 놓쳐 같은 방식으로 빌드를 시작했다. 반복된 운영 준비 누락은 확인됐으며 정확한 커널 원인은 미확정이다.
- 차단은 npm의 optional prebuild hook이 아니라 build 명령 본체에서 실행한다. `/opt/stockanalysis`의 live/staging 경로와 Amazon EC2 DMI vendor를 확인하며 IMDS/인증 정보에 접근하지 않는다. 다른 진입점으로 직접 Next CLI를 실행하는 행위까지 OS 차원에서 차단하는 것은 아니다.
- 기존 Web Runtime Artifact workflow를 재사용하며 웹 변경 PR/develop push에서 자동 실행한다. 운영 자격 증명을 CI에 추가하지 않는다. artifact는 빌드만 포함하며 자동 배포/재부팅을 수행하지 않는다.
- package.json의 build script만 바꾸고 dependency lock은 유지한다. 활성화 검사는 schema/Python/lock 변경 차단을 유지하고 실제 의존성·Node 요구 조건을 별도로 대조한다.
- 신규 inspect_host.py는 개인 IMDS identity를 확인한 다음 시간 제한이 있는 읽기 명령만 실행한다. 프로세스 전체 arguments, runtime env, 임의 애플리케이션 로그와 개인 DB row를 출력하지 않는다.
- 수집 프로필 generator에는 현재 MemoryMax/CPUQuota/TimeoutStartSec가 없다. 이것만으로 실제 설치 unit에 override가 없다고 단정하지 않는다. 복구 후 live unit과 DB 컨테이너 사용량을 확인해야 하며, Docker DB는 서비스 프로세스의 memory cgroup으로 제한되지 않는 점도 고려한다.

참조: [GitHub workflow trigger/filter](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow), [npm script 실행 규칙](https://docs.npmjs.com/cli/v11/using-npm/scripts/).
