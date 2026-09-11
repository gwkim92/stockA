# 인계

브랜치: fiture/research-automation. 자동화 기능과 로컬/운영 읽기 검증을 구현했다. 배포와 실제 반복 실행 증거는 후속으로 추가한다.

- 신규 CLI: `research-maintenance-run --env-file <ENV> --artifact-root <RUNTIME>/research-automation-artifacts [--execute]`. 날짜 기본값은 UTC 오늘이다.
- 신규 systemd profile: `research-maintenance`, 매일 America/New_York 00:20/06:20/12:20/18:20, 1회 최대 3기업.
- 부모 pipeline: research_maintenance. 기업별 원자적 갱신 receipt: research_statement_refresh.
- DB 내부 변경 전 백업: 기업별 ops.pipeline_run.config_json.backup_before. 공개 응답·안전한 최근 상태: artifact root/research-maintenance.
- 신규 API 보조 필드: `/api/data-health.research_maintenance`. 실제 큐 개수는 최근 완료 시점의 값이다. 기존 pipeline_runs에도 새 job이 포함된다.
- 다음 계획과 수작업 구분: automation-inventory.md.
- 미관련 dirty 문서와 이전 pilot 파일은 수정/재실행하지 않았다.

## 2026-09-11 07:13 UTC 진행 중 상태

- PR #62, head `405cdab8cb603065253fe652dab74cb1e9bd6821`. financial-period, AI 계약 Python 3.11/3.13, PostgreSQL cutoff/atomic, history CI 통과. Web Product Quality는 Chromium/WebKit 설치 중이며 아직 merge하지 않았다.
- 운영 코드를 바꾸기 전 분리 빌드를 `/opt/stockanalysis/runtime/research-automation-20260911/build`에서 시작했다. `/tmp/stocka-research-activate.py <head> --prepare`는 개인 계정과 기존 develop/깨끗한 checkout을 확인한 뒤 feature object를 fetch하고 별도 웹 소스·node_modules를 준비한다. 서비스 중지·코드 교체·타이머 설치는 prepare 모드에서 수행하지 않는다.
- 이 빌드 도중 웹·새 SSH 연결 응답이 멈췄다. 자원 압박이 의심되지만 ps/free 응답을 아직 받지 못했으므로 OOM으로 확정하지 않는다. 이전 배포 문서에는 2GiB 임시 swap을 사용한 기록이 있었으나 이번 분리 빌드에는 메모리 제한/swap을 준비하지 않은 것이 운영 준비의 누락이다.
- 기존 터널은 PID 35009, socket `/private/tmp/stocka-model-live-20260910.sock`, 13309→3000. 이 연결로 자원 조회 및 **이번 build 디렉터리가 cwd인 프로세스만 종료**하는 명령을 전달했으나 아직 실행 응답을 확인하지 못했다. 기존 터널을 삭제하거나 종료하지 않는다.
- AWS 콘솔을 Chrome 탭 1527793586에 열었으나 로그아웃 상태다. 사용자에게 개인 계정 115623963546 로그인을 요청했다. 회사 계정/AWS CLI write/EC2 재부팅은 수행하지 않았다.
- 먼저 서버 응답을 복구하고 실제 서비스 상태·빌드 로그·메모리를 확인해야 한다. 같은 빌드를 다시 실행하지 않는다. 재빌드는 프로세스 전체에 메모리/CPU 제한을 적용하거나 CI 결과물을 사용한다. 그 다음 CI 완료→정확한 develop merge→활성화→2회 반복 실행 검증을 이어간다.
- `verify_runtime.py`는 아직 실행하지 않았다. source/정규화/추천/보유/과거 성과의 보호 hash와 두 차례의 서로 다른 6개 기업 갱신을 검증하도록 준비한 파일이다.

## 2026-09-11 07:29 UTC 추가 상태

- 운영 무응답은 미해결이다. 새 SSH는 banner exchange timeout, 기존 master는 broken pipe를 반환했다. 이번 build cwd만 종료하려던 명령도 연결 실패하여 종료를 확인하지 못했다. prepare 호출의 로컬 SSH 세션이 남아 있다는 사실은 원격 빌드 생존/종료의 증거가 아니다.
- Chrome recovery 탭 1527793586은 AWS Sign-In, 기존 개인 IAM 탭도 로그아웃 상태다. 사용자에게 개인 계정 115623963546 로그인을 요청한 상태다. 로그인 확인 없이 회사 AWS 계정 또는 CLI write로 복구하지 않는다.
- 로컬 Docker Linux/amd64 빌드는 완료됐다. `/tmp/stocka-research-linux-build/web-linux-next.tar.gz`, 같은 디렉터리 `linux-build-manifest.json`. Source commit `405cdab8cb603065253fe652dab74cb1e9bd6821`, apps/web tree `ec9d127f9df598d9ac94e2220c2895608cbd0ff1`, archive SHA256 `b433e3a28e826a6c0950ba13169bb64150825c6a81f1e1e227bce7dd4fd91d80`, build ID `n6gifU6rercsc47m2xoTj`. 제한은 2 CPU/2GB/no swap/256 PIDs/900초다. 로그 `/tmp/stocka-research-linux-build.log`, 로컬 build 컨테이너는 `--rm`으로 정상 종료됐다.
- **원격 `/tmp/stocka-research-activate.py`는 여전히 예전 무제한 빌드 버전이다. 다시 실행하지 않는다.** 현재 task의 `activate.py`는 외부 Linux 결과물+manifest 없이는 중단한다. SHA256, 소스 tree, 플랫폼, build ID를 확인한 후 활성화한다. 복구 후 최신 script와 두 artifact를 BASE로 다시 전달해야 한다.
- 코드 적용 전 서버의 ps/free, 이번 build.log, 서비스, 활성 타이머, 실제 HEAD와 `.next/BUILD_ID`를 확인한다. 원인이 확인되지 않은 채 OOM으로 단정하거나 같은 빌드를 재시도하지 않는다.
- `verify_runtime.py before` → research-maintenance service 2회 → `verify_runtime.py after` 순서의 검증 동안 다른 타이머 실행이 보호 데이터 hash를 바꾸지 않도록 활성 타이머 목록을 저장하고 잠시 정지한다. 이미 실행 중인 작업은 종료를 기다리고, 검증 실패 여부와 관계없이 기존 타이머를 복원한다. 소스 실패나 불확실 상태가 있으면 즉시 재실행하지 않고 receipt부터 읽는다.
- CI 웹 재실행 run 34572074012 attempt 2는 success로 완료됐다. `405cdab8`의 모든 CI 통과를 확인했다. 이후 변경은 task의 배포 보호/검증 스크립트와 문서뿐이며 문법 검사 및 git diff 검사를 통과했다. PR #62는 merge/배포하지 않았다. 후속 작업에서 최신 head의 완료된 검증을 먼저 읽고 merge 여부를 결정한다.
