# 검증 기록

2026-09-11 로컬 구현 검증. 아직 운영 배포 결과가 아니다.

| 검증 | 결과 |
|---|---|
| `STOCKA_TEST_POSTGRES_BIN=/opt/homebrew/opt/postgresql@17/bin bash scripts/verify_financial_period_integrity.sh` | 165개 통과. 임시 Postgres, 실제 transaction/COMMIT/receipt 대조 |
| AI·CLI·frontend adapter 회귀 묶음 | 262개 통과 |
| 운영 orchestrator 및 profile scheduler verification scripts | 통과 |
| `npm run build`, `npm run typecheck` | 통과. 로컬 검증용 산출물 |
| ResearchProvenance Vitest | 5개 통과 |
| Playwright company config, `--grep 'financial source'` | desktop/mobile 4개 통과 |

실제 DB 검사는 8개 경쟁 실행에서 예약 5개만 생성됨, 동일 SHA 재수집·이미 생성된 수동 결과의 중복 방지, 저장 이후 응답 소실 복구, 불명 결과의 재호출 차단, 24시간 확인된 실패 재시도, 생성 중 원천 변경, 과거 일자 한도 우회 차단을 포함한다. 이 검사의 모델 제공자는 fake이며 실제 모델 성공 근거로 쓰지 않는다.

화면은 최종 빌드를 브라우저에서 확인했다. 원천이 바뀐 보고서의 안내가 자동으로 열리고 요약에도 이전 자료 사용을 표시한다. 버전 일치와 과거 버전 미기록 상태를 구분한다. `evidence/financial-source-desktop.png`, `evidence/financial-source-mobile.png`는 합성 데이터 화면이다.

운영 검증은 `apply_server.py`로 Linux CI artifact를 적용한 뒤 `verify_server.py`의 제한된 canary로 진행한다. 생성 한도가 이미 찼으면 그대로 유지하고 실제 모델 성공은 미검증으로 기록한다. 운영 체크포인트가 있으면 canary를 그대로 반복하지 않는다.
