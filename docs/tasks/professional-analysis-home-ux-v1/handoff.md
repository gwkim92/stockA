# professional-analysis-home-ux-v1 Handoff

## Status

- completed: home page has been restructured into a professional research desk layout. Local verification, EC2 deploy, EC2 build, route smoke, and browser smoke passed.

## Current Decision

- Rebuild only the home page information architecture first. The current biggest UX failure is that `/` repeats many operational sections and does not clearly say what to inspect first.
- Keep all investment and trading boundaries unchanged.

## Next Step

- exact next step: apply the same research-desk pattern to `/intelligence`, `/ai-evidence`, `/cycle-map`, and `/recommendations`, starting with `/intelligence`.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `git diff --check`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task professional-analysis-home-ux-v1`
- passed on EC2: `cd /opt/stockanalysis/app/apps/web && npm run typecheck && npm run build`
- passed on EC2: `systemctl is-active stockanalysis-web.service stockanalysis-frontend-api.service` returned `active active`.
- passed route smoke through `http://127.0.0.1:13000`: `/`, `/data-health`, `/intelligence`, `/ai-evidence`, `/cycle-map`, `/recommendations` all returned HTTP 200.
- passed browser smoke: `/` renders `오늘 투자 판단은`, `수집 신뢰도에서 주문 차단까지 같은 순서로 읽는다`, `핵심 분석 패킷`, and `거래 차단 안전 조건 3개 미충족`.
- passed browser smoke: stale phrases `차단 막힌 조건` and `broker boundary` were absent from the visible home snapshot.

## Risks

- This is a home-page UX pass only. The deeper `/intelligence`, `/ai-evidence`, `/cycle-map`, and `/recommendations` pages still need the same treatment in follow-up tasks.
