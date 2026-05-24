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
- EC2 결과:
  - migration 0020 적용 완료
  - fixture provider smoke 성공: `run_id=691`, `invocation_id=945`
  - Codex OAuth smoke는 `401 token_invalidated`로 실패했지만 fallback 성공: `run_id=692`, `status=completed_with_fallback`
  - `cycle_community_ai_v2` summary row 2개 저장 확인

## Remaining Risk

- EC2 Codex OAuth 토큰이 무효화되어 실제 LLM summary는 아직 생성되지 않았다. EC2에서 Codex 재로그인이 필요하다.
- AI summary는 추천 점수에 반영하지 않는다. 추천 품질 반영은 다음 `recommendation-quality-calibration` 이후 별도 weight 변경 task에서만 가능하다.
