# 현재 인계 — 2026-09-11 09:10 UTC

## 완료한 운영 변경

- 사용자 로그인/증설 승인 후 Chrome 콘솔에서 개인 계정 `115623963546`, us-east-1, `i-029d51b163fb07b61`을 재확인했다. 정상 중지 → EBS 스냅샷 요청 → t3.large 변경 → 시작을 수행했다. 강제 종료나 AWS CLI write는 하지 않았다.
- t3.small 2GiB → t3.large 8GiB, vCPU 2개. EIP `3.211.40.142`와 EBS `vol-05dfffff20cdf8923` 16GiB를 유지했다. 스냅샷 `snap-0ee7a1fb382ee9555`는 100%/완료됨이다.
- 콘솔 Linux 요금은 $0.0208/h → $0.0832/h였다. 월 730h 컴퓨팅만 약 $15.18 → $60.74, 증가 약 $45.55. EBS·스냅샷·IPv4·트래픽·CPU surplus는 별도다. 앞서 공식 제품표의 근사치와 소액 차이가 있으며 실제 청구는 Billing을 따른다.
- SSH 복구 후 `inspect_host.py`로 IMDS 개인 계정/인스턴스/유형을 확인했다. 현재·직전 부팅에 OOM/blocked I/O 커널 기록은 없었다. 원인은 확정하지 않는다. 최근 두 번의 공통 촉발점은 운영 호스트의 무제한 Next 빌드이며 9월 10일 외부 빌드 지시를 11일에 지키지 못한 운영 실수다.
- 운영 develop `6b019ff3` → `502eb6795dbcd328ea5a9b6bc6aa503be0061408`. PR #62/#63 CI를 통과한 Linux 결과물의 source tree·SHA·lock hash·BUILD_ID를 검증해 배포했다. 운영 컴파일 0회. Build ID `WcwTXPpZJZtUkdFHyJ8-t`.
- FastAPI readiness와 웹 두 프로세스의 `/data-health` 모두 200, 서비스 3개 active. 인증 env 3개 및 AI 설정 SQLite hash 유지. 스키마·추천 weight·포트폴리오·실거래 경계는 변경하지 않았다.
- 실제 운영 경로에서 `npm run build`를 실행해 exit 1과 `No compiler was started`를 확인했다. 직접 Next CLI 우회까지 OS에서 차단하는 기능은 아니다.
- 기존 무제한 `/tmp/stocka-research-activate.py`는 복구 후 확인 시 이미 없었다. 이번 정리 작업에서 별도 archive를 생성하지 않았으며, 해당 경로는 재실행하지 않는다.

## 배포/검증 중 수정한 문제

- activate.py가 생성기 반환 목록의 `manifest_record` JSON까지 systemd unit으로 취급했다. 소스와 `.next` 교체 후 마지막 단계에서 assert로 중단됐고 finally가 서비스와 기존 타이머를 복원했다. manifest record를 건너뛰도록 교정했다.
- 원래 스크립트를 재실행하지 않았다. `finish_activation.py`는 정확한 checkpoint·HEAD·build·설정 hash를 확인하고 생성된 두 systemd 파일 설치 단계만 완료했다. 서버의 `activation.json`에 재개 구간이 기록됐다.
- `verify_runtime.py`의 jsonb_agg ORDER BY 괄호 오류를 고쳤다. 수집을 다시 실행하지 않고 `/tmp/stocka-verify-research-runtime.py after`로 동일 baseline/receipt를 읽어 검증했다. 보호 데이터 hash 비교는 첫 검사에서도 통과했고 수정 후 전체 검증도 통과했다.

## 실제 자동화 검증

- 설치된 research-maintenance service를 연속 두 번 실행했다. parent `23865`, `23869` 모두 succeeded; child `23866/23867/23868/23870/23871/23872` 모두 succeeded.
- A/ADBE/ADI → ADSK/AEIS/ALAB, 서로 다른 6기업, 합계 1,887 financial facts. 모든 child에 같은 DB의 변경 전 백업이 있다. 원천 정책 `sec-statement-duration-v2`, 최신 queue 9개 fresh/23개 due/0 retry_wait/0 reconcile.
- 추천·score component·보유 snapshot·benchmark·기존 outcome·AI report·대상 외 원천·과거 정규화의 DB fingerprint 일치를 확인했다.
- 검증 전 활성 timer 목록을 저장하고 일시 정지, 두 실행 뒤 14개 모두 복원했다. 이 숫자는 데이터 profile 13개와 scheduler-status 1개다. 전체 정의 profile은 15개이며 기존 KR reference/candles 두 profile은 비활성이다. 임의 활성화하지 않았다.
- 신규 timer 다음 시각은 2026-09-11 10:20 UTC/19:20 KST. 매 6시간 3기업, 최신성 7일, 실패 후 24시간 대기.
- scheduler-status service를 갱신했다. `/api/data-health`의 실제 envelope는 `.data.research_maintenance`이며 succeeded/23869를 확인했다. 전체 overall_status는 attention_required다.
- Chrome `http://127.0.0.1:13309/data-health` 실제 로드/접힌 상세 열기/실행 행 클릭과 캡처 완료. `재무 자료 자동 점검·갱신`, `성공`, `정상`, `실행 #23869`를 확인했다. 터널 socket `/private/tmp/stocka-model-live-20260910.sock`을 복구했다.
- 실제 수집 후 09:08 UTC: 총 7,823MiB, 가용 6,774MiB, 메모리 PSI 0, load 0.27/0.42/0.22, 디스크 67%/가용 5.4GiB. 이는 짧은 canary 후 상태이며 장기 부하 검증은 아니다.

## 근거와 남은 범위

- `evidence/resize.json`, `host-after-resize.json`, `host-after-canary.json`, `activation.json`, `research-canary.json`, `api-after.json`, `verification.json`에 비밀 값 없는 근거를 저장했다.
- 실제 unit의 MemoryMax/MemoryHigh/CPUQuota/TimeoutStart는 아직 infinity이며 PostgreSQL container도 별도 메모리 상한이 없다. 운영 빌드 차단과 8GiB 증설을 배치 전체의 자원 격리 완료로 표현하지 않는다.
- 스냅샷은 보관 중이다. 실제 복구 리허설·보존 기간 자동 관리는 후속 작업이다. 다음 작업에서 무조건 삭제하지 않는다.
- API의 남은 open gates: alert_destination, data_operations_artifact_runner 및 기존 성과/검토 관련 항목. 기존 표본/평가/추천 weight를 바꾸지 않는다. 새 AI 실제 호출/보고서 재생성은 이번 canary에 포함하지 않았다.
- 다음 우선순위: 작업별 자원/동시 실행/무진행 감시 → SEC 성공 receipt에서 전문 분석과 보고서 원천 버전 전파 → 중단 단계 재개와 백업 보존 자동 관리. KR 비활성 profile과 화면의 오래된 activation 표시는 실제 범위와 대조 후 분리한다.

---

# 이전 진행 기록 (아래 미완료 표시는 당시 상태)
# 인계

- branch: fiture/runtime-resource-guard, base develop fd8226630f3a9f26cdc7898e2e700239eac94f1d (PR #62 merged). 앞선 자동화 코드는 아직 서버에 활성화하지 않았다.
- 개인 AWS recovery Chrome tab 1527793616은 로그인 화면이다. 사용자에게 계정 115623963546 로그인을 요청했다. 기존 IAM 탭 1527793408에도 로그아웃 overlay가 있다. AWS write 또는 재부팅은 이번 턴에 수행하지 않았다.
- 원인 증거: docs/tasks/ai-model-settings-v1/handoff.md의 Recovery and deployment evidence에 9월 10일 동일 Next 서버 빌드 무응답/재부팅 복구가 있다. 당시 OOM 로그가 없었고 이번에도 커널 로그를 읽지 못했으므로 메모리 고갈로 확정하지 않는다. 별도 수집 payload 확대 문제는 docs/tasks/tossinvest-shadow-daily-resource-guard-v1/handoff.md에 기록돼 있다.
- 표준 npm build를 보호하고 기존 CI runtime artifact의 자동 trigger와 source/integrity manifest를 추가했다. 이전 research-automation activate.py도 해당 CI manifest를 사용할 수 있다.
- 복구 후 inspect_host.py를 기존 venv Python으로 실행하여 bounded read-only 증거를 얻는다. 이전 remote /tmp/stocka-research-activate.py는 무제한 build 버전일 수 있으므로 절대 재실행하지 말고 새 파일을 업로드한다.
- 우선순위는 서버 복구 → 실제 자원/동시 작업/로그 확인 → CI 결과물 배포 → research-maintenance 두 차례 실행/보호 데이터 검증/원래 타이머 복원/웹 확인이다. 로그인 없이 회사 AWS 계정이나 로컬 AWS CLI write로 대체하지 않는다.
- PR #63 head `8f9c02c0f7b802c88af29b7583b99ea7b817afc1`. 자동 artifact CI run 34579004209 성공. 전체 브라우저 CI run 34579004245는 진행 중이다.
- 검증한 새 artifact: `/tmp/stocka-resource-guard-ci/web-runtime-800a327e97cd29efeb7be91248d8fbebffe9bd94/`의 `web-runtime.tar.gz`와 `linux-build-manifest.json`. Build ID `WcwTXPpZJZtUkdFHyJ8-t`, web tree `1cc01b1944658ac6f7b85b73525a88b9fdb508e0`, SHA256 `89998f05d43e2528e05f1da0e1c71654cbde49fe5dfa34d9fb04f6f6b5f9f597`, 3,671,147 bytes. PR merge checkout source `800a327e97cd29efeb7be91248d8fbebffe9bd94`의 결과물이며 head와 web tree 일치를 확인했다. 다른 source로 배포할 때 다시 대조한다.
- 이전 `/tmp/stocka-research-linux-build` artifact는 새 build guard 파일/package script가 없는 이전 web tree다. PR #63까지 배포한다면 새 artifact를 사용한다.

## 08:35 UTC 최종 인계

- PR #63 head 8f9c02c0의 모든 CI 통과를 확인한 뒤 develop `502eb6795dbcd328ea5a9b6bc6aa503be0061408`로 병합했다. PR #62와 #63 모두 병합됐지만 운영 배포/복구는 미완료다.
- Chrome recovery tab 1527793616은 여전히 AWS Sign-In/빈 이메일 입력 화면이다. 사용자에게 개인 계정 로그인을 요청한 상태이고, AWS 재부팅/write는 수행하지 않았다. 새 SSH도 여전히 banner timeout이다.
- 운영 호스트에서 복구 이후 사용할 script는 현재의 research-automation activate.py와 runtime-resource-guard inspect_host.py다. API/web/DB 프로세스 종료 여부, 커널 OOM, 실제 resource limit은 아직 확인하지 못했다. 웹의 외부 13000 직접 timeout은 기존에도 있던 네트워크 경계이므로 이번 장애 원인 증거로 쓰지 않는다.
- 분석은 incident-analysis.md에 저장했다. CI 결과/로그/manifest 대조는 완료했으며 다음 실제 행동은 개인 계정 인증 후 EC2 상태/시스템 로그 확인과 필요한 재부팅 복구다.

## 로그인·증설 승인 후 진행

- 사용자가 로그인과 필요한 서버 증설을 명시적으로 승인했다. 새 Chrome tab 1527793632에서 개인 계정 115623963546/us-east-1/i-029d51b163fb07b61/EIP 3.211.40.142를 확인했다.
- 변경 전 AWS 상태 검사 3종(시스템/인스턴스/EBS)은 통과했다. 루트 볼륨은 EBS vol-05dfffff20cdf8923, 16GiB, /dev/xvda다. 콘솔 시스템 로그는 9월 10일 09:02 UTC 부팅과 이전 swap 기록을 포함하지만 이번 OOM 증거는 보이지 않는다.
- t3.small 2GiB → t3.large 8GiB 계획을 알렸다. Linux us-east-1 on-demand 표 기준 730시간 약 $15.26 → $60.96 (스토리지/IP/트래픽 및 CPU 추가 요금 별도). 기존 EIP/EBS/아키텍처를 보존한다.
- 콘솔에서 OS 종료 건너뛰기를 선택하지 않고 해당 인스턴스 중지를 한 번 요청했다. 성공 알림과 상태 ‘중지 중’을 확인했다. 아직 완료된 중지/유형 변경/시작으로 보고하면 안 된다.
