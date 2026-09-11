# 반복 서버 무응답 분석

최종 상태: 2026-09-11 09:10 UTC. 사용자 로그인과 증설 승인 후 t3.large 8GiB로 변경하여 SSH/API/웹을 복구했고, CI 결과물 배포와 실제 수집 두 번의 검증을 마쳤다. 현재·직전 부팅의 커널 OOM 기록은 없으므로 세부 자원 고갈 원인은 확정하지 않는다. 아래 표와 초기 판단은 장애 중 확보한 근거이며 최신 실행 결과는 handoff.md와 evidence/를 따른다.

## 확인한 사실

| 시점 | 기록 | 의미 |
|---|---|---|
| 이전 Toss 수집 | 확장된 US 종목을 한 번에 수집하고 큰 candle payload를 각 행에 반복 저장. 이후 10종목/30개 candle 제한 및 compact evidence로 교정 | 대량 작업에 입력 크기·실행량 제한이 없던 별개의 자원 위험 |
| 9월 8일 배포 | 같은 t3.small에서 임시 2GiB swap을 사용해 빌드한 뒤 해제 | 빌드 시 자원 여유를 별도로 확보한 기록 |
| 9월 10일 모델 설정 배포 | 서버 Next 빌드 도중 웹/SSH 무응답. 재부팅 후 복구. 커널 OOM 기록은 발견하지 못함 | 동일 촉발 상황이 이미 있었고, 이후 외부 Linux artifact 사용을 명시함 |
| 9월 11일 자동화 배포 준비 | 별도 runtime 디렉터리에서 자원 제한 없이 Next 빌드를 다시 시작. 웹/SSH 무응답. 활성화 단계 전 | 새 자동화 코드 실행 전 발생. 빌드만 다른 디렉터리에 두어도 서버 자원을 공유함 |

기존 운영 기록상 웹 두 프로세스, API, PostgreSQL 컨테이너와 예약 작업이 한 호스트에 있다. 해당 t3.small은 2 vCPU/2GiB 메모리 사양이다([AWS 공식 사양](https://aws.amazon.com/ec2/instance-types/t3/)). 이번 부팅의 실제 총 메모리와 가용량은 복구 후 확인한다.

## 판단

- 최근 두 차례의 공통 촉발점은 운영 호스트에서 시작한 웹 빌드다. 9월 10일 외부 빌드 지시를 9월 11일에 지키지 못한 운영 준비 누락이 반복됐다.
- 메모리 압박이 가장 먼저 확인할 가설이다. CPU/EBS 지연이나 동시 예약 작업의 영향은 현재 데이터로 배제할 수 없다. OOM 로그나 실제 관측값 없이 ‘OOM 확정’ 또는 ‘서버 사양만이 원인’으로 보고하지 않는다.
- 현재 웹 접근은 SSH 터널에 의존한다. 외부 13000 포트 직접 연결은 9월 8일 정상 배포 시에도 timeout이었다. 따라서 외부 HTTP timeout을 이번 장애의 독립 증거로 쓰지 않는다. 현재 확인된 직접 증거는 SSH 연결의 banner timeout과 터널을 통한 서비스 접근 불가이며, API/web 프로세스가 실제로 종료됐는지는 복구 후 확인해야 한다.
- profile generator에 CPU/메모리/전체 작업 시간 제한이 없는 것은 코드에서 확인했다. 실제 설치 unit의 drop-in과 컨테이너 제한은 아직 읽지 못했다. 작업별 제한만으로 Docker DB의 사용량까지 제한되는 것도 아니다.
- 외부 artifact workflow가 수동 실행 또는 workflow 자체 변경에만 반응하던 설정은 사람이 서버 빌드로 되돌아갈 여지를 남겼다.

## 이번 변경과 남은 확인

- PR #63: 표준 npm build 본체에서 운영 경로/EC2를 차단하고, 기존 CI를 웹 변경마다 자동 실행한다. 이는 직접 Next CLI를 우회 호출하는 것까지 OS 차원에서 막는 기능은 아니다.
- CI run 34579004209가 Linux 결과물 생성을 성공했다. 내려받은 archive SHA256, 소스 tree, package lock, build ID, platform과 cache 제외를 확인했다. 전체 브라우저 회귀검사 run 34579004245도 성공해 PR #63을 develop `502eb679`로 병합했다. 운영 develop 502eb679에 해당 결과물 배포를 완료했다.
- 운영에서는 빌드하지 않고 검증된 결과물만 교체한다. host 진단 script와 기존 자동화 2회 검증 script는 준비됐다.
- 로그인 후 대상 인스턴스 상태/시스템 로그를 확인하고 필요한 복구를 수행한다. 그 다음 실제 사용량에 맞춘 batch 동시 실행 제한·CPU/메모리 예산·무진행 감지를 결정한다. 현재 운영 설정을 추측으로 변경하지 않았다.

근거 파일: `docs/tasks/ai-model-settings-v1/handoff.md`, `docs/tasks/runtime-deploy-20260908/handoff.md`, `docs/tasks/tossinvest-shadow-daily-resource-guard-v1/handoff.md`, `docs/tasks/research-automation-20260911/handoff.md`.

## 복구 후 확인

- 8GiB 메모리와 메모리 PSI 0, 실제 수집 후 가용 6,774MiB를 확인했다.
- profile unit의 자원/전체 시간 한도 infinity를 실제로 확인했다. 서버 빌드 차단은 적용했지만 전체 배치/DB cgroup 격리는 후속 범위다.
- AWS 3종 상태 검사는 장애 중에도 통과했다. EC2 실행/상태 검사만으로 웹·SSH 응답을 보장할 수 없으므로 서비스 readiness와 작업 receipt를 따로 검증했다.
