# 운영·평가 근거 복구 — 2026-09-10

## 현재 작업 상태

사용자의 프로젝트 분석 후속 실행 요청으로 진행했다. 기존 `runtime-deploy-20260908/handoff.md`의 로컬 수정은 보존했다. 작업 브랜치는 `fiture/runtime-evidence-recovery-20260910`이다.

코드 수정·회귀 검증·develop 푸시·EC2 배포·배포 후 읽기 검증을 완료했다. 실제 AI 성공과 전체 일일 판단 실행은 사용자 인증 및 API 할당량 문제 때문에 미완료다.

## 현재 상태와 원인

- IMDS로 개인 계정 `115623963546`, us-east-1, 인스턴스 `i-029d51b163fb07b61`을 재검증했다. 배포 기준은 `develop@c9d52190`이었다.
- FastAPI 및 웹 두 서비스는 active, API readiness는 live/DB pool 정상, 평가 이력 경로는 HTTP 200이었다. 기존 timer 13개가 설치되어 있다.
- 추천 가격은 32/32개 최신, 누락·stale 0개, 공통 최신 가격일은 2026-09-09였다. 불필요한 가격 재수집은 하지 않았다.
- `decision-daily`는 9월 9일 `cycle-community-ai-summary-v2` 단계의 `input_budget_exceeded`로 중단됐다. AI 호출 이전 fixture preview도 동일한 프롬프트 생성기를 사용하므로 pipeline row를 남기기 전에 종료되었다. 실제 17개 사이클 중 6개가 12,000자 제한에 실패했다.
- 최근 48시간 뉴스 AI 호출 720개는 모두 실패했다. 구조화에는 입력 크기 초과, 번역에는 OpenAI API 할당량 소진이 기록되어 있다.
- Codex 로그인 상태만 보면 logged_in이고 7월 성공 기록 때문에 healthy였지만, 9월 10일 직접 진단은 `failed_auth_invalid`였다. 기존 공식 device-auth 경로를 시작해 사용자의 재로그인을 요청했다. 토큰이나 키를 로컬에서 서버로 복사하지 않았다.
- 알림 테스트는 7월 1일 이후 오래된 상태다. 이번 요청에서 외부 메시지 전송을 명시적으로 지시받지는 않아 ntfy 메시지를 보내지 않았다.

## 코드 변경

- 공통 입력 선택기를 추가했다. 원문·필수 metadata·사이클 conflict 정보는 온전히 유지하며, 지정된 참고자료 목록만 레코드 단위로 선택한다. 선택은 결정적이고 원본 객체를 변경하지 않는다.
- 제외된 레코드 수는 framed JSON 안에 `input_selection`으로 명시한다. 잘못된 JSON이나 필수 metadata 자체의 초과는 계속 거부한다. 원문/JSON 문자열을 잘라 한도를 우회하지 않는다.
- 사이클의 고정된 두 단계 목록 축소를 실제 직렬화 길이를 확인하는 선택으로 교체했다. 프롬프트와 grounding, context hash가 같은 선택을 사용하며 템플릿 버전을 올렸다.
- 뉴스는 동일 RSS 원문과 검색 문맥을 생성 chunk 문자열에 중복하여 전송하지 않는다. 원문 제목·요약과 chunk 식별자는 유지하고 검색 레코드를 선택한다. 요청 해시에 전체 원천 metadata와 문맥을 포함해 잘린 기존 chunk 밖의 변경도 식별한다.
- 기존 Analysis Prompt Quality 검증 스크립트에 새 회귀 테스트를 연결했다. 추천 점수/가중치, benchmark, schema, 주문 권한은 변경하지 않았다.

## 검증

- 로컬 프롬프트/해석 회귀: 272개, 실패 0, SDK 의존 1개 skipped, 외부 IO 시도 0.
- 실제 EC2 Python 3.12 및 설치 SDK로 후보 디렉터리 회귀: 272개 모두 통과, skipped 0, 외부 IO 시도 0. 최초 후보 패키지의 SQL fixture 누락 3개를 보완한 뒤 통과했다. SQL 파일을 DB에 적용한 것은 아니다.
- 운영 CLI·오케스트레이터·추천 평가 회귀: 127개 통과.
- 실제 DB 입력을 후보 코드로 구성: 사이클 17/17개 통과, 최대 11,969/12,000자. 같은 문맥을 다시 선택해도 내용·해시 입력이 일치했다.
- 뉴스 10/10개 입력 구성 통과, 최대 8,675/11,000자. 원문 제목과 요약은 모두 그대로였다. 이 검증의 모델 호출과 DB 쓰기는 0회다.
- 실제 보존 평가 snapshot 1,335개 모두 canonical SHA-256 일치.
- 실제 DB 신원: required relations 모두 존재, fingerprint `1c13a195c31b9ad1c97b3f2e6d6baae9a45c31257ff6c5cfb4d50f5b555fe5f7`.
- 원천 연결 dry-run: readiness 28 → quality 26/outcome 27을 정확히 읽었다. `lineage_incomplete_fail_closed`: outcome에 market/strategy/horizon/universe cohort 필드가 없다. 최신 평가를 과거 참조에 대신 끼워 넣지 않았다. 유효한 lineage eval이 없어 prospective observation을 실행하지 않았으며 감사 과정의 DB 쓰기는 0회다.

## 증거와 남은 범위

로컬 증거 디렉터리: `artifacts/runtime-evidence-recovery-20260910/`. 핵심 파일은 `initial-runtime.json`, `diagnosis-safe.json`, `decision-artifacts.json`, `codex-direct-smoke.json`, `payload-sizes-and-evals.json`, `evidence-readonly.json`, `candidate-live-input-check.json`, `prompt-contract-report.json`, `server-candidate-tests.log`, `operations-regression.log`이다.

자동 승인 검토가 원격 DB 오류·전체 journal을 로컬로 복사하는 진단을 거부했다. 이후에는 원문을 서버에 두고 오류 분류·코드 위치·상태·개수만 추출하는 작업으로 좁혀 승인받았다.

사용자 인증 전 실제 AI 회복이나 전체 일일 판단 성공을 주장하지 않는다. API 할당량/결제/키는 변경하지 않는다. 가중치 pilot은 시작하지 않으며, 평가 원천의 cohort 식별과 별도 정책 결정을 후속으로 남긴다. 대형 live adapter 분해는 현재 장애 복구와 분리한다.

## 배포와 최종 확인

- 코드 커밋 `25d1ace3da5d3c6302b327b8363e0c99bf77c737`을 develop에 fast-forward 반영하고 GitHub에 푸시했다.
- [Analysis Prompt Quality CI](https://github.com/gwkim92/stockA/actions/runs/34445485819)는 Python 3.11/3.13 offline contract와 PostgreSQL cutoff/atomic 4개 job 모두 통과했다.
- EC2 tracked 변경 없음과 실행 중인 data operations service 없음, 여유 디스크 6.8GB를 확인했다. 기존 untracked `dogfood-output/`은 보존했다.
- 서버 내부 `/opt/stockanalysis/runtime/recovery-20260910-25d1ace3/`에 이전 커밋과 코드 tar, timer 상태를 백업했다. 코드 tar SHA-256은 `1b5b1c0427e39a31b15d7586f975dd92fa963557240799941f151106a8cf6772`이다.
- EC2는 `git pull --ff-only origin develop`로 해당 커밋을 받았고 API 서비스만 재시작했다. DB migration, 웹 코드/build, scheduler 설정은 변경하지 않았다.
- 2026-09-10 06:36 UTC 배포 후 확인: API readiness `ok`, live DB pool `ok`, API/웹 두 서비스 모두 active, 가격 32/32개 fresh. `deployed-readback.json`에 기록했다.
- 배포된 실제 코드의 `cycle-community-ai-summary-v2` dry-run은 `status=planned`, `execute=false`, `node_count=17`이다. 모델 호출·업무 DB 쓰기는 0회다. `decision-daily`의 과거 실패 상태를 성공으로 덮거나 실패 flag만 초기화하지 않았다.
- Mac SSH 터널을 `127.0.0.1:13309 → EC2 127.0.0.1:3000`으로 복구했다. 브라우저에서 `/performance/evaluations`의 평가 1720/기록 1,335개와 `/performance/evaluations/1720`의 저장 내용 일치, 평가 당시 근거, 후속 성과 미측정 표시를 확인했다. 터널은 현재 Mac 세션용이며 재부팅 후 지속성을 설정한 것은 아니다.
- 06:36 UTC 인증은 `device_code_expired`, `login_probe_status=not_logged_in`이었다. 사용자 인증이 끝나야 direct smoke와 제한된 실제 AI 실행을 진행할 수 있다. 일회용 인증 코드는 이 문서에 보관하지 않는다.

## 다음 실행 순서

1. 사용자가 공식 device-auth 로그인을 마치면 서버 login 상태를 확인하고 기존 direct smoke를 한 번 수행한다. 만료 코드를 재사용하거나 토큰을 다른 기기에서 복사하지 않는다.
2. 인증 성공 후 기존 Codex 경로의 제한된 사이클/뉴스 실행을 검증한다. 뉴스 scheduler의 실제 provider는 `agents_sdk_openai`이므로 Codex 로그인만으로 API quota 문제가 해결됐다고 판단하지 않는다. 과금/키/provider 설정 변경은 별도 범위를 확인한다.
3. 허용된 AI provider가 준비된 뒤 일일 profile을 기존 제한으로 실행하고, 마지막 성공 단계·pipeline 결과·저장된 AI 결과를 확인한다.
4. 평가 연결은 readiness 28이 참조한 quality 26/outcome 27의 cohort 누락을 해결할 별도 작업으로 다룬다. 유효한 연결 근거가 생기기 전 prospective observation과 가중치 pilot을 시작하지 않는다.
