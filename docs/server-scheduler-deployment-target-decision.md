# Server Scheduler Deployment Target Decision

생성일: 2026-05-20

## 결론

현재 조건에서는 외부 scheduler를 바로 배포하지 않는다.

이유는 단순하다. 지금 데이터베이스와 런타임은 로컬 Mac의 Postgres/FastAPI/Next에 있다. GitHub Actions나 외부 managed scheduler는 이 로컬 DB에 안전하게 접근할 수 없다.

## 무료 조건에서의 현실적 후보

- GitHub Actions scheduled workflow: public repo 표준 runner는 무료 후보지만, hosted DB/runtime이 있어야 실제 ingest를 저장할 수 있다.
- 기존 VPS/systemd timer: 이미 가진 서버가 있다면 추가 비용 없이 가장 단순하다. 현재는 서버가 제공되지 않았다.
- Kubernetes CronJob: 이미 cluster가 있을 때만 후보이다. 현재는 비용/운영 복잡도가 과하다.
- Managed scheduler: 무료 tier가 있더라도 worker endpoint/hosted DB가 필요하고, provider lock-in이 생긴다.
- Mac LaunchAgents/cron: 지금 당장 로컬 DB에 닿을 수 있지만, 사용자가 원한 “서버 측” 반복 실행은 아니다.

## 현재 결정

- 배포 상태: not deployed
- 추천 상태: blocked until hosted database/runtime exists
- 다음 작업: `hosted-database-runtime-decision`

## 참고 근거

- GitHub Actions public repo standard runner는 무료 사용 가능: <https://docs.github.com/actions/administering-github-actions/usage-limits-billing-and-administration>
- GitHub Actions schedule은 UTC POSIX cron이고 최소 5분 간격: <https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows>
- GitHub Actions secrets는 repository secrets로 주입 가능하지만 secret 값을 workflow/log에 직접 출력하면 안 됨: <https://docs.github.com/en/actions/how-tos/security-for-github-actions/security-guides/using-secrets-in-github-actions>
