# stockA 운영 배포 및 복구 인계 — 2026-09-08

## 배포 위치와 확인 결과

개인 AWS 계정 `115623963546`, `us-east-1`, EC2 `i-029d51b163fb07b61` (`stockanalysis-mvp-20260520`, t3.small)에 직접 접속했다. IP `3.211.40.142`, SSH `ec2-user`, 키 `/Users/woody/Downloads/settle.pem`, 코드 `/opt/stockanalysis/app`, 환경 설정 `/opt/stockanalysis/runtime`이다. 계정/인스턴스/리전은 IMDS identity document로 검증했다.

기존 `develop@366abe812d20fbe059ad5a5b62c501c0107ee9ae` (7월 11일)에서 CI 검증된 `cfa40c905fd3a538caf6292eafe84bacfc25e289`로 배포했다. Next build ID는 `ACSruGlBuP3B8ZnxoAOea`다. 운영 웹은 127.0.0.1:3000, 별도 웹 서비스는 0.0.0.0:13000, API는 127.0.0.1:8787이다. 웹 두 서비스와 API는 active/HTTP 200이다. DB는 같은 서버의 `stockanalysis-postgres`, PostgreSQL 16, 127.0.0.1:5432다. 외부 13000 직접 연결은 현재 PC에서 timeout이므로 SSH 터널을 사용했다. AWS 보안그룹은 변경하지 않았다.

## 백업과 롤백

서버 전용 보호 디렉터리 `/opt/stockanalysis/runtime/deploy-20260908-cfa40c90`에 다음을 보존했다. 시크릿이 포함될 수 있으므로 전체 폴더를 Git/공유 artifact에 복사하지 않는다.

- `database.dump`: 609 MB DB의 custom-format 논리 백업. TOC 793줄, SHA-256 및 전체 `pg_restore --file=/dev/null` decode 통과. 다른 DB로 실제 restore를 수행한 것은 아니다.
- `database-globals.sql`, `previous-code.tar.gz`, `previous-web-runtime.tar.gz`, `previous-venv.tar.gz`, `pip-freeze.txt`, 당시 env 파일.
- 실제 교체 전 `.next`와 `node_modules`는 `previous-live-next`, `previous-live-node_modules`에도 남겼다.
- `previous-commit.txt`, `active-timers.json`, `activation.json`, 각 단계 로그.

앱 롤백은 스케줄러 작업이 실행 중이지 않은지 확인하고 기존 active timer를 일시 중지한 뒤 웹/API를 중지하여 수행한다. 확인된 이전 커밋과 보관된 `.next`/`node_modules`를 함께 복원하고 기존 venv의 editable package를 재설치한 후 서비스를 시작한다. 마지막에 원래 timer 상태를 복원한다. 기존 `dogfood-output/`는 건드리지 않는다. 마이그레이션 0035는 additive이므로 앱 롤백만을 위해 신규 평가 기록을 삭제하지 않는다. DB 전체 복원은 이후 기록을 덮어쓰므로 별도 범위 판단이 필요하다.

## 수행한 DB/실데이터 검증

- 존재하지 않았던 migration 0035를 lock timeout과 transaction으로 적용했다. eval_run 컬럼 4개와 snapshot 테이블/인덱스를 확인했다.
- 기존 평가는 `legacy_unavailable`로 표시된다. 과거 추천 이력을 소급 생성하지 않았다.
- 기존 스케줄러와 같은 30일 horizon의 deterministic evaluator를 한 번 실행했다: pipeline `23131`, eval `1720`, snapshot `1335`개. 추천/weight/portfolio/order 변경이나 모델 호출이 아니다.
- 저장 payload 전체 1335개의 canonical SHA-256이 일치했다. 실제 비교 API 두 페이지 50개에서 해시·복사 metadata 검증 통과, 페이지 간 중복 없음, 첫 페이지 비교 25개 `unchanged`.
- 9개 실제 웹 경로 HTTP 200. 목록/과거 상세/새 상세를 실제 브라우저로 확인했다. 모바일 390px에서 가로 overflow 없음.
- 서버 backend 72개, production build/typecheck 통과. 기존 OAuth status 테스트 한 개가 서버의 실제 Codex 설치에 영향을 받아 처음 실패했고 테스트 프로세스에만 `STOCKANALYSIS_CODEX_CLI_COMMAND=/usr/bin/false`를 설정하여 외부 CLI를 격리한 뒤 72개 통과했다. 운영 설정 변경이 아니다.
- 전체 DB 행을 API DTO 전용 metadata 검증 함수에 직접 넣은 초기 검증은 bigint/Decimal 표현 차이 때문에 실패했다. 최종 검증은 실제 API JSON DTO를 통한 metadata 검증과 전체 저장 payload canonical hash 검증을 분리했다.
- 임시 2GiB swap은 빌드 후 해제·삭제했다. 기존 timer 13개를 복원했다.

## 가격 수집 문제와 후속 코드

원래 일일 수집 설정은 6개 종목만 포함했다. active 추천은 32종목이고 그중 26개가 오래된 가격이었다. 기존 daily budget 24, per-run cap 6, throttle 8초를 유지하여 AMD 1회 canary와 6/6/6/5개 batch를 실행했다. 총 24개 요청 모두 성공했고 각각 실제 가격 100개를 보완했다. 원래 한도는 소진됐으며 남은 2개는 다음 예산일에 처리해야 한다. 한도나 ledger 날짜를 바꾸어 우회하지 않았다.

이 PR은 기존 `market-price-daily-run`에 `STOCKANALYSIS_MARKET_PRICE_INCLUDE_ACTIVE_RECOMMENDATIONS=true` opt-in을 추가한다. 설정 CSV와 현재 active 추천 종목을 합쳐 가장 오래된 가격부터 처리한다. 원래 CSV를 유지하고 별도 생성 CSV를 사용한다. DB 조회 실패를 6종목 fallback으로 숨기지 않는다. 최종 요청/예산 집행은 기존 runner를 그대로 사용한다. 실제 DB preview는 설정 6개 + active 추천을 합쳐 중복 제거 33개였고 ADBE/ADI가 우선순위 첫 두 종목이었다. 이 후속 코드의 최종 배포/활성화 상태는 PR 및 로컬 `artifacts/runtime-deploy-20260908/final.json`에 기록한다.

## 외부 인증 문제

- 뉴스 AI의 agents_sdk_openai: quota exhausted.
- 기업/사이클 codex_oauth: invalid_refresh_token / 401, 사용자 재로그인 필요.
- 사용자에게 서버 device login 절차를 안내했다. 실제 로그인 성공/모델 호출 성공을 확인하기 전 AI 회복을 주장하지 않는다. 결제/구독/키 교체는 수행하지 않았다.
- systemd service exit 0은 AI 성공을 뜻하지 않았다. 실패 시 `succeeded_with_fallback`으로 끝나는 실제 pipeline/AI invocation 기록을 확인했다. 투자 검토/성과 관찰 gate도 운영 장애와 별개로 남길 수 있다.

현재 세션의 최종 API/브라우저/가격/인증 상태는 `artifacts/runtime-deploy-20260908/`의 보고서와 PR에 이어서 기록한다.
