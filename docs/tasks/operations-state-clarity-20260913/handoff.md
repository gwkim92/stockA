# 운영 상태 표시 정합성 — 2026-09-13

## 변경

- Toss 계정과 미국 장중 수집의 마지막 월~금 예정 시각을 America/New_York로 계산한다. 해당 시각 이후 시작·완료한 성공 기록이 있고 다음 실행 전이라면 8시간 경과 후에도 `scheduled_wait`로 표시한다. 실패·누락·fallback·정체와 금요일 마지막 실행 누락은 경고를 유지한다. 휴장일 달력이나 스케줄 설정은 바꾸지 않는다.
- `tossinvest_market_data_sync` 공유 pipeline 요약은 US/microdata 실행을 명시적으로 선택한다. 기존 DISTINCT ON의 같은 run_id 정렬 동률 때문에 US 일봉/장중 등 임의 job 설명이 선택되던 문제를 제거했다. 이 요약은 전체 Toss 모드별 건강함을 보장하지 않는다. pipeline 요약 43개 범위는 유지한다.
- `needs_more_data` 저장값과 원래 설명을 보존하면서 화면 전용 label/reason을 추가한다. 유한 수익률(0 포함)이 있으면 판단 보류, 수치가 없으면 수치 근거 부족, paper symbol blocker가 있으면 가상 매매 검증 차단을 표시한다.
- 누적평가의 550/454는 같은 결정의 여러 날짜 관찰을 포함한다. 독립 판단 개수로 표현하지 않는다. 원래 평가, 기간, 기준, 비중, 주문 경계는 그대로다.

## 검증

- 어댑터·표시 단위 검사 113개 통과.
- 실제 disposable PostgreSQL 포함 최종 208개 통과. 월요일 예정 시각, DST, 실패/누락/장기 실행, 모드 분리, 2,500개 실행 이력에서 계산 횟수 상한을 확인했다.
- 새 상태의 frontend 검사 2개와 타입 검사 통과.
- 로컬 디스크 부족으로 최초 PostgreSQL/typecheck가 실패했다. 종료 확인된 disposable DB 및 `/private/tmp/stocka-research-linux-build/apps/web`의 재생성 가능한 build/dependency 산출물만 정리했다. 운영 데이터와 사용자의 변경은 보존했다.
- PR71 CI 5개 모두 통과(research-home 12분 4초). PR72 백엔드 보정은 financial-period/batch-runtime/history 통과 후 지연 복구를 위해 먼저 반영했다. PR72 전체 UI 회귀도 9분49초에 통과했다(최종 CI4개 모두 성공).

- PR: [기능71](https://github.com/gwkim92/stockA/pull/71), [쿼리 비용 보정72](https://github.com/gwkim92/stockA/pull/72).

## 운영 결과

- 개인 계정 115623963546 / i-029d51b163fb07b61 확인 후 develop 배포. 기능 PR71 merge `c5392f84`, 쿼리 비용 보정 PR72 merge `402d8bfa`.
- 웹은 검증한 Linux artifact BUILD_ID `3KugfnYpOj1xutd_eBHqc`, web tree `dc3b7508346e3d135f8ac456ccb99a0c88ea7854`를 사용했다. 후속 백엔드 보정에서 그대로 유지했다.
- 설정 4개 hash 보존, 활성 timer 14개 복구, API/웹 3개 서비스 정상. 최신 status snapshot도 운영 profile 13개 보호/활성, 주의 0개를 확인했다(KR 2개 의도적 비활성).
- 계정 run24013, US microdata run23999 모두 `scheduled_wait`. 총 pipeline 43개. artifact runner 실패/누락 0개, attention false.
- feedback eval1768은 검증6/반박4/미확정1(AMZN) 그대로다. calibration eval1771은 50회/550관찰/454성숙/96미확정 그대로다. 이력·feedback·calibration 전체 레코드 hash를 배포 전후 대조했다. weight 검토 차단과 항목별 주문 차단도 보존했다.
- 실제 localhost 터널을 통한 Chromium: 1440px/390px에서 두 대기 표시, AMZN 판단 보류, 누적 관찰 설명, `/portfolio/coverage/details`를 확인했다. 두 화면 모두 HTTP200, JS 오류0, 문서 가로 넘침0.

## 실행 중 발견하고 수정한 회귀

첫 배포 후 브라우저 접속이 30초 제한에 걸렸다. 새 일정 CTE가 과거 실행 행으로 인라인되어 쿼리 비용 추정치가 커지고 PostgreSQL JIT의 고비용 최적화가 활성화됐다. 실제 전체 SQL EXPLAIN ANALYZE는 기존 1.973초 → 첫 수정15.534초였고, 기대 작업별 일정 CTE를 materialized로 고정한 후보는1.994초였다. JIT 자체를 끄거나 DB 설정을 바꾸지 않았다. 최종 배포 쿼리는 1.946초로 재확인했다(`evidence/query-performance.json`).

HTTP 전체 응답은 SQL만의 시간이 아니다. 보정 후 단독 조회 7.808초를 관찰했으며 API 조합/운영 상태 조회 비용은 별도 개선 여지로 남긴다. 첫 화면 검증의 상세 경로도 `/portfolio/coverage`에서 실제 상세 경로 `/portfolio/coverage/details`로 바로잡았다. 고정 헤더가 섹션 캡처의 라벨을 가리던 문제는 실제 스크롤 위치를 조절해 다시 캡처했다.

## 다음 점검

추천 성과의 현재 조회는 `overdue_outcomes_ready` / 미처리 21개 / 다음 측정일 2026-09-14이고, 저장된 action router eval 1781(기준일 2026-09-11)은 `no_op_wait_until_next_due_date`다. 기준일·대상과 거래일 입력을 대조한 뒤 필요한 자동 실행/표시 보정을 결정한다. 지금 기록만으로 두 상태가 같은 대상을 뜻한다고 단정하지 않는다.

EROK 원천 제한, 검토 결정의 반박 4개, 외부 알림 미검증은 이번 표시 변경으로 해제하지 않는다. 평가 단위의 독립성이나 검토 판정 의미를 바꾸는 작업, 추천 weight 변경 및 실거래는 별도 경계를 따른다.
