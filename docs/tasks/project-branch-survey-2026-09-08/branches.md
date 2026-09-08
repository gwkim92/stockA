# 원격 브랜치 전수 목록 — 2026-09-08

실제 remote branch 51개. `origin/HEAD`는 symbolic ref이므로 제외한다. +는 해당 branch에만, -는 develop에만 있는 도달 가능 커밋 수이며, squash 브랜치에서는 미반영 기능 수를 뜻하지 않는다. 날짜는 마지막 committer timestamp 기준이다. 기능 요약은 branch명·실제 커밋/변경 파일·관련 PR을 대조했다.

| 브랜치 | SHA | 마지막 날짜 | develop 대비 + / - | 상태 / PR | 주요 작업 |
|---|---|---|---|---|---|
| `develop` | `1d9d8dcc` | 2026-09-07 | +0 / -0 | 통합 기준 | 고정 개발·통합·배포 기준; 최근 PR #48 반영 |
| `main` | `ab8278f6` | 2026-05-01 | +0 / -1219 | 반영됨(조상) | 2026-05-01 공개 초기 baseline / GitHub 기본 브랜치 |
| `codex/ai-news-evidence-flow-clarity-v1` | `f0aaf010` | 2026-06-06 | +0 / -424 | 반영됨(조상) | 뉴스 → AI 해석 → 근거 확인의 화면 흐름·문구 |
| `codex/analysis-prompt-contract-v1` | `cd6a6c15` | 2026-09-06 | +0 / -85 | 반영됨(조상) · [#35 MERGED](https://github.com/gwkim92/stockA/pull/35) | 분석 prompt/output 계약과 정확한 사이클 근거 참조 |
| `codex/analysis-prompt-hardening-v2` | `b49c9dfc` | 2026-09-06 | +0 / -78 | 반영됨(조상) · [#36 MERGED](https://github.com/gwkim92/stockA/pull/36) | SEC scalar·뉴스 원문 인용/출처 경계 강화 |
| `codex/ci-fast-integrity-v1` | `65aabbb8` | 2026-09-01 | +0 / -203 | 반영됨(조상) · [#22 MERGED](https://github.com/gwkim92/stockA/pull/22) | 분석 무결성의 경량 CI |
| `codex/company-evidence-workspace-v1` | `37cf30c9` | 2026-09-05 | +0 / -98 | 반영됨(조상) · [#33 MERGED](https://github.com/gwkim92/stockA/pull/33) | 기업 분석·AI 근거 해석 화면 |
| `codex/company-review-notebook-v1` | `bcc08a70` | 2026-09-07 | +0 / -39 | 반영됨(조상) · [#42 MERGED](https://github.com/gwkim92/stockA/pull/42) | 원문 비교와 개인 기업 검토 노트 |
| `codex/cross-asset-provider-quality-and-market-map-v1` | `2393fa6c` | 2026-06-06 | +0 / -440 | 반영됨(조상) | cross-asset 공급 품질과 시장 지도 |
| `codex/cycle-operating-board-v1` | `562bbb46` | 2026-06-06 | +0 / -420 | 반영됨(조상) | 사이클 운영 화면 재구성 |
| `codex/cycle-quality-audit-hardening-v1` | `c84ec4fb` | 2026-06-06 | +0 / -418 | 반영됨(조상) | 사이클 AI 품질 감사 강화 |
| `codex/cycle-screen-entry-clarity-v1` | `0dbb47e4` | 2026-06-06 | +0 / -423 | 반영됨(조상) | 사이클 화면 진입 경로 설명 |
| `codex/data-health-decision-clarity-v1` | `5f1e8fd8` | 2026-06-06 | +0 / -426 | 반영됨(조상) | 데이터 건강 상태·자료 부족·조치 설명 |
| `codex/equity-atomic-persistence-v1` | `8de716fa` | 2026-09-06 | +0 / -54 | 반영됨(조상) · [#40 MERGED](https://github.com/gwkim92/stockA/pull/40) | 리서치 결과·호출 기록 원자적 저장과 receipt 대조 |
| `codex/equity-batch-isolation-v1` | `260d6e90` | 2026-09-06 | +0 / -59 | 반영됨(조상) · [#39 MERGED](https://github.com/gwkim92/stockA/pull/39) | 종목별 실패 격리·저장 실패 경계 유지 |
| `codex/equity-context-cutoff-v1` | `001e726d` | 2026-09-06 | +0 / -66 | 반영됨(조상) · [#38 MERGED](https://github.com/gwkim92/stockA/pull/38) | 명시적 UTC 기준시각으로 과거 입력 제한 |
| `codex/equity-research-contract-v3` | `c71e3f31` | 2026-09-06 | +0 / -72 | 반영됨(조상) · [#37 MERGED](https://github.com/gwkim92/stockA/pull/37) | 기업 분석 confidence·입력 출처 계약 |
| `codex/equity-result-check-v1` | `f85005a4` | 2026-09-06 | +0 / -49 | 반영됨(조상) · [#41 MERGED](https://github.com/gwkim92/stockA/pull/41) | 저장된 기업 분석 결과의 제한적 읽기 전용 진단 |
| `codex/fred-dollar-index-lag-policy-handoff-final-v1` | `76c02682` | 2026-06-06 | +0 / -433 | 반영됨(조상) | FRED 달러 지표 지연 정책의 검증 인계 |
| `codex/fred-dollar-index-lag-policy-v1` | `2af44e93` | 2026-06-06 | +0 / -434 | 반영됨(조상) | FRED 달러 지표 발표 지연 정책 |
| `codex/investor-home-reliability-v1` | `02f52d9e` | 2026-09-05 | +0 / -154 | 반영됨(조상) · [#25 MERGED](https://github.com/gwkim92/stockA/pull/25) | 투자자 홈 피드 독립성·신뢰할 수 있는 오류 상태 |
| `codex/local-mvp-runtime-aws-bootstrap` | `80869764` | 2026-06-06 | +0 / -441 | 반영됨(조상) · [#20 MERGED](https://github.com/gwkim92/stockA/pull/20) | 누적 로컬 MVP·AWS 운영 기반과 develop 배포 기준 |
| `codex/market-map-decision-clarity-v1` | `5f3aacf5` | 2026-06-06 | +0 / -432 | 반영됨(조상) | 시장 지도 판단 정보의 설명 |
| `codex/market-map-ec2-smoke-fix-v1` | `eb47ba62` | 2026-06-06 | +0 / -439 | 반영됨(조상) | 시장 지도 live source join 수정 |
| `codex/market-map-user-wording-v1` | `80a291f9` | 2026-06-06 | +0 / -431 | 반영됨(조상) | 시장 지도 사용자 문구 |
| `codex/market-map-wording-polish-v1` | `2515431f` | 2026-06-06 | +0 / -430 | 반영됨(조상) | 시장 지도 한국어 문구 보완 |
| `codex/news-theme-triage-v1` | `72577ad2` | 2026-09-06 | +0 / -93 | 반영됨(조상) · [#34 MERGED](https://github.com/gwkim92/stockA/pull/34) | 날짜별 뉴스 검토·테마 연결 |
| `codex/personal-review-inbox-v1` | `471b566d` | 2026-09-07 | +0 / -31 | 반영됨(조상) · [#43 MERGED](https://github.com/gwkim92/stockA/pull/43) | 개인 검토 inbox와 저장 노트 복구 |
| `codex/portfolio-performance-workspace-v1` | `6fa2a755` | 2026-09-05 | +0 / -111 | 반영됨(조상) · [#31 MERGED](https://github.com/gwkim92/stockA/pull/31) | 보유 현황·측정 성과·coverage 누락 화면 |
| `codex/professional-investment-workspace-redesign-v3` | `e8964a8a` | 2026-06-25 | +0 / -313 | 반영됨(조상) | 6월 전문 투자 workspace 재설계 |
| `codex/professional-source-gap-actionable-remediation-v1` | `aed06a61` | 2026-06-06 | +0 / -413 | 반영됨(조상) | 공식 Invesco QQQ 원천 자료 보완 경로 |
| `codex/recommendation-eval-history-v1` | `745bef33` | 2026-09-07 | +13 / -0 | 미병합 · [#49 OPEN](https://github.com/gwkim92/stockA/pull/49) | 불변 평가 스냅샷 조회 API·페이지네이션; UI 미연결 |
| `codex/recommendation-eval-persistence-v1` | `b8118e26` | 2026-09-07 | +10 / -1 | squash 반영됨 · [#48 MERGED](https://github.com/gwkim92/stockA/pull/48) | 평가 시점 추천 상태·계보·설정 snapshot 저장 |
| `codex/recommendation-investment-memo-v1` | `08601f95` | 2026-09-05 | +0 / -144 | 반영됨(조상) · [#28 MERGED](https://github.com/gwkim92/stockA/pull/28) | 추천 상세를 근거 연결 투자 메모로 구성 |
| `codex/recommendation-quality-audit-v1` | `d85ff130` | 2026-09-07 | +12 / -2 | squash 반영됨 · [#47 MERGED](https://github.com/gwkim92/stockA/pull/47) | 성과 화면의 추천 품질·요약 일치 감사 |
| `codex/recommendation-weight-review-prospective-evidence-foundation-v1` | `d6f70848` | 2026-09-02 | +0 / -177 | 반영됨(조상) · [#23 MERGED](https://github.com/gwkim92/stockA/pull/23) | 향후 weight 검토용 사전 기록 근거 기반 |
| `codex/recommendation-weight-review-prospective-evidence-live-observation-v1` | `abb6f303` | 2026-09-02 | +0 / -160 | 반영됨(조상) · [#24 MERGED](https://github.com/gwkim92/stockA/pull/24) | 사전 기록 근거의 guarded live 관찰 경계 |
| `codex/recommendation-weight-review-source-lineage-reconciliation-v1` | `e20a68d5` | 2026-09-01 | +0 / -209 | 반영됨(조상) · [#21 MERGED](https://github.com/gwkim92/stockA/pull/21) | 추천 weight 검토 자료의 원천 계보 대조 |
| `codex/research-discovery-workspace-v1` | `e2f603c1` | 2026-09-05 | +0 / -123 | 반영됨(조상) · [#30 MERGED](https://github.com/gwkim92/stockA/pull/30) | 종목·사이클·시장 탐색 UX |
| `codex/research-payload-contract-v1` | `d65a6c89` | 2026-09-07 | +0 / -14 | 반영됨(조상) · [#45 MERGED](https://github.com/gwkim92/stockA/pull/45) | producer와 reader 양쪽 리서치 서술 필드 검증 |
| `codex/research-review-state-continuity-v1` | `f661bb5b` | 2026-09-07 | +0 / -3 | 반영됨(조상) · [#46 MERGED](https://github.com/gwkim92/stockA/pull/46) | 필드 오류·원문 문맥을 저장/내보내기에 유지 |
| `codex/research-workspace-redesign-v1` | `dd4b5b02` | 2026-09-05 | +0 / -132 | 반영됨(조상) · [#29 MERGED](https://github.com/gwkim92/stockA/pull/29) | 반응형 리서치 workspace·디자인 체계 |
| `codex/review-continuity-v1` | `fcf4a318` | 2026-09-07 | +0 / -26 | 반영됨(조상) · [#44 MERGED](https://github.com/gwkim92/stockA/pull/44) | 저장된 검토 정체성 유지와 과거 판단 비교 |
| `codex/thesis-source-reader-v1` | `569ca6f6` | 2026-09-05 | +0 / -106 | 반영됨(조상) · [#32 MERGED](https://github.com/gwkim92/stockA/pull/32) | 투자 논리·원문 근거 읽기 화면 |
| `codex/tossinvest-market-data-agent-context-v1` | `343ad83f` | 2026-06-23 | +0 / -340 | 반영됨(조상) | TossInvest 시장 데이터를 AI 입력 문맥에 연결 |
| `codex/web-dependency-remediation-v1` | `91c851fb` | 2026-09-05 | +0 / -149 | 반영됨(조상) · [#27 MERGED](https://github.com/gwkim92/stockA/pull/27) | 웹 의존성 수정과 보안 audit CI |
| `codex/xag-fred-silver-proxy-auto-refresh-v1` | `97e32b6a` | 2026-06-06 | +0 / -436 | 반영됨(조상) | FRED 은 가격 대용 지표의 거시 갱신 편입 |
| `codex/xag-fred-silver-proxy-handoff-final-v1` | `c98406ea` | 2026-06-06 | +0 / -435 | 반영됨(조상) | 은 가격 대용 지표 검증 인계 |
| `codex/xag-fred-silver-proxy-provider-v1` | `7ba6f9bf` | 2026-06-06 | +0 / -437 | 반영됨(조상) | XAG용 FRED 은 가격 대용 공급자 |
| `codex/xag-provider-policy-visibility-v1` | `be93df98` | 2026-06-06 | +0 / -438 | 반영됨(조상) | XAG 공급 fallback 소진 상태 설명 |
| `feature/frontend-detail-routes` | `45fc2db5` | 2026-05-01 | +3 / -1219 | squash 반영됨 · [#1 MERGED](https://github.com/gwkim92/stockA/pull/1) | 초기 추천·thesis·AI 근거 상세 경로 |

## 각 브랜치 최근 이력과 파일 근거

전체 SHA, 최근 non-merge commit 5개와 해당 변경 파일, 관련 PR, 미병합 delta는 [branch-inventory.json](/Users/woody/Documents/ChatGPT/stockA/docs/tasks/project-branch-survey-2026-09-08/branch-inventory.json)에 저장했다. 최근 5개 로그는 짧은 브랜치에서는 조상 작업을 포함하므로 전용 작업 범위 전체와 같지 않다.

현재 원격 tag 0개. 삭제된 옛 브랜치의 PR 이력은 별도 `pull-requests.json`에서 볼 수 있다.
