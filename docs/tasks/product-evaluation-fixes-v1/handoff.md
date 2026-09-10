# 수정 결과 인계

현재 branch `fiture/product-evaluation-fixes-v1`, 수정 커밋 `72d59535e3eeae7da06f557979dd560d7247788a`, 시작 develop `80769207`. 평가 10개 항목의 구현·로컬 검증·독립 구현/화면 검토를 완료했다. 수정 범위와 증거는 `contract.md`, `qa.md`, `review.md`를 따른다.

## 검증

Python 195개, 웹 단위 523개, 종목/원천 브라우저 60개, 타입/production build가 통과했다. 추가 display 계약 검사 123개도 외부 I/O 0건으로 통과했다(기존 Python 검사와 일부 중복). 영향 12개 경로를 desktop/mobile로 확인했고 마지막 문구 수정 후 6개 경로를 다시 캡처했다. 실제 페이지 이동, RSS 원천 클릭, 모바일 표의 키보드 스크롤이 통과했다.

운영 데이터는 읽기 전용으로 새 SQL과 대조했다. 과거 재무 forecast/valuation은 재생성하지 않았다. 이전 값의 계보 미검증 상태를 드러내고 새 계산은 같은 매출 기간 입력만 소비한다. 이것은 투자 성능 개선의 증거가 아니다.

## 공개 전송/배포 진행

`gwkim92/stockA`는 공개 저장소다. 작업 커밋의 코드·테스트·평가 문서 51개를 작업 브랜치로 push하는 작업을 자동 승인 검토가 거부했다. 사유는 이 payload를 공개 목적지에 전송하는 명시적 승인이 없다는 것이다. 이후 사용자가 “진행해라”로 공개 푸시 및 CI 통과 후 기존 개인 EC2 배포를 승인했다. 72d59535의 작업 브랜치 푸시가 완료됐고 Linux artifact CI 34479374219는 성공했다. Web Product Quality 34479377494가 실행 중이며 운영 반영은 아직 하지 않았다.

현재 운영 서비스는 기존 `develop@f9f1d5ee`이며 API와 웹 두 서비스가 모두 active다. 승인 후 기존 개인 EC2에만 반영한다. 원격 develop은 조회 시 `80769207`이었다. GitHub 계정은 개인 gwkim92, Git SSH는 지정 id_ed25519_pusan/IdentitiesOnly=yes를 사용한다. Linux CI artifact의 hash·소스·package-lock·build ID 확인, 소스/.next rollback backup, 환경·모델 저장소 보존, API/웹/타이머 및 사용자 터널 확인이 필요하다. 작은 EC2 안에서 Next build하지 않는다.

## 보존한 상태

기존 runtime-deploy-20260908 / runtime-evidence-recovery-20260910 문서 변경은 사용자 작업으로 남겼다. 생성 next-env.d.ts 변경과 Playwright 출력은 커밋하지 않았다. 모든 로컬 증거는 ignored `artifacts/product-evaluation-fixes-v1/`에 있다.

로컬 검토용 API 18779, 웹 13014는 읽기 전용 미리보기다. data-health와 AI 운영 DTO는 기존 운영 API에서 GET으로 읽고, 변경 SQL 경로는 현재 코드를 이용해 운영 DB를 read-only 조회한다. 사용자 터널 13309 및 Chrome 모델 관리자 세션은 유지한다. 모델 Terra/revision 2와 인증·추천 weight·benchmark·주문 설정은 변경하지 않았다.
