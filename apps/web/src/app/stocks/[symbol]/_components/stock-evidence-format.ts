import type { Route } from "next";

import { koCode, koLabel } from "@/lib/korean-labels";

export function formatStoryBasis(basis: readonly string[]) {
  const labels: Record<string, string> = {
    same_title_signature: "제목 핵심 단어",
    same_source_document: "원천 문서 연결",
    same_theme: "테마 연결",
  };
  if (basis.length === 0) {
    return "단일 이벤트";
  }
  return basis.map((item) => labels[item] ?? koCode(item)).join(" · ");
}

export function formatEventDate(value: string) {
  return value ? value.slice(0, 10) : "날짜 없음";
}

export function evidenceChunkPreview(value: string | null | undefined) {
  if (!value) {
    return "문서 미리보기 없음";
  }
  const titleMatch = value.match(/Title:\s*(.*?)(?:\s+Summary:|\s+Published\/Event At:|$)/);
  if (titleMatch?.[1]) {
    const text = titleMatch[1].toLowerCase();
    if (/(fed|warsh|rate|rates|treasury|bond|yield|inflation)/.test(text)) {
      return "한국어 요약: 금리·연준 관련 원천 근거";
    }
    if (/(oil|iran|hormuz|crude|energy|gas|xom|drilling)/.test(text)) {
      return "한국어 요약: 에너지·지정학 관련 원천 근거";
    }
    if (/(quantum|qubit|rigetti|d-wave|ionq|qbts|qubt|ibm)/.test(text)) {
      return "한국어 요약: 양자컴퓨팅·정책 수혜 관련 원천 근거";
    }
    if (/(nvidia|semiconductor|chip|qualcomm|skyworks|qorvo|tower semiconductor|tsem)/.test(text)) {
      return "한국어 요약: AI 반도체 사이클 관련 원천 근거";
    }
    return "한국어 요약: 시장 뉴스 흐름 관련 원천 근거";
  }
  return koLabel(value.split(" Retrieval context:")[0] ?? value);
}

export function stockEvidenceGuardrails() {
  return [
    "읽기 전용 상태다. 추천 점수, 포지션, 주문을 변경하지 않는다.",
    "민감한 접속 정보와 API 키는 화면에 노출하지 않는다.",
    "새 분석을 만들지 않고 저장된 근거만 보여준다.",
  ];
}

export function stockEvidenceProviderLabel(provider: string) {
  if (provider === "codex_oauth") {
    return "심화 근거 분석";
  }
  if (provider === "fixture") {
    return "검증용 샘플 분석";
  }
  return koCode(provider);
}

export function stockEvidenceHref(evidenceId: string | null) {
  return evidenceId ? (`/ai-evidence/${evidenceId}` as Route) : null;
}

export function stockEventSourceDocumentHref(documentId: string | null) {
  return documentId ? (`/source-documents/${documentId}` as Route) : null;
}

export function stockEventsHref(symbol: string) {
  return `/events?symbol=${encodeURIComponent(symbol)}` as Route;
}

export function stockRecommendationHref(recommendationId: string) {
  return `/recommendations/${recommendationId}` as Route;
}

export function stockThesisHref(thesisId: string) {
  return `/theses/${thesisId}` as Route;
}
