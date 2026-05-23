# Task Contract

## Task

- 이름: news-intraday-daily-cadence
- 요청: EC2 뉴스 자동화가 주말에 멈추지 않도록 `news-intraday` profile scheduler cadence를 매일 짧은 주기로 조정한다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `news-intraday` systemd timer가 월-금 장중 전용이 아니라 매일 2시간 간격으로 실행되도록 코드 default, 검증, EC2 설치 상태가 일치한다.

## Why

- 뉴스와 정책/기술 흐름은 주말에도 발생한다.
- 현재 EC2 timer는 `Mon..Fri *-*-* 09..18:00/30 America/New_York`라서 토요일과 일요일에는 새 RSS 수집, 번역, 뉴스 묶음, AI 후보 분석이 자동으로 돌지 않는다.
- 현재 `news-intraday`는 RSS 수집뿐 아니라 번역/AI 후보 분석도 포함하므로 30분보다 2시간 간격이 실행 겹침과 OAuth 호출량을 줄이는 현실적 타협이다.

## Scope

- 포함:
  - `news-intraday` default cron schedule 변경
  - scheduler unit tests와 verification script 기대값 갱신
  - task handoff/review 작성
  - EC2 manifest 재생성, systemd timer 재설치, daemon reload, timer active/next run 확인
- 제외:
  - 뉴스 수집과 AI 분석 profile 분리
  - DB schema 변경
  - 추천 점수/거래 로직 변경
  - 유료 provider 도입

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/operating_data_profile_scheduler.py`
  - `tests/test_operating_data_profile_scheduler.py`
  - `scripts/verify_operating_data_profile_scheduler_invocation.sh`
  - `docs/tasks/news-intraday-daily-cadence/*`
- 수정 금지 파일:
  - `.env`/secret 값
  - DB migrations
  - scoring formula
  - broker/order code

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_operating_data_profile_scheduler tests.test_data_operations_cli.DataOperationsCliTests.test_operating_data_profile_scheduler_invocation_plan_command_writes_output_and_markdown tests.test_data_operations_cli.DataOperationsCliTests.test_operating_data_profile_scheduler_invocation_plan_rejects_repo_inside_output tests.test_data_operations_cli.DataOperationsCliTests.test_operating_data_profile_scheduler_invocation_plan_rejects_repo_inside_manifest_output_root`
  - `bash scripts/verify_operating_data_profile_scheduler_invocation.sh`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
  - `git diff --check`
  - EC2 `systemd-analyze verify` for generated profile manifests
  - EC2 `systemctl list-timers --all stockanalysis-operating-data-news-intraday.timer --no-pager`

## Done Criteria

- [x] 코드 default schedule이 매일 2시간 간격이다.
- [x] systemd manifest가 `OnCalendar=*-*-* 00,02,04,06,08,10,12,14,16,18,20,22:00 America/New_York`를 렌더한다.
- [x] EC2 installed timer의 next run이 주말에도 잡힌다.
- [x] AWH task verify를 통과한다.
