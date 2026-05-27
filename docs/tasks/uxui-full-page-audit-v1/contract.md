# uxui-full-page-audit-v1 Contract

## Task Request

- request: 전체 UX/UI, 문구, 페이지 분할을 순차적으로 점검하고 refactor를 시작한다.

## Goal

- goal: 실제 브라우저에서 모든 주요 페이지를 점검해 사용자가 이해하기 어려운 문구, 중복 정보, 페이지 분할 실패, 빈값/오류, 모바일·레이아웃 문제를 정리하고, 이후 refactor 순서를 고정한다.

## Mutable Surface

- mutable surface:
  - `docs/tasks/uxui-full-page-audit-v1/*`
  - `dogfood-output/uxui-full-page-audit-v1/*`
  - follow-up implementation files only after audit findings are concrete

## Invariants

- Do not change recommendation scoring weights.
- Do not change benchmark definitions, portfolio positions, broker/order flow, live trading, or paper execution.
- Do not hide operational or source-limit states; rewrite them into user-comprehensible language instead.
- Do not make broad page rewrites without route-level findings and a follow-up slice.

## Scope

- Crawl primary cockpit routes via the EC2 local tunnel.
- Capture route status, title text, visible text excerpts, console/load errors where available, and screenshots.
- Produce a prioritized UX/UI audit report.
- Decide the first concrete refactor slice based on evidence.

## Verification

- verification command: `agent-browser --session uxui-full-page-audit-v1 open http://127.0.0.1:13000/`
- verification command: `agent-browser --session uxui-full-page-audit-v1 screenshot --annotate dogfood-output/uxui-full-page-audit-v1/screenshots/home.png`
- verification command: `curl -fsS http://127.0.0.1:13000/`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task uxui-full-page-audit-v1`

## Done Criteria

- [x] Primary routes are visited or route failures are recorded.
- [x] Audit report lists prioritized systemic issues and first refactor slice.
- [x] Handoff states exact next implementation step.
