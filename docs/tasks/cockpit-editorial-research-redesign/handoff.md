# Session Handoff

## Active Task

- 이름: cockpit-editorial-research-redesign
- 담당: Codex
- 날짜: 2026-05-18

## Current Status

- 완료:
  - 공통 shell을 light editorial research terminal 스타일로 전환했다.
  - 상단 navigation을 번호형 운영 인덱스 문법으로 바꿨다.
  - 홈 화면을 manifest hero, 운영 관계도 SVG, status rail, review ledger, runtime ledger, route index로 재구성했다.
  - `remediation`, `data-health`, `cycles`를 같은 editorial/ledger 문법으로 2차 전환했다.
  - 기존 frontend API DTO, route, backend logic은 변경하지 않았다.
- 진행 중:
  - none.
- 막힌 점:
  - none.

## Implemented

- `apps/web/src/app/layout.tsx`
  - brand mark를 노드/엣지 형태로 바꾸고, navigation에 `00`~`10` index를 부여했다.
  - viewport theme color를 light cockpit palette에 맞췄다.
- `apps/web/src/app/page.tsx`
  - 기존 bento dashboard를 운영 원장형 홈으로 교체했다.
  - `getCockpitSnapshot()` 데이터는 그대로 사용한다.
  - 핵심 지표, 보완 큐, 첫 의사결정, runtime/budget 상태를 새 레이아웃에 배치했다.
- `apps/web/src/app/globals.css`
  - dark glass/bento palette를 paper/grid/line 기반 light theme로 전환했다.
  - 기존 상세 페이지가 쓰는 `bento-*`, `metric-*`, `btn-*` class도 새 문법으로 재스타일링했다.
- `apps/web/src/app/remediation/page.tsx`
  - 보완 큐를 hero, summary rail, ticket ledger, status count, decision boundary 패널로 재구성했다.
- `apps/web/src/app/data-health/page.tsx`
  - 데이터 상태를 runtime health summary, pipeline ledger, provider budget meter, gates/freshness, scheduler facts로 재구성했다.
- `apps/web/src/app/cycles/page.tsx`
  - 사이클 보드를 strategy summary rail과 theme cycle index row로 재구성했다.

## Verification

- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `git diff --check`
- Local runtime visual check:
  - fixture API: `http://127.0.0.1:8765`
  - Next.js app: `http://127.0.0.1:3001`
  - desktop screenshot: `.playwright-cli/page-2026-05-18T08-05-14-293Z.png`
  - lower desktop screenshot: `.playwright-cli/page-2026-05-18T08-05-43-838Z.png`
  - mobile screenshot: `.playwright-cli/page-2026-05-18T08-04-45-100Z.png`
  - remediation desktop lower screenshot: `.playwright-cli/page-2026-05-18T08-36-56-803Z.png`
  - data-health desktop lower screenshot: `.playwright-cli/page-2026-05-18T08-44-00-386Z.png`
  - data-health mobile screenshot: `.playwright-cli/page-2026-05-18T08-44-48-488Z.png`
  - cycles desktop screenshot: `.playwright-cli/page-2026-05-18T08-42-44-490Z.png`

## Remaining Risk

- `events`, `theme detail`, `recommendation`, `thesis`, `evidence`, `source document`, `coverage`, `performance`는 아직 global restyle 중심이고 route-specific editorial 구조는 아니다.
- 일부 backend 자유문장 reason은 길어서 ledger에서 그대로 표시된다. 다음 UI pass에서는 reason을 summary/detail로 나누는 것이 좋다.
- 브라우저 검증은 local dev server 기준이다. production `next start` smoke는 별도로 수행하지 않았다.
- Dev mode에서 확인 중 HMR websocket reconnect 로그가 일시적으로 남았다. 화면 렌더링과 production build는 통과했다.

## Exact Next Step

- `events`, `themes/[themeKey]`, `recommendations/[recommendationId]`, `theses/[thesisId]`를 같은 문법으로 3차 전환한다.
- 긴 보완 사유는 table cell에서 한 줄 요약 + detail route/link로 분리한다.
