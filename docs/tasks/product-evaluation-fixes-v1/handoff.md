# 수정·배포 완료 인계

2026-09-10 평가의 10개 기능·화면 항목을 수정하고 개인 EC2에 배포했다. 기능 커밋은 `72d59535`, 브라우저 기대 문구 후속 수정은 `7a4d46b7`이다. 배포 당시 develop은 `fd73778a31559f45be46336429d3a822b54af426`이며 CI artifact는 `7a4d46b7f8e93588c44b9264d400f13d76588b21`에서 생성했다. 두 버전의 앱·backend·dependency·DB 경로가 동일함을 검증했다. 이후 커밋은 이 배포의 증거 문서만 갱신한다.

## 실제 접속과 결과

사용자 접속 주소는 http://127.0.0.1:13309 이다. 기존 Chrome 모델 관리자 탭을 새로고침해 Terra, 설정 revision 2, 관리자 권한 및 기존 만료일을 확인했다. 역할 정책의 `실행 상태 미조회`도 반영됐다. 작업별 5개 모델 설정과 인증·환경을 바꾸지 않았다.

실제 API에서 등록 종목 8,038개 전체의 NVDA 검색 1개, 홈 최신 검토 3개, 실행 없는 성과의 not_evaluated/null, NVDA 최신 매출 기간 2026-01-25 및 결측 5개, 기존 DCF/scenario/SOTP의 unverified_legacy를 확인했다. 새 재무 계산은 동일 매출 기간의 입력만 사용하고 기존 forecast/valuation을 소급 재생성하지 않았다.

운영 웹 11개 경로 × 데스크톱/모바일 22건과 두 viewport의 RSS 원천 클릭을 확인했다. 모두 정상 렌더링·문서 가로 넘침 없음이다. NVDA 검색/새로고침, 근거 10개→다음 10개/복귀/새로고침, 인코딩된 원천 링크, 표 내부 키보드 가로 스크롤이 통과했다.

## 검증

- Python 연관 195개, 웹 단위 523개, 타입/production build 통과.
- 전체 Web Product Quality `34480578643` 성공: 검토 노트 168, 투자 화면 66, 보유/성과 36, 원천 읽기 38, 기업/근거 44, 뉴스/테마 42개(합계 394개), 별도 평가 이력 브라우저 검사도 성공.
- Linux runtime artifact `34480582112` 성공. build ID `0rlLlUJzuSCAWSz0Soz6Q`, SHA-256 `f65d9844dc55b4510a11d38656d175264289165dd5ab00d89a84b72a872d15a8`.
- develop 후속 Web Product Quality `34481915252`, Evaluation History `34481915268`, Read Contract `34481915254` CI도 모두 성공했다.

## 배포와 복원

개인 계정 `115623963546`, instance `i-029d51b163fb07b61`, us-east-1을 IMDS로 확인했다. EC2에서 build하지 않고 검증 artifact만 전송했다. 첫 시도는 Next 포트가 열리기 전에 점검이 실행되어 이전 `f9f1d5ee`로 자동 복원됐다. 기동 완료 대기를 보완한 두 번째 시도가 성공했다. 웹 기동 대기 절차의 문제였으며 첫 로그도 보존했다.

API와 웹 두 서비스가 active, API ready=ok, 3000/13000 웹 smoke=200이다. 기존 활성 타이머 13개를 복구했고 최종 systemd 상태도 확인했다. frontend-api.env, web.env, data-operations.env의 hash/mode가 전후 동일하다. 모델 revision 2 / gpt-5.6-terra / override 없음 / mode 0600이 유지됐다. 스키마 migration, 수동 AI 호출, 금융 데이터 재생성, 주문 실행은 하지 않았다.

서버 전용 기록은 `/opt/stockanalysis/runtime/product-evaluation-fixes-v1/` 아래 activation.json, preflight.json, previous-source.tar.gz, previous-next, attempt-1에 있다. 자동 재실행을 막는 activation marker가 있으므로 배포 스크립트를 그대로 재실행하지 않는다. 기존 설정이나 백업을 삭제하지 않는다.

## 남은 운영 상태와 보존한 작업

검증 시점의 데이터 상태 API는 attention_required이며 9개 gate가 남는다. 특히 artifact runner의 7개 항목은 최근 실행 자체는 succeeded지만 기록이 stale인 상태다. 이것을 새 배포 실패나 데이터 정상으로 표현하지 않는다. 저장된 scheduler 요약의 14개/12개와 실제 systemd 활성 13개도 구분한다. 알림 목적지·AI 이력·투자 검토·성과 성숙 관련 주의는 원천 데이터/운영 후속 범위이며 이번 배포에서 배치를 재실행하거나 임의로 닫지 않았다.

기존 runtime-deploy-20260908 / runtime-evidence-recovery-20260910 문서 변경은 사용자 작업으로 남겼다. 생성 next-env.d.ts와 Playwright 출력은 커밋하지 않았다. 로컬 증거는 ignored `artifacts/product-evaluation-fixes-v1/`, 운영 화면 증거는 그 아래 `production/`에 있다. 임시 Postgres는 종료했다. 이전 로컬 미리보기 대신 실제 사용자 터널을 최종 검증에 사용했다.
