# Session Handoff

## Active Task

- 이름: news-cluster-automation-regression
- 담당: Codex
- 날짜: 2026-05-21

## Current Status

- 진행 중:
  - EC2 실제 DB에서 `news_event_candidate=10`, `news_cluster_summary=0` 상태를 확인했다.
  - 이전 00:38 실행 리포트에는 cluster 3건 생성 기록이 있었지만, 이후 DB reset/recovery로 사라진 것을 확인했다.
  - 최신 자동 프로필이 AI 후보 분석만 실행하고 cluster evidence를 재생성하지 않는 회귀를 원인으로 판단했다.
  - `news-intraday` operating-data profile에 `news-cluster-evidence` 단계를 AI 후보 분석 앞에 복구했다.
  - cadence/local runtime manual command도 단일 AI extract가 아니라 `operating-data-run --profile news-intraday`를 안내하도록 정렬했다.
  - EC2에 배포했고, `news-intraday` profile 수동 실행으로 `news_cluster_summary=4`, `news_event_candidate=19` 상태를 확인했다.
  - authorized `/api/ai/news-clusters?asOfDate=2026-05-21&limit=4`가 cluster 4건과 clustered event 26건을 반환했다.
  - `/intelligence` 터널 smoke에서 저장된 뉴스 증거/뉴스 묶음과 주요 theme marker가 렌더링되는 것을 확인했다.

## Exact Next Step

- exact next step: 다음 정기 timer 실행 후 `news-intraday-operating-data-run.json`이 최신 profile report로 갱신되는지 확인한다.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_operating_data_orchestrator tests.test_data_operations_cadence tests.test_news_rss_cluster_evidence tests.test_news_rss_ai_extract -v`: pass, 28 tests.
- `git diff --check`: pass.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task news-cluster-automation-regression`: pass.
- EC2 deploy: `git pull --ff-only`, editable package refresh, FastAPI/Next restart: pass, both services active, HEAD `afec8d2`.
- EC2 `news-intraday` profile execution: data steps inserted 4 `news_cluster_summary` artifacts and 9 additional `news_event_candidate` artifacts.
- EC2 DB count after run: `news_cluster_summary=4`, `news_event_candidate=19`.
- EC2 API smoke: `/api/ai/news-clusters?asOfDate=2026-05-21&limit=4` returned `cluster_count=4`, `clustered_event_count=26`, providers `local_rules`.
- Tunnel web smoke: `/intelligence` contained `저장된 뉴스 증거`, `뉴스 묶음`, `ENERGY_GEOPOLITICS`, `MACRO_RATES_FED`.

## Risks

- 이번 수정은 자동화 단계 복구이며 추천 산식이나 주문/거래 실행은 바꾸지 않는다.
- 수동 EC2 profile 실행은 DB row를 정상 생성했지만, 마지막 report file overwrite에서 기존 root-owned 파일 권한 때문에 exit code가 실패했다. EC2 scheduler report directory/file ownership은 `ec2-user`로 정리했다. systemd timer는 root 실행이라 자동 실행 자체의 차단점은 아니다.
- The current local-rule news cluster provider remains free and non-LLM; Codex OAuth is still used only for individual news candidate extraction.
