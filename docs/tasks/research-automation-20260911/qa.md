# 운영 완료 업데이트 — 2026-09-11 09:10 UTC

PR #62/#63을 포함한 develop `502eb6795dbcd328ea5a9b6bc6aa503be0061408`를 복구한 t3.large에 외부 CI 결과물로 배포했다. research-maintenance 서비스 두 번 실행 parent 23865/23869, A/ADBE/ADI/ADSK/AEIS/ALAB 6기업 성공, backup_before 6개와 보호 DB fingerprint 불변을 확인했다. 큐는 fresh 9/due 23, 기존 타이머와 신규 timer 총 14개를 복원했다. 실제 Chrome data-health에서 재무 자료 자동 점검·갱신 성공 #23869를 확인했다.

배포 manifest_record 필터와 검증 SQL ORDER BY 괄호 오류를 수정했다. 배포는 checkpoint에서 마지막 unit 설치만 재개했고, SQL 수정 후 수집을 다시 실행하지 않고 저장된 결과를 검증했다. 자세한 복구·검증·남은 범위는 `../runtime-resource-guard-20260911/handoff.md`와 `evidence/`를 따른다. 새 AI 실제 호출 및 원천에서 전문 분석으로 즉시 전파는 이번 검증 범위 밖이다.

---

## 이전 진행 기록 (당시 상태)

# 검증

- 로컬 PostgreSQL 및 Python 회귀: 140개 통과. 원자적 원천/정규화/완료 기록, 변경 전 백업, 중간 실패 rollback, 실행 중 행 잠금, 중단 후 대조, 큐 최신성/구정책/24시간 대기, AI 순환·당일 건 제외·5개 예약 한도 포함.
- CLI·frontend read adapter: 214개 통과.
- Frontend API contract script 통과.
- Next typecheck/build 및 실행 이력 컴포넌트 2개 검사 통과.
- 운영 읽기 전용 preview: 개인 계정/instance 확인, 추적 기업 32개, 갱신 대상 29개, 정상 정책 3개. 새 data-health SQL 정상. AI 보고서 5개 입력 준비/preview 모두 정상, 실제 모델 호출 0회.
- 운영 배포·실제 반복 실행·Chrome 화면 검증: 진행 중. 완료 후 증거를 추가한다.
- PR head `405cdab8`의 CI 전부 통과: financial-period, AI 계약 Python 3.11/3.13, PostgreSQL cutoff/atomic, history, Web Product Quality. 웹 CI 첫 시도는 Ubuntu 패키지 다운로드 지연으로 취소됐으며 run 34572074012 attempt 2는 success로 완료됐다. 이후 task의 배포 보호 스크립트와 문서만 보완했고, 두 Python 운영 스크립트의 문법 및 git diff 검사를 통과했다. 이후 head의 CI는 별도 확인해야 한다.
- 운영과 분리된 로컬 Docker Linux/amd64 빌드 통과: Node 22, CPU 2개·메모리 2GB·swap 0·프로세스 256개·900초 제한. 결과물 3,661,308 bytes, build ID `n6gifU6rercsc47m2xoTj`. 실제 운영 활성화·실행 증거는 아니다.
- 운영 서버 무응답은 미해결이다. 새 SSH 연결은 banner exchange timeout, 기존 tunnel master는 broken pipe를 반환했다. 운영 빌드 종료 명령의 전달/실행은 확인되지 않았다. AWS 콘솔 개인 계정 로그인 대기 상태이며 AWS write/재부팅은 수행하지 않았다.
