# Session Handoff

## Current Status

- 상태: ec2_verified
- 기준일: 2026-05-22
- 완료:
  - `/events`와 `/ai-evidence` 화면 코드를 확인했다.
  - live adapter가 같은 이벤트/문서의 최신 artifact를 고르기 때문에 `news_cluster_summary`가 개별 후보처럼 보이는 root cause를 확인했다.
  - event list evidence 선택 우선순위를 `news_event_candidate`, `source_document_event`, `news_cluster_summary` 순으로 바꿨다.
  - event list API에 `evidenceType` filter를 추가했고 `/ai-evidence`는 `news_event_candidate`만 직접 조회한다.
  - event summary에 개별 후보, 뉴스 묶음, 미검토 카운트를 추가했다.
  - `/events`와 `/ai-evidence` 문구/목록을 개별 후보와 뉴스 묶음 기준으로 분리했다.
- 막힌 점:
  - 없음.

## Planned Fix

- `news_event_candidate`를 event list evidence 우선순위 1순위로 둔다.
- summary count를 개별 후보와 뉴스 묶음 증거로 분리한다.
- `/events`와 `/ai-evidence` 문구를 “원장”, “개별 후보”, “뉴스 묶음” 기준으로 정리한다.

## Verification Log

- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task event-ai-evidence-boundary`
- PASS: after `evidenceType` filter, `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- PASS: after `evidenceType` filter, `cd apps/web && npm run typecheck`
- PASS: after `evidenceType` filter, `cd apps/web && npm run build`
- PASS: after `evidenceType` filter, `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
- PASS: after `evidenceType` filter, `git diff --check`
- PASS: after `evidenceType` filter, `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task event-ai-evidence-boundary`
- PASS: EC2 HEAD `17223cf`, `stockanalysis-frontend-api.service` and `stockanalysis-web.service` active.
- PASS: EC2 `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter`.
- PASS: EC2 `cd apps/web && npm run typecheck && npm run build`.
- PASS: EC2 `/api/events?asOfDate=2026-05-22&eventType=all&evidenceType=news_event_candidate&limit=10` returns only `news_event_candidate` items, `item_count=10`, filtered total `event_count=24`.
- PASS: local tunnel `/events` HTTP 200 and shows separate metrics: event rows 117, individual AI candidates 24, news clusters 36, unreviewed 57.
- PASS: local tunnel `/ai-evidence` HTTP 200 and Playwright snapshot shows only `개별 후보` cards.

## Remaining

- `/events` still intentionally shows raw event rows, including broad flow items such as personal-finance or political-news RSS rows. They are now labeled as `뉴스 묶음 근거`, not individual candidate analysis. Next UI/data-quality work should decide whether `/events` needs default filters or source/category controls.

## Exact Next Step

- exact next step: continue page-by-page audit with `/events` default filtering and broad RSS source quality controls.
