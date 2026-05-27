# uxui-full-page-audit-v1 Audit

## Coverage

- target: `http://127.0.0.1:13000`
- desktop viewport: `1440x1100`
- mobile viewport sample: `390x844`
- visited routes: `/`, `/data-health`, `/intelligence`, `/cycle-map`, `/events`, `/events/classification`, `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked`, `/ai-evidence/ai-evidence-251`, `/recommendations`, `/recommendations/recommendation-67`, `/stocks`, `/stocks/SPY`, `/stocks/EROK`, `/portfolio/coverage`, `/paper-trading`, `/trading-readiness`, `/performance`, `/remediation`, `/cycles`
- route status: all visited routes returned HTTP `200`
- console/page errors: no blocking browser errors found in this pass
- evidence artifacts: `dogfood-output/uxui-full-page-audit-v1/`

## Anti-Patterns Verdict

- fail: the product has useful data, but too many pages still feel like generated internal status dashboards rather than a confident investment cockpit.
- the largest problem is not visual polish. It is information architecture, copy discipline, and route responsibility.
- repeated decision-strip explanations, long card grids, technical terms, and giant ledger pages create cognitive overload.

## Top Findings

### Critical 1. News/AI information architecture is still split by implementation, not user job

- routes: `/intelligence`, `/events`, `/events/classification`, `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked`, `/ai-evidence/ai-evidence-251`
- evidence:
  - `/ai-evidence` desktop screenshot height: `27525px`
  - `/ai-evidence/results` desktop screenshot height: `26445px`
  - `/ai-evidence/blocked` desktop screenshot height: `24730px`
  - `/intelligence` mobile screenshot height: `14267px`
- impact: 사용자는 “뉴스 원장, 1차 분류, AI 후보, 통과 결과, 차단 결과”가 왜 따로 있는지 알기 전에 같은 설명과 리스트를 반복해서 보게 된다.
- fix:
  - `/intelligence`는 “오늘의 흐름 요약과 문제 후보” 허브로 줄인다.
  - `/events`는 원천 뉴스 원장만 맡긴다.
  - `/events/classification`은 1차 태그 오류 찾기만 맡긴다.
  - `/ai-evidence`는 AI 후보 queue만 맡긴다.
  - `/ai-evidence/results`는 통과 결과만 맡긴다.
  - `/ai-evidence/blocked`는 차단 이유와 복구 가능성만 맡긴다.
  - 각 페이지 상단의 반복 설명은 1개 문장과 다음 action만 남긴다.

### Critical 2. “검토”를 말하지만 실제 검토 행동이 없다

- routes: `/`, `/intelligence`, `/ai-evidence/ai-evidence-251`, `/remediation`, `/recommendations`
- evidence:
  - home: `사람이 확인할 항목`, `지금 사람이 처리해야 할 것`
  - AI detail: `검토한다`, but no approve/reject/save action exists
  - remediation: duplicate TSLA/MSFT tickets say 사람이 검토해야 한다
- impact: 사용자는 무엇을 눌러야 검토가 끝나는지 모른다. 실제 write API가 없으면 “검토”라는 단어는 상태가 아니라 안내문으로만 보여야 한다.
- fix:
  - write action이 없는 곳은 `검토 완료`가 아니라 `판단 근거 확인`으로 바꾼다.
  - 사람이 하는 기능이 없으면 `사람이` 표현을 제거하고 `운영 항목`, `AI 검토 결과`, `보완 후보`로 바꾼다.
  - 저장형 검토는 별도 task에서 audit write boundary가 생긴 뒤 추가한다.

### High 1. 개발자/운영자 용어가 사용자 화면에 섞여 있다

- routes: `/`, `/data-health`, `/ai-evidence/*`, `/stocks/*`, `/recommendations/*`, `/portfolio/coverage`, `/paper-trading`, `/trading-readiness`
- examples:
  - `weight 검토`, `broker submit`, `runner`, `artifact`, `eval-run`, `validator`, `taxonomy`, `Codex OAuth`, `inline`
- impact: 한국어 투자 사용자는 이 단어를 보고 시스템 상태인지 투자 판단인지 구분하기 어렵다.
- fix:
  - user copy dictionary를 만든다.
  - `weight` -> `추천 산식` or `목표 비중`
  - `broker submit` -> `증권사 주문 전송`
  - `runner` -> `자동 실행 작업`
  - `artifact` -> `저장된 분석 결과`
  - `eval-run` -> `검증 기록`
  - `validator` -> `자동 검증`
  - `taxonomy` -> `분류 체계`
  - technical identifiers are hidden behind expandable “운영 세부정보”.

### High 2. AI evidence detail has a Korean translation gap at the wrong level

- route: `/ai-evidence/ai-evidence-251`
- evidence: step trace says `한국어 번역 없음`, while representative news cards below have Korean translated titles and summaries.
- impact: 사용자는 원천 대조 단계에서 “한국어 번역 없음”을 보고 바로 불신한다. 실제로는 대표 뉴스 번역이 있는데 cluster-level fallback이 없다.
- fix:
  - cluster evidence should show `korean_title/korean_summary` when available.
  - if cluster-level translation is missing, fallback to representative news Korean title/summary.
  - label should say `묶음 요약 번역 없음` only if neither cluster nor representative translation exists.

### High 3. Data-health is still an operations log, not a decision gate

- route: `/data-health`
- evidence:
  - desktop screenshot height: `31545px`
  - mobile screenshot height: `60825px`
- impact: 수집·분석 상태는 중요한데, 현재는 운영 로그가 너무 길어 “오늘 문제인가 아닌가”를 놓친다.
- fix:
  - top: 5 gate summary only.
  - middle: attention groups only.
  - bottom: raw runs, artifacts, IDs are collapsed under “운영 세부정보”.
  - source-limited, outcome-wait, investment-review gates must remain visible but plain Korean.

### High 4. Stock list and action queues lack clear click affordance and prioritization

- routes: `/stocks`, `/remediation`
- evidence:
  - `/stocks` desktop shows a long table; mobile becomes a long stack of cards but primary click target is not obvious.
  - `/remediation` repeats TSLA/MSFT tickets with the same reason.
- impact: 사용자는 어떤 종목부터 눌러야 할지, 같은 항목이 왜 여러 번 반복되는지 알기 어렵다.
- fix:
  - `/stocks`: add search/filter, “추천 있음/보유 중/뉴스 있음/원천 차단” filters, and a visible `종목 열기` action per row/card.
  - `/remediation`: group duplicate tickets by symbol/reason and show count + latest update.

### Medium 1. Some AI/theme relationships still look suspicious

- routes: `/intelligence`, `/ai-evidence/results`, `/cycles`
- examples:
  - SpaceX/Space Force satellite contract appears inside `에너지·지정학`.
  - quantum IPO news is attached to `기술 도메인` rather than the more specific `양자컴퓨팅·정책 수혜`.
- impact: UI가 아무리 좋아도 관계 설명이 틀리면 추천 근거 신뢰도가 떨어진다.
- fix:
  - route-level UI should show “왜 이 테마인가” with evidence span.
  - quality audit should flag theme specificity downgrade and suspicious theme-stock combinations.

### Medium 2. Mobile technically works, but page length is unacceptable

- routes: `/data-health`, `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked`, `/intelligence`, `/stocks`
- evidence:
  - `/data-health` mobile: `60825px`
  - `/intelligence` mobile: `14267px`
  - `/stocks` mobile: `9896px`
- impact: mobile에서 한 페이지를 끝까지 읽는 사용자는 거의 없다. 핵심 판단은 상단 1-2 화면 안에 있어야 한다.
- fix:
  - cap default lists to top 5-10.
  - add filters and “더 보기” routes.
  - keep raw ledgers separate from decision screens.

## What Is Working

- all audited routes load with HTTP `200`.
- no blocking console/page errors were found.
- Korean translation exists for many individual news cards.
- read-only/no-order boundary is visible and consistently blocks live order flow.
- home page now correctly surfaces outcome wait dates before weight review.

## Refactor Sequence

1. `ux-copy-system-and-glossary-v1`
   - replace user-facing technical terms and “사람이 검토” copy across top routes.
   - no schema/scoring changes.

2. `news-ai-information-architecture-v4`
   - make `/intelligence` a short hub.
   - reduce duplicate explanations across `/events`, `/events/classification`, `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked`.
   - add cluster-level Korean translation fallback on AI evidence detail.

3. `data-health-decision-gate-redesign-v2`
   - compress `/data-health` into gate summary + attention groups + collapsed operation details.

4. `stocks-list-action-affordance-v1`
   - add visible row/card actions, filters, and priority grouping.

5. `remediation-queue-dedup-v1`
   - group duplicate TSLA/MSFT style remediation tickets and make “what to do next” explicit.

6. `mobile-page-length-hardening-v1`
   - default list caps, progressive disclosure, and mobile-first layout reductions.

## First Implementation Slice

- next task should be `ux-copy-system-and-glossary-v1`.
- reason: it is the lowest-risk systemic fix and immediately removes the user-visible “개발자 용어/사람 검토/weight/broker/runner/artifact” problem without changing data, scoring, or backend behavior.
