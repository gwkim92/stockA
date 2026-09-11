# 인계

재무 원천 변경에 따른 기업 리서치 자동 갱신을 구현하고 운영 배포·실제 모델 생성 검증까지 완료했다.

- PR: https://github.com/gwkim92/stockA/pull/65
- 배포 코드: `47afdd7e8edf4bb9a4d5b3fb812bee7400f206f0` (develop). PR head `7f64e448`와 전체 파일이 동일하며 PR의 CI 9개 및 develop의 6개 workflow가 모두 통과했다.
- 운영: 개인 계정 `115623963546`, us-east-1, `i-029d51b163fb07b61`, `3.211.40.142`, t3.large.
- 배포 시각: 2026-09-11 14:13:23 UTC. Linux Build ID `S6E8C2VuQgS05GOa0Bqno`. 산출물은 CI에서 만들었고 EC2에서 웹 빌드는 실행하지 않았다.
- 실제 생성 검증 시각: 14:17:38 UTC. A / claim23927 / generation23928 / artifact495 / invocation41307 / primary 성공. 실제 모델 `gpt-5.6-terra`, transport에서 관측한 reasoning `none`.
- 같은 A 재실행: `no_op`, 추가 예약·모델 호출 없음. 일일 사용 0→1/5. 입력과 현재 재무 source run은 모두23866이고 API 상태는 `current`다.
- 보호 데이터/환경/모델 설정 보존. 원천 재무 테이블, 추천·점수·보유·benchmark·outcome 및 다른 기업 리포트의 hash가 동일했다.
- API8787, 웹3000/13000 모두200. 양쪽 운영 HTML에 재무 입력 버전 일치 안내가 포함됐다. 기존 timers14개 복원, batch13/13개 보호, 보호 설정 주의0개, 가용 메모리6810MiB.

## 자동 실행 경로

`stockanalysis-operations research-report-refresh-run --env-file <ENV> [--symbol AAPL] --execute`.

기존 research-maintenance의 재무 갱신 후단과 기존 daily reporting이 같은 worker를 사용한다. 운영 profile plan의 두 단계는 `research-maintenance` → `equity-research-reporting`이다. 회당 최대1개, 자동 경로의 UTC 일일5개 한도를 공유한다. 종목 필터는 한도를 우회하지 않는다. 과거 일자로 자동 예약할 수 없다.

성공한 수집의 SHA/기간 정책이 바뀌거나 생성 정책이 바뀌면 대상이 된다. 저장 receipt와 실제 artifact/invocation이 일치하는 결과만 완료로 판단한다. 확인된 fallback은24시간 뒤 기존 한도에서 재시도한다. 불명 결과나 결과 변형은 자동 재호출하지 않고 receipt 대조 상태를 남긴다. 기존 수동 리포트 CLI는 자동 예약 lock 밖의 관리자 실행 경로이며, 그 기록은 기존 as-of-date 기준 예산 계산에 포함된다.

## 배포 중 관측한 문제와 처리

첫 활성화의 사전 검사(14:08:44)에 기존 상태 수집기(14:08:43~14:08:48)가 겹쳐 검사 단계에서 중단됐다. 코드·기존 웹 파일 교체 전임을 commit/Build ID/설정 hash/14개 timers로 확인했다. 기록을 private `attempt-status-overlap/`에 보존한 뒤, timers 중지 직전에 시작된 짧은 작업이 끝나도록 최대30초 기다리는 처리를 적용했다. 긴 배치는 여전히 배포를 막는다. 동일 처리를 canary에 적용하고 모델 호출 전 타이머 체크포인트도 먼저 저장한다.

운영 검증은 일회성 `stockanalysis-research-source-refresh-canary.service`에서 실행했다. 기존 batch slice, 메모리1GiB, CPU1개, 실행900초 제한을 적용했고 `ExecStopPost`가 timers 복원을 실행하도록 구성했다. unit은 `Result=success`, `ExecMainStatus=0`으로 종료했다. 기존 생성 checkpoint가 있으면 그대로 재실행하지 않는다.

## 증거와 복구 자료

로컬 evidence: `ci.json`, `develop-ci.json`, `linux-build-manifest.json`, `preflight.json`, `activation.json`, `live-verification.json`, desktop/mobile 캡처. 브라우저 캡처는 합성 데이터 QA이며 실제 모델 생성 증거는 별도 live JSON이다.

서버: `/opt/stockanalysis/runtime/research-source-refresh-20260911/`. `previous-source.tar.gz`, `previous-next/`, `activation.json`, `canary-started.json`, `canary-first.json`, `canary-second.json`, `canary-verification.json`, `final-verification.json`, `next-state.json`이 있다. settings hash와 보호 데이터 hash 등 상세 체크포인트는 private directory에 남는다. `apply_server.py`, `verify_server.py`, `postflight_server.py`는 최종 사용한 검증 도구다.

## 남은 범위와 다음 작업

전체 data-health는 기존 `attention_required` 상태다. 이번 자동 갱신 성공을 전체 데이터 품질 완료로 해석하지 않는다. 버전 일치는 재무 입력에 한정하며 뉴스·밸류에이션 전체 최신성이나 리서치 내용의 사실 검증을 증명하지 않는다. 추천 weight·benchmark·schema·실거래·모델 설정·AWS 설정은 변경하지 않았다.

로컬 IP와 기존 허용목록 차이로 SSH 터널/직접 브라우저 접속은 이번에 복구하지 않았다. 운영 작업은 로그인된 EC2 Instance Connect로 수행했고, 화면 동작은 로컬 실제 브라우저, 운영 연결은 인증 API와 서버 렌더 HTML로 구분해 검증했다.

다음 작업은 갱신 대기·실패 원인·한도 사용량·불명 결과 확인 상태를 운영 화면에 묶어 보여 주는 것이다. 남은 기업 원천은 기존6시간 주기 수집이 이어서 처리한다. 보호 기준을 우회하는 자동 재생성이나 한도 증액은 하지 않는다.

최종 대기 현황: current1 / 갱신 대기14 / 원천 수집 대기17, 오늘1/5회 사용, 다음ADBE·ADI·ADSK. 기존 주의 항목8개는 알림 목적지, 실패·누락·stale job을 합산한 artifact 실행 증거, benchmark/보유검토·피드백·추천성과 성숙 관련 항목이다. artifact runner gate는 실행 전체가 불가능하다는 의미가 아니라 개별 작업의 누락/실패/오래된 증거를 포함한다. 다음에는 운영 queue 가시성과 함께 이들 중 실제 자동화를 막는 항목부터 분리해 복구한다. `evidence/next-state.json`에 현재 목록을 남겼다.
