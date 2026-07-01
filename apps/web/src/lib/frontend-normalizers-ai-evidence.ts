import { ensureRecord, isRecord, type MutableRecord, withDefault } from "./frontend-normalizer-utils";

export function normalizeAiEvidenceDetailPayload(data: MutableRecord) {
  withDefault(data, "cluster_summary", null);
  withDefault(data, "cluster_events", []);
  withDefault(data, "retrieval_context_summary", {
    as_of_date: "",
    known_themes: [],
    theme_edges: [],
    current_event_impacts: [],
    recent_similar_events: [],
  });
  withDefault(data, "audit_notes", []);
  withDefault(data, "extracted_fields", []);
  withDefault(data, "visibility_trace", {
    summary_ko: "AI 근거 가시성 경로가 아직 충분히 연결되지 않아 기본 경로만 표시한다.",
    source: {
      status: data.source_document_id ? "linked" : "missing",
      source_document_id: typeof data.source_document_id === "string" ? data.source_document_id : "",
      source_document_count: data.source_document_id ? 1 : 0,
      source_chunk_count: Array.isArray(data.source_chunks) ? data.source_chunks.length : 0,
      message_ko: data.source_document_id ? "원천 문서가 연결되어 있다." : "원천 문서 연결이 아직 없다.",
    },
    translation: {
      status: data.korean_title || data.korean_summary ? "translated" : "missing",
      translated_event_count: data.korean_title || data.korean_summary ? 1 : 0,
      translation_confidence: typeof data.translation_confidence === "number" ? data.translation_confidence : null,
      message_ko: "번역 추적 정보가 아직 충분히 연결되지 않았다.",
    },
    ai_structure: {
      status: "stored",
      provider: isRecord(data.extraction_run) && typeof data.extraction_run.provider === "string" ? data.extraction_run.provider : "not_available",
      model_id: isRecord(data.extraction_run) && typeof data.extraction_run.model_id === "string" ? data.extraction_run.model_id : "not_available",
      evidence_type: typeof data.evidence_type === "string" ? data.evidence_type : "unknown",
      extracted_field_count: Array.isArray(data.extracted_fields) ? data.extracted_fields.length : 0,
      theme_impact_count: 0,
      instrument_impact_count: 0,
      cluster_event_count: 0,
      message_ko: "저장된 구조화 근거를 표시한다.",
    },
    validator: {
      status: "not_available",
      quality_gate: isRecord(data.extraction_run) && typeof data.extraction_run.quality_gate === "string" ? data.extraction_run.quality_gate : "not_available",
      blocked: false,
      decision_ko: "검증 추적 정보 없음",
      reasons_ko: ["검증 상세 이유가 아직 충분히 연결되지 않았다."],
    },
    recommendation_linkage: {
      status: "not_available",
      target_symbol: isRecord(data.instrument) && typeof data.instrument.symbol === "string" ? data.instrument.symbol : "",
      theme_key: isRecord(data.classification) && typeof data.classification.theme_key === "string" ? data.classification.theme_key : "",
      message_ko: "추천 연결 경로가 아직 충분히 연결되지 않았다.",
    },
    steps: [],
    read_only_boundary: {
      live_llm_call_enabled: false,
      write_enabled: false,
      broker_submit_allowed: false,
      order_boundary: "read_only_no_order",
    },
  });
  const candidate = data.news_candidate;
  if (isRecord(candidate)) {
    withDefault(candidate, "theme_impacts", []);
    withDefault(candidate, "instrument_impacts", []);
  }
}
