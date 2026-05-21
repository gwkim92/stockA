# Session Handoff

## Active Task

- 이름: operating-data-profile-scheduler
- 담당: Codex
- 날짜: 2026-05-20

## Current Status

- 완료:
  - `stockanalysis-operations operating-data-run`에 `--profile` option을 추가했다.
  - `full-recovery`는 전체 복구/배포 smoke용으로 유지했다.
  - 자동 운영 후보 profile을 분리했다.
  - `news-intraday`: RSS 수집, RSS 이벤트 enrichment, 뉴스 클러스터 AI evidence.
  - `market-daily`: 무료 provider budget을 지키는 market candle watchlist refresh.
  - `decision-daily`: missing symbol backfill, cycle/recommendation/thesis, portfolio snapshot, remediation, paper validation.
  - `macro-weekly`: macro series refresh.
  - `performance-monthly`: due performance outcome schedule.
  - 뉴스/AI 관련 cadence를 intraday로 노출하고 `news_rss_event_enrichment` expected job을 cadence registry에 추가했다.
  - `news-intraday`는 portfolio positions CSV 없이 preview할 수 있게 dependency를 분리했다.

## Exact Next Step

- 다음 세션은 이것부터 시작: EC2 systemd timer 배포 전에 profile별 timer plan을 만든다. 같은 backend command를 사용하되 `news-intraday`, `market-daily`, `decision-daily`, `macro-weekly`, `performance-monthly`를 별도 service/timer로 나누고, `full-recovery`는 manual-only로 남긴다.
- 현재 진행 상황: `operating-data-profile-scheduler`는 profile별 `operating-data-run --profile` 호출 패킷을 렌더하는 CLI 하위 명령으로 연결되었습니다.
  `operating-data-profile-scheduler-invocation-plan`은 target/platform 선택, profile 선택/자동 full-recovery 포함, 일정 오버라이드, repo-outside 경로 검증, markdown 출력, manifest 파일 생성까지 한 번에 수행합니다.
- `systemd` 타겟은 cron 규칙의 변환 가능성을 사전 검사합니다. `*/30` 형태 분 단위 스텝이나 시간대 범위 같은 미지원 패턴은 즉시 실패하여 잘못된 timer manifest 생성이 막혀 있습니다.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_operating_data_orchestrator tests.test_data_operations_cli tests.test_data_operations_cadence -v`
- `PYTHONPATH=src python3 -m unittest tests.test_operating_data_profile_scheduler -v`
- `bash scripts/verify_operating_data_profile_scheduler_invocation.sh`

## Risks

- 아직 EC2 systemd timer는 설치하지 않았다.
- `event-intelligence-weekly` job id는 기존 호환을 위해 유지하지만 cadence와 command template은 intraday local cluster evidence 방향으로 정렬했다.
- 실거래 broker submission과 kill switch unlock은 여전히 범위 밖이다.
- CLI 명령은 invocation packet만 생성하고 실행을 직접 수행하지 않기 때문에 실제 스케줄러 배포/호스트 mutation은 별도 승인 절차로 남습니다.
- 미지원 systemd cron 패턴(예: `*/30 9-18 * * 1-5`)은 즉시 `ValueError`로 거부되어 변환 오류를 런타임에서 감출 수 없습니다.
