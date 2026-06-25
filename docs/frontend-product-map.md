# Frontend Product Map

## Product Boundary

The primary user is a Korean long-horizon investor. The secondary user is the operator maintaining collection, AI, scheduling, and trading-safety infrastructure.

Primary reading order:

`오늘 → 시장 → 사이클·뉴스 → 종목 → 추천 → 포트폴리오·성과`

Operations are available through a separate utility entry and never define the primary navigation.

## Route Roles

| Route | Area | User question | Dominant conclusion | Next route |
| --- | --- | --- | --- | --- |
| `/` | 투자 판단 | 오늘 무엇이 달라졌는가? | 시장, 새 근거, 추천, 보유 위험의 우선순위 | `/market-map` |
| `/market-map` | 투자 판단 | 자산군 전체의 압력은 어디에 있는가? | cross-asset regime과 충격 | `/cycle-map` |
| `/cycle-map` | 투자 판단 | 상위 흐름이 어느 테마와 종목으로 전파되는가? | 계층형 사이클 경로 | `/intelligence` |
| `/cycles` | 리서치 상세 | 사이클 상태를 표로 비교하면 무엇이 다른가? | 상태·점수·전환 가능성 비교 | `/cycle-map` |
| `/intelligence` | 투자 판단 | 어떤 뉴스 흐름이 투자 판단을 바꾸는가? | 시장 서사, 반대 근거, 영향 대상 | `/ai-evidence` |
| `/events` | 리서치 상세 | 실제로 어떤 원천 뉴스가 들어왔는가? | 시간순 원천 뉴스 원장 | `/intelligence` |
| `/events/classification` | 운영 관리 | 규칙 분류가 어떤 태그를 붙였는가? | 1차 분류 품질 | `/ai-evidence` |
| `/ai-evidence` | 리서치 상세 | AI가 구조화한 근거는 무엇인가? | 통과·차단 근거 목록 | `/intelligence` |
| `/ai-evidence/[evidenceId]` | 리서치 상세 | 이 해석이 원문과 연결 결과에 근거하는가? | 번역, 구조화, 검증, 영향 경로 | `/recommendations` |
| `/ai-evidence/blocked` | 운영 관리 | 어떤 후보가 왜 차단됐는가? | 차단 사유와 품질 경계 | `/ai-evidence` |
| `/ai-evidence/results` | 리서치 상세 | 통과한 근거는 어디에 사용됐는가? | canonical impact와 연결 대상 | `/recommendations` |
| `/source-documents/[documentId]` | 리서치 상세 | 해석의 원천 문장은 무엇인가? | 한국어 요약과 원문 발췌 | `/ai-evidence` |
| `/stocks` | 투자 판단 | 현재 분석할 종목은 무엇인가? | 추천·보유·관찰 우선순위 | `/stocks/[symbol]` |
| `/stocks/[symbol]` | 투자 판단 | 이 종목을 지금 왜 보거나 피해야 하는가? | 사업·재무·가치·사이클·위험 종합 | `/recommendations` |
| `/themes/[themeKey]` | 리서치 상세 | 테마의 현재 상태와 노출 종목은 무엇인가? | 테마 상태와 전파 경로 | `/cycle-map` |
| `/recommendations` | 투자 판단 | 어떤 후보가 판단 단계에 있는가? | 행동 경계와 근거 품질 | `/recommendations/[recommendationId]` |
| `/recommendations/[recommendationId]` | 투자 판단 | 이 판단은 어떤 근거와 위험을 갖는가? | 기대·위험·반대 논리·portfolio fit | `/portfolio/coverage` |
| `/theses/[thesisId]` | 리서치 상세 | 투자 논리가 아직 유효한가? | 성립 조건, catalyst, invalidation | `/recommendations` |
| `/portfolio/coverage` | 포트폴리오 | 보유 위험과 논리 공백은 어디인가? | 집중도, thesis, benchmark drift | `/performance` |
| `/performance` | 포트폴리오 | 과거 판단이 실제로 효과가 있었는가? | benchmark-relative outcome과 표본 성숙도 | `/portfolio/coverage` |
| `/paper-trading` | 포트폴리오 | 추천이 안전하게 가상 검증 가능한가? | 실행 가능·차단·대기 상태 | `/trading-readiness` |
| `/data-health` | 운영 관리 | 데이터와 자동화가 신뢰 가능한가? | freshness, incidents, next retry | `/` |
| `/admin/ai-agents` | 운영 관리 | AI provider와 인증이 정상인가? | model, quota, OAuth, smoke | `/data-health` |
| `/trading-readiness` | 운영 관리 | 거래 안전 경계가 잠겨 있는가? | permission, limits, kill switch | `/paper-trading` |
| `/remediation` | 운영 관리 | 어떤 판단 공백을 해결해야 하는가? | 종목·위험별 조치 목록 | `/portfolio/coverage` |

## Copy Boundary

- Investor pages state facts, implications, risks, and destinations.
- Operator pages may show job, provider, run, and artifact metadata.
- Korean interpretation precedes English source text.
- `확인한다`, `봐야 한다`, and system-operation tutorials are not page conclusions.
- Empty states distinguish no data, stale data, source limitation, safety block, and system error.
