# Review

## Result

- 로컬 구현과 검증 완료.
- 새 CLI: `stockanalysis-operations cycle-community-ai-summary-v2-run`
- 저장 경로:
  - `ai.model_invocation`: provider/model/status/request_hash 기록
  - `ai.cycle_community_summary`: `summary_type='cycle_community_ai_v2'`로 한국어 AI summary 저장
- 출력 schema는 `korean_summary`, `key_drivers`, `causal_paths`, `supporting_events`, `conflicts`, `uncertainty`, `watchlist_symbols`를 포함한다.
- runner는 FastAPI 요청 중 AI를 호출하지 않고 batch CLI에서만 provider를 호출한다.
- Codex OAuth 실패 시 pipeline은 `succeeded_with_fallback`으로 끝나고 fixture summary를 저장한다.
- `/cycle-map`은 같은 날짜에 v2 AI summary가 있으면 한국어 AI summary를 우선 노출하고, 없으면 기존 deterministic v1 summary를 사용한다.

## Remaining Risk

- 실제 Codex OAuth 산출물 품질은 EC2 smoke에서 limit 기반으로 별도 확인해야 한다.
- AI summary는 추천 점수에 반영하지 않는다. 추천 품질 반영은 다음 `recommendation-quality-calibration` 이후 별도 weight 변경 task에서만 가능하다.
