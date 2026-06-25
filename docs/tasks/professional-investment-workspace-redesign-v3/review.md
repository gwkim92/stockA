# professional-investment-workspace-redesign-v3 Review

## Scope Review

- 투자자 1차 흐름을 `오늘 → 시장 → 리서치 → 종목 → 추천 → 포트폴리오`로 고정했다.
- 데이터 상태, AI 운영, 거래 안전, 보완 작업은 별도 운영 콘솔로 분리했다.
- 추천 점수, 반영 비중, DB schema, API DTO, benchmark, portfolio position, broker/order boundary는 변경하지 않았다.
- Next.js는 `16.2.4`의 공개 high 보안 권고를 해소하기 위해 동일 minor 패치인 `16.2.9`로 정확히 고정했다.

## Code Review

- 공통 shell, status, decision summary, metric strip, research section, presentation copy 경계를 추가했다.
- 투자 화면의 `pipeline`, `runner`, `artifact`, snake_case 판단 코드와 미번역 taxonomy 노출을 자동 검사한다.
- 운영 화면도 `equity_research`, `missing_api_key`, `admin_key_missing` 같은 raw 상태 코드를 별도 회귀식으로 검사한다.
- 레거시 `globals.css`는 아직 남아 있지만 새 화면의 색상·타이포·간격은 `DESIGN.md`와 `tokens.css`를 우선한다.
- 공용 `decision-brief-copy` 선택자 충돌과 `decision-brief-meta` pill 우선순위 충돌을 수정했다.
- 데이터 화면의 reveal은 투명도 변화 없이 transform만 사용해 전환 중 대비 저하를 제거했다.

## Slop And Test Assessment

- `remove-ai-slops` 관점에서 raw 내부 코드, 중복 운영 문구, ad-hoc 페이지 문자열 변환, 과도한 pill/card 반복을 점검했다. 이번 작업은 이를 presentation 계층과 공통 shell/status/research 컴포넌트로 이동했으며, 동작을 바꾸는 광범위한 레거시 정리는 수행하지 않았다.
- `programming` 기준의 250 LOC 초과 파일은 `data-health`, 종목 상세, 추천 상세, AI 근거 상세에 여전히 남는다. 해당 파일은 기존 대형 DTO 표현과 결합돼 있어 이번 시각 재설계 커밋에서 무리하게 분해하지 않고 후속 domain-component extraction task로 명시한다.
- 테스트가 fixture 값에만 과적합되지 않도록 실제 EC2 읽기 데이터로 홈, 데이터 상태, 핵심 경로를 추가 검증했다. fixture 전용 추천 ID는 live smoke의 품질 판정에 사용하지 않고, 실제 추천 ID를 배포 smoke에서 선택한다.
- raw-code 검사는 투자 경로뿐 아니라 운영 경로까지 포함한다. 실제 EC2 데이터에서 발견된 영문 portfolio review reason은 `koReason()` 경계로 수정하고 live-data 3개 뷰포트 테스트로 잠갔다.

## Verification

- `npm test`: 14 tests passed.
- `npm run typecheck`: passed.
- `npm run build`: passed on Next.js `16.2.9`.
- Playwright: desktop, tablet 768px, mobile 390px projects configured.
- Axe: 12 investor/operations core routes on all three projects passed with no serious/critical violations.
- `verify_frontend_api_contract.sh`: passed.
- `verify_project_execution_roadmap.sh`: passed.
- AWH task readiness: passed.
- `git diff --check`: passed.

## Residual Risk

- `data-health`, 종목 상세, 추천 상세는 여전히 큰 레거시 페이지다. 이번 작업은 presentation 경계와 시각 체계를 우선 분리했고, 도메인별 component extraction은 후속 refactor task가 필요하다.
- `npm audit`에는 Next.js 내부 `postcss@8.4.31`의 moderate 경고 2건이 남는다. 강제 override는 framework support 경계를 벗어나므로 적용하지 않았다.
- React Doctor는 기존 AI 운영 server action 4개에 사용자 인증 검사 부재를 보고했다. backend admin-action token 경계가 있으나 Next server action 자체의 사용자 인증은 별도 security task에서 닫아야 한다.
- repository-wide Python suite는 frontend 변경과 무관한 cadence env 및 로컬 FastAPI dependency 문제로 전부 통과하지 못한다. frontend contract와 browser regression은 별도로 통과했다.
