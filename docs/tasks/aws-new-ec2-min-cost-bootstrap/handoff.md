# Session Handoff

## Active Task

- 이름: aws-new-ec2-min-cost-bootstrap
- 담당: Codex
- 날짜: 2026-05-20

## Current Status

- 완료:
  - AWS Console 계정 `wooody (115623963546)`, 리전 `us-east-1` 확인.
  - 기존 EC2 `settleLab` 재사용이 아니라 새 EC2 launch form으로 전환.
  - task contract 작성.
  - 새 EC2 launch form 구성 완료 직전 상태:
    - Name: `stockanalysis-mvp-20260520`
    - AMI: Amazon Linux 2023 kernel-6.1 AMI, Free Tier available 표시
    - Instance type: `t3.small`, Free Tier available 표시, 2 vCPU, 2 GiB
    - Key pair: existing `settle`
    - Public IP auto assign: enabled
    - Security group: new `stockanalysis-mvp-ssh-20260520`
    - SSH inbound: `211.54.17.177/32` only
    - HTTP/HTTPS inbound: not enabled
    - Storage: gp3 16 GiB
- 막힌 점:
  - `인스턴스 시작`은 비용 발생 액션이므로 사용자 명시 승인 전 클릭하지 않음.
  - 로컬 AWS CLI profile은 AWS Console 계정과 다르므로 AWS CLI로는 이 계정 리소스를 변경하지 않음.

## Exact Next Step

- 사용자가 새 EC2 생성을 승인하면 AWS Console의 `인스턴스 시작` 버튼을 누른다.
- 생성 후 인스턴스 ID/public DNS/public IPv4를 확인하고 EC2 Instance Connect 접속을 시도한다.
- 접속되면 OS, disk, memory, git/python/node/docker 상태를 확인한다.

## Cost Notes

- Console displays `t3.small` and AMI as Free Tier available, but Free Tier/credit eligibility depends on account terms and usage.
- Public IPv4 can be billed separately even when EC2 compute is free-tier eligible.
- 16 GiB gp3 is within the common 30 GiB EBS Free Tier storage note, but actual account eligibility must be watched in Billing.

## Risks

- Existing `settle` private key is not present in local `~/.ssh`; EC2 Instance Connect should be used first.
- If EC2 Instance Connect fails, access may require the user's `settle` private key or a new/imported key pair.
- Single EC2 with local Postgres is the lowest-cost MVP path, not HA/production-grade.
