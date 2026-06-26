# frontend-product-map-and-copy-contract-v1 Handoff

## Status

- implemented locally as the copy/route contract for the professional investment UX normalization sequence.

## Route Role Contract

| Route | Role | Core question | First-screen conclusion |
| --- | --- | --- | --- |
| `/` | Investor | 오늘 무엇을 먼저 봐야 하는가 | 시장 흐름, 새 근거, 추천 변화, 보유 위험, 시스템 이상 |
| `/market-map` | Investor | 시장 체제가 어디로 기울고 있는가 | 지수·금리·달러·원자재·변동성·신용의 방향 |
| `/cycle-map` | Investor | 거시에서 종목까지 어떤 사이클이 연결되는가 | 거시 → 섹터/도메인 → 테마 → 종목 → 추천/보유 영향 |
| `/intelligence` | Investor | 뉴스와 AI 근거가 어떤 시장 흐름으로 해석됐는가 | 주요 흐름, 반대 근거, 영향 테마와 종목 |
| `/ai-evidence` | Investor | 원천 뉴스가 어떤 투자 근거가 됐는가 | 원천 뉴스 → 한국어 번역 → AI 구조화 → 자동 검증 → 영향 경로 |
| `/stocks` | Investor | 어떤 종목을 봐야 하는가 | 전일 대비, 보유 여부, 분석 상태, 추천 연결 |
| `/stocks/[symbol]` | Investor | 이 종목은 지금 투자 판단에 쓸 수 있는가 | 상품 유형, 가격, 보유 현실, 분석 커버리지, 핵심 근거 |
| `/recommendations` | Investor | 추천 후보 중 무엇을 비교해야 하는가 | 근거 충족도, 차단 사유, 포지션 현실 |
| `/recommendations/[id]` | Investor | 왜 이 추천이 나왔고 실행은 왜 막혀 있는가 | 결론, 점수, 리스크, 보유 여부, 주문 차단 |
| `/portfolio/coverage` | Investor | 보유 포지션이 이익인지 손실인지, 위험은 무엇인가 | 평단가, 평가손익, 수익률, benchmark 대비 상태 |
| `/paper-trading` | Investor | 가상 검증은 실행 가능한가, 차단됐는가 | 실행 가능, 안전 차단, 데이터 부족, 승인 필요, 실거래 비활성 |
| `/data-health` | Operations | 수집·분석·AI·스케줄러가 정상인가 | 장애 영향, 최근 실패, 다음 자동 재시도 |
| `/admin/ai-agents` | Operations | AI provider와 모델 운영 상태는 어떤가 | 인증, 비용, 재로그인, smoke 상태 |
| `/trading-readiness` | Operations | 실거래 차단 경계와 안전장치는 유지되는가 | read-only, kill switch, order submit 차단 |
| `/remediation` | Operations | 어떤 데이터·분석 공백을 보완해야 하는가 | source gap, quality gap, action router 상태 |

## Forbidden Investor Copy

- Internal execution: `pipeline`, `runner`, `artifact`, `job_id`, `run_id`.
- Data plumbing: `fallback`, `canonical`, `shadow`, raw provider status.
- Raw codes: snake_case status, raw enum, internal profile names unless inside operations details.
- Ambiguous action copy: `검토 가능`, `확인한다`, `봐야 한다`, `미수집`.

## Implemented

- Route role contract and forbidden investor copy list are recorded here and in `contract.md`.
- Follow-up implementation used this contract to add presentation view models and investor/operations boundary wording.

## Next

- Keep this file as the route/copy contract for subsequent page decomposition work.
