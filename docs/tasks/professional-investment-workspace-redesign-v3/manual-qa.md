# professional-investment-workspace-redesign-v3 Manual QA

## Viewports

| Viewport | Route | Result |
| --- | --- | --- |
| 375x844 | `/data-health` | 실제 EC2 읽기 데이터, 운영 콘솔 분리, 자연스러운 한국어 줄바꿈, metadata square cells, horizontal overflow 없음 |
| 768x900 | `/stocks` | inverse hero 대비 개선, 투자 결론 우선, horizontal overflow 없음 |
| 1280x900 | `/cycle-map` | 거시·도메인·테마·종목 흐름 위계, 지표 strip, horizontal overflow 없음 |

## Browser Checks

- 투자 화면에서 알려진 raw code `CHINA ADR COVERAGE`, `monitor_or_accumulate`, `needs_thesis_review`, `missing_thesis`가 노출되지 않는다.
- 운영 화면에서 `missing_api_key`, `admin_key_missing`, `provider health cache`, `active 추천`이 사용자 문구로 변환된다.
- `/stocks` 표는 800px 이하에서 카드형 행으로 바뀌어 열과 상세 행동을 한 화면에서 읽을 수 있다.
- `/data-health` 상세 표는 좌우 이동 안내와 sticky first column을 제공한다.
- 최종 상세 표 안내는 `상세 표는 좌우로 이동할 수 있습니다.`로 줄여 고아 음절 줄바꿈을 제거했다.
- primary navigation은 실제 route href를 가진다.
- production HTML에는 `react-grab`, `react-scan` 진단 도구가 포함되지 않는다.

## Screenshot Evidence

- `/private/tmp/stockanalysis-mobile-data-health-v3.png`
- `/private/tmp/stockanalysis-mobile-data-health-v4.png`
- `/private/tmp/stockanalysis-tablet-stocks-v3.png`
- `/private/tmp/stockanalysis-desktop-cycle-map-v3.png`

## Remaining Manual Checks

- EC2 실제 데이터의 긴 문구와 비어 있는 상태는 배포 후 핵심 route smoke에서 다시 확인한다.
- 전체 25개 route의 모든 상태 조합을 시각 snapshot으로 고정하는 작업은 별도 visual-regression task로 남긴다.
