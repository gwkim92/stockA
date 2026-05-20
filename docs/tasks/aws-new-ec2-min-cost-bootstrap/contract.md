# Task Contract

## Task

- 이름: aws-new-ec2-min-cost-bootstrap
- 요청: AWS 콘솔에서 새 EC2를 최소 비용 기준으로 준비하고, 프로젝트 서버 배포 시작 가능 상태를 만든다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 새 EC2 launch 구성이 비용/보안/운영 경계를 포함해 검토 가능하며, 실제 생성은 사용자에게 예상 비용과 구성을 보고한 뒤 명시 승인으로만 진행된다.

## Why

- 사용자는 기존 EC2 재사용이 아니라 새 EC2 생성을 명시했다.
- 프로젝트는 로컬 MVP에서 외부 서버 런타임으로 넘어가야 data ingest, FastAPI backend, Next.js cockpit, worker/scheduler를 상시 구동할 수 있다.
- 사용자는 비용이 없다고 명시했으므로 무료/최저비용 후보와 과금 리스크를 먼저 고정해야 한다.

## Scope

- 포함:
  - AWS 콘솔에서 계정/리전/launch 가능 상태 확인
  - 새 EC2 launch form 준비
  - Free Tier eligible 또는 최저비용 인스턴스 후보 선택
  - 최소 EBS 용량, SSH 접근, 보안 그룹 최소 개방 검토
  - 생성 전 예상 비용/위험 보고
- 제외:
  - 사용자 승인 없는 EC2 생성
  - RDS, ALB, NAT Gateway, Elastic IP 추가 생성
  - 유료 모니터링, Savings Plan, Reserved Instance 구매
  - 도메인, Route53, ACM, WAF, CloudFront 생성
  - production secret 주입 또는 브로커/실거래 연결

## Boundaries

- 새 리소스 생성 버튼은 비용 발생 액션이므로 사용자 승인 전 클릭하지 않는다.
- AWS Console 계정은 `wooody (115623963546)`, 리전은 `us-east-1`로 확인되었다.
- 로컬 AWS CLI profile은 다른 계정(`061051252914`)을 가리키므로 이 작업에서 AWS CLI로 리소스를 변경하지 않는다.
- 프로젝트 초기 배포는 단일 EC2 내부 Postgres + FastAPI + Next.js + worker를 우선 검토한다. RDS는 비용 때문에 제외한다.
- 퍼블릭 IPv4는 EC2가 Free Tier eligible이어도 별도 비용이 발생할 수 있다.

## Preferred Launch Shape

- AMI: Ubuntu 또는 Amazon Linux 계열의 Free Tier eligible Quick Start AMI.
- Instance type: 우선 `t4g.small` 또는 `t3.small` Free Tier eligible 여부를 콘솔에서 확인한다. 표시가 불명확하면 `t3.micro`로 낮춘다.
- Storage: gp3 8-16GiB, delete on termination enabled.
- Network: default VPC, public subnet, auto-assign public IPv4 only if 접속/서비스 노출에 필요.
- Security group: SSH는 현재 접속 IP로 제한, HTTP/HTTPS는 실제 프론트 노출 전까지 열지 않는다.

## Verification

- 생성 전:
  - launch summary 캡처 수준으로 구성 확인
  - 비용 발생 항목 식별
  - 승인 문구 확보
- 생성 후:
  - 인스턴스 상태 running 확인
  - EC2 Instance Connect 또는 SSH 접속 확인
  - OS, disk, memory, python/node/docker/git 존재 여부 확인
  - repository clone과 secret-free bootstrap plan 확인

## Done Criteria

- [x] 새 EC2 launch configuration이 준비되었다.
- [x] 사용자에게 비용 발생 가능성을 보고했다.
- [x] 명시 승인 없이 비용 발생 버튼을 누르지 않았다.
- [x] 생성된 경우 서버 접속과 기본 런타임 상태가 확인되었다.
- [x] 다음 세션이 이어받을 수 있게 handoff가 작성되었다.
