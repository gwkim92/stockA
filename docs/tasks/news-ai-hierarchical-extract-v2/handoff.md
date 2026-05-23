# Session Handoff

## Current Status

- 완료:
  - `DEFAULT_TEMPLATE_VERSION`을 `2026-05-23-hierarchical-ko-v3`로 올렸다.
  - Codex OAuth schema/prompt를 거시/도메인/테마/직접 종목/인과 경로/근거 span 구조로 확장했다.
  - parser는 기존 v2 `theme_code`/`instrument_impacts` artifact를 계속 읽을 수 있게 유지했다.
  - validator는 macro/domain/theme impact를 모두 `event.event_classification_impact` 경로로 검증한다.
  - 프론트 live adapter는 v2/v3 candidate artifact를 모두 payload로 노출한다.
- 막힌 점:
  - 없음.

## Exact Next Step

- exact next step: EC2에서 `news-rss-ai-extract-run --provider codex_oauth --execute --limit 1` smoke를 돌려 실제 Codex OAuth v3 artifact가 생성되는지 확인한다.
