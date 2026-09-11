# 최종 검증 — 2026-09-11

- 개인 AWS console/IMDS 교차 확인, t3.large 8GiB/2vCPU, EIP/EBS 유지. EBS snapshot completed 100%.
- 서비스 3개 active, API readiness 및 웹 3000/13000의 data-health 200. 서버 env/AI 설정 hash 불변.
- CI Linux artifact source tree/SHA256/lock hash/BUILD_ID 검증 후 develop 502eb679 배포.
- 운영 npm build 음성 검사: exit 1, 컴파일 시작 전 차단.
- 설치된 재무 수집 service 2회 성공, 서로 다른 6기업, 부모 2/자식 6 receipt, 변경 전 백업·보호 데이터 fingerprint 검증 통과. 보고서 SQL 구문 수정 후 읽기 검증만 재실행했으며 수집 재실행 없음.
- 타이머 14개 원복, 다음 research-maintenance 10:20 UTC. 데이터 profile 13/15 active, KR 두 profile 비활성은 기존 상태.
- Chrome 13309/data-health 실제 렌더, 실행 로그 펼치기, 성공 #23869 행과 screenshot 확인.
- 수집 후 가용 메모리 6,774MiB, 메모리 PSI 0. 커널 OOM 증거 없음. 짧은 실제 실행 검증이며 장기 무장애/피크 부하 보장은 아니다.
- 배포 복구·검증 script Python 문법 및 실제 checkpoint/SQL 실행 통과. 세부 근거는 evidence/와 handoff.md.

## 이전 코드/CI 검증 기록

# 검증

- build guard 7개 통과: live/staging/정규화 경로, 다른 EC2 checkout 차단, 개발·GitHub runner·Docker build 경로 허용.
- 활성화 스크립트 Python 문법, git diff 검사 통과.
- 로컬 실제 npm build와 타입 검사 통과. build가 새 보호 진입점을 거쳐 정상 완료됐다. CI 검증은 PR에서 진행한다.
- 서버: SSH banner exchange timeout 재확인. AWS Chrome 콘솔 로그아웃 상태, 개인 계정 로그인 요청 중. 복구/운영 활성화/자원 측정 미완료.
- PR #63의 Linux artifact CI run 34579004209 성공. 실제 내려받은 archive SHA256, source tree, package lock SHA256, BUILD_ID, linux/amd64 및 cache 제외를 검증했다. 결과 `/tmp/stocka-resource-guard-ci/verification.json`.
- YAML parser의 로컬 Python 환경에는 PyYAML이 없어 Ruby YAML parser로 구문을 확인했고, 실제 GitHub workflow 실행도 통과했다.
- 최종 head 8f9c02c0의 Web Runtime Artifact와 Web Product Quality 모두 success. 전체 브라우저 CI run 34579004245는 08:34:47 UTC 완료됐다. PR #63은 develop 502eb6795dbcd328ea5a9b6bc6aa503be0061408로 병합했다. 서버 배포는 아니다.
