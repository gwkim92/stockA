# 검증 기록

첫 표는 2026-09-11 로컬 검증이며, 실제 배포 결과는 아래 운영 검증 기록에 구분했다.

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

## 운영 검증 완료

PR #65 CI9개와 merge commit47afdd7e의 6개 workflow 모두 통과. 실제 EC2 배포 후 A의 primary report가 생성됐으며 같은 종목 재실행은 no-op였다. claim23927/child23928/artifact495/invocation41307, 실제 모델 gpt-5.6-terra, source23866 일치. 일일0→1/5, 추가 예약·호출 없음, 보호 데이터와 설정 동일, timers14개 복원, batch13/13개 보호를 확인했다. 자세한 수치와 한계는 `evidence/live-verification.json` 및 handoff를 따른다.

운영 API와 양쪽 웹 HTML의 버전 일치 문구를 확인했다. 직접 운영 브라우저 접속은 로컬 IP 허용목록 차이로 검증하지 못했으며, desktop/mobile 실제 브라우저 검사는 로컬 빌드와 합성 API에서 수행했다. 전체 data-health의 기존 attention_required는 남아 있다.

배포 사전 검사에서 발생한 상태 수집 겹침은 실제 journal로 확인했다. 코드/웹 변경 전 중단을 검증하고 checkpoint를 보존했다. 최대30초 대기 보완 뒤 활성화가 완료됐고, 세 검증 도구는 Python compile 확인 및 실제 실행을 거쳤다.
