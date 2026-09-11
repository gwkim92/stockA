# 인계

진행 중. Branch fiture/research-operations-visibility. 접속 복구 완료: 14.32.108.104/32 → 개인 EC2 SSH, http://127.0.0.1:13309. im.stocka.web-tunnel LaunchAgent 설치, 강제 종료 후 자동 복구 검증. 새 운영 화면은 로컬/DB/브라우저 검사 완료 중이며 아직 미배포.

기존 decision-daily는 9/10 equity 리포트5개가 context/input_budget_exceeded로 실패한 뒤 중단됐다. 이후 배포본1abc9a2a에는 리서치1개 처리 및 마지막 순서가 이미 반영돼 있다. 기존 systemd service를1회 시작했고 결과 대기 중. 체크포인트와 이전 보고서는 /opt/stockanalysis/runtime/research-operations-visibility-20260912에 보존했다.

남은 순서: 새 UI 캡처 확인 → PR/CI → 현재 develop과 일치하는 Linux artifact만 배포(EC2 빌드 금지) → 실제 queue/화면/타이머/설정/자원 제한 확인 → 복구 배치 결과 및 남은 gate 분류 기록.
