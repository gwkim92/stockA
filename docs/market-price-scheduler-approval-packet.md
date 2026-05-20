# Market Price Scheduler Approval Packet

생성일: 2026-05-20

## 결론

`market-price-daily` 스케줄러는 아직 실제로 설치되지 않았다.

- 최근 단발 실행/드라이런: 통과
- 승인 관문: `blocked_pending_manual_approval`
- 활성화 허용: `false`
- 설치 상태: `not_installed`
- host LaunchAgents 쓰기: `false`
- `launchctl` 실행: `false`
- 다음 차단점: repo 밖 명시 승인 record 필요

이 문서는 실제 활성화를 실행하지 않는다. 실행 전에 아래 명령과 rollback 명령을 사용자가 명시 승인해야 한다.

## 대상 작업

- Job: `market-price-daily`
- Pipeline: `market_price_upsert`
- Domain: `market`
- Cadence: `daily`
- Scheduler type: `launchd`
- Label: `com.stockanalysis.data-operations.market-price-daily`
- Schedule: 미국 동부 시간 기준 화요일-토요일 18:30
- Runtime env file: `/private/tmp/stockanalysis-runtime/data-operations.real.env`
- Rendered plist: `/private/tmp/stockanalysis-runtime/evidence/activation-chain-market-price-daily/operator-dry-run/rendered/com.stockanalysis.data-operations.market-price-daily.plist`

## 실제 실행될 명령

아래 명령은 아직 실행하지 않았다.

```bash
install -m 600 "/private/tmp/stockanalysis-runtime/evidence/activation-chain-market-price-daily/operator-dry-run/rendered/com.stockanalysis.data-operations.market-price-daily.plist" "$HOME/Library/LaunchAgents/com.stockanalysis.data-operations.market-price-daily.plist"
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.stockanalysis.data-operations.market-price-daily.plist"
launchctl kickstart -k "gui/$(id -u)/com.stockanalysis.data-operations.market-price-daily"
launchctl print "gui/$(id -u)/com.stockanalysis.data-operations.market-price-daily"
```

## 실패 시 rollback 명령

아래 rollback 명령도 아직 실행하지 않았다.

```bash
launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.stockanalysis.data-operations.market-price-daily.plist"
rm -f "$HOME/Library/LaunchAgents/com.stockanalysis.data-operations.market-price-daily.plist"
```

## 실제로 반복 실행될 child command

plist가 등록되면 launchd는 아래 wrapper를 통해 market price daily runner를 실행한다.

```bash
/bin/bash -lc 'exec /bin/bash /Users/woody/ai/stockanalysis/scripts/run_data_operations_scheduler_job.sh --env-file /private/tmp/stockanalysis-runtime/data-operations.real.env --job-id market-price-daily --timeout-seconds 600 -- /private/tmp/stockanalysis-runtime/venv/bin/python -m stockanalysis.operations.cli market-price-daily-run --skip-if-fresh'
```

## 승인 record 템플릿

승인을 진행하려면 repo 밖 JSON 파일로 아래 형태의 record가 필요하다. 이 템플릿은 secret 값을 포함하지 않는다.

```json
{
  "approval_record": "data_operations_scheduler_activation_approval",
  "approval_decision": "approved",
  "operator": "woody",
  "approved_at": "2026-05-20T00:00:00Z",
  "job_id": "market-price-daily",
  "operator_dry_run_report": "/private/tmp/stockanalysis-runtime/evidence/activation-chain-market-price-daily/operator-dry-run/evidence/operator-dry-run.json",
  "activation_window": "manual_activation_after_exact_command_review",
  "rollback_owner": "woody",
  "acknowledged_commands": [
    "install -m 600",
    "launchctl bootstrap",
    "launchctl kickstart",
    "launchctl print"
  ],
  "acknowledged_risks": [
    "host_scheduler_state_change",
    "recurring_data_operation_execution",
    "rollback_required_if_first_run_fails"
  ]
}
```

## 사용자가 승인할 때 필요한 문장

실제 host activation을 원하면 다음 내용을 명시해야 한다.

```text
market-price-daily 스케줄러를 위 exact command로 내 Mac의 LaunchAgents에 설치하고 launchctl bootstrap/kickstart/print까지 실행하는 것을 승인한다. 실패 시 위 rollback command를 실행하는 것도 승인한다.
```

## 아직 하면 안 되는 것

- 위 `install` 명령 실행
- 위 `launchctl bootstrap` 실행
- 위 `launchctl kickstart` 실행
- 위 `launchctl bootout` 실행
- `~/Library/LaunchAgents` 직접 쓰기/삭제

## 다음 단계

1. 사용자가 위 approval 문장을 명시 승인한다.
2. repo 밖 approval record를 생성한다.
3. approval gate를 다시 생성해 `activation_allowed=true`로 바뀌는지 확인한다.
4. activation request, user decision, final preflight, host execution confirmation을 순서대로 통과시킨다.
5. 마지막에만 실제 host activation을 실행한다.
