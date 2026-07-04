# ec2-access-stability-v1 Contract

## Purpose

EC2 운영 후보의 접속, 서비스, read-only API, data-health, 로컬 터널 상태를 매번 수동 판단하지 않도록 표준 검증 절차를 고정한다.

## Scope

- 대상 계정은 개인 AWS 계정 `115623963546`이다.
- 대상 EC2는 `stockanalysis-mvp-20260520`, public IP `3.211.40.142`, app path `/opt/stockanalysis/app`이다.
- 로컬 AWS CLI write 작업은 사용하지 않는다.
- 실거래 주문, 추천 weight, DB schema, benchmark, portfolio position은 변경하지 않는다.

## Deliverables

- `scripts/verify_ec2_access_stability.sh`
  - SSH 접속 가능 여부
  - EC2 git branch/commit
  - `stockanalysis-web.service`
  - `stockanalysis-frontend-api.service`
  - FastAPI `/__ready`
  - authenticated `/api/data-health`
  - optional local `127.0.0.1:13000` tunnel check
- `docs/tasks/ec2-access-stability-v1/handoff.md`

## Acceptance Criteria

- script exits `0` when EC2 SSH, services, FastAPI readiness, and authenticated data-health are available.
- script reports open gates instead of hiding them.
- script confirms `order_boundary=read_only_no_order`.
- optional local tunnel check is controlled by `STOCKANALYSIS_REQUIRE_LOCAL_TUNNEL=1`.

## Verification

```bash
bash scripts/verify_ec2_access_stability.sh
STOCKANALYSIS_REQUIRE_LOCAL_TUNNEL=1 bash scripts/verify_ec2_access_stability.sh
```
