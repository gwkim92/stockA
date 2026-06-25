const INTERNAL_TERM_REPLACEMENTS = [
  ["pipeline-run-", "최근 작업 기록 "],
  ["pipeline", "작업"],
  ["runner", "실행 기록"],
  ["artifact", "결과 기록"],
  ["fallback", "보조 경로"],
  ["live DB", "운영 데이터"],
  ["fixture", "예시 데이터"],
  ["paper validation", "가상 매매 검증"],
  ["Paper validation", "가상 매매 검증"],
  ["paper trade", "가상 매매"],
  ["broker submit", "증권사 주문 제출"],
  ["order boundary", "실거래 제한"],
  ["order_boundary", "실거래 제한"],
  ["read_only_no_order", "읽기 전용, 실거래 주문 차단"],
  ["source blocker", "원천 근거 부족"],
  ["active share", "벤치마크와 다른 비중"],
  ["outcome window", "성과 측정 기간"],
  ["weight review", "추천 산식 검토"],
  ["quality gate", "품질 기준"],
] as const;

const INVESTOR_CODE_COPY: Readonly<Record<string, string>> = {
  "coverage status missing_thesis": "투자 논리 연결 누락",
  "covered thesis and outcome remain valid": "투자 논리와 성과 측정이 유효합니다.",
  exclude: "제외",
  monitor_or_accumulate: "관찰 또는 분할 매수",
  needs_thesis_review: "투자 논리 보강 필요",
};

export function investorCopy(value: string | number | boolean | null | undefined): string {
  if (value === null || value === undefined || value === "") {
    return "정보 없음";
  }
  if (typeof value === "number") {
    return value.toLocaleString("ko-KR");
  }
  if (typeof value === "boolean") {
    return value ? "예" : "아니오";
  }
  if (INVESTOR_CODE_COPY[value]) {
    return INVESTOR_CODE_COPY[value];
  }

  return INTERNAL_TERM_REPLACEMENTS.reduce(
    (copy, [internalTerm, investorTerm]) => copy.replaceAll(internalTerm, investorTerm),
    value.replaceAll(/pipeline-run-\d+/g, "최근 작업 기록"),
  )
    .replaceAll(/\beval-run-\d+\b/g, "품질 평가 기록")
    .replaceAll(/\s+/g, " ")
    .trim();
}
