import { koCode, koLabel } from "../korean-labels";

import { investorCopy } from "./copy";

const RECOMMENDATION_TERMS = [
  ["DCF-lite", "간이 현금흐름 평가"],
  ["페이퍼 검증", "가상 매매 검증"],
  ["broker flow", "실거래 연결"],
  ["read_only_no_order", "읽기 전용, 실거래 주문 차단"],
  ["source_data_blocked", "원천 근거 부족으로 차단"],
  ["macro-flow", "상위 흐름"],
  ["sec_companyfacts_missing_us_gaap_facts", "SEC 표준 재무 항목 없음"],
  ["ipo_prospectus_without_standard_periodic_financials", "정기 재무제표 전 공시만 존재"],
  ["fund_company_financial_model_not_applicable", "ETF·펀드라 기업 재무 모델 비적용"],
  ["accumulate_candidate", "분할 매수 신호"],
  ["base case", "기준 시나리오"],
  ["upside case", "상승 시나리오"],
  ["downside case", "하락 시나리오"],
  ["margin of safety", "안전마진"],
  ["confidence", "신뢰도"],
  ["valuation_snapshot", "밸류에이션 스냅샷"],
  ["valuation_margin_score", "밸류에이션 안전마진"],
  ["total_score", "총점"],
  ["recommendation_id", "추천 ID"],
  ["뉴스·AI 해석", "뉴스·투자 근거"],
  ["뉴스·AI", "뉴스 근거"],
  ["AI 근거", "투자 근거"],
  ["AI 검증", "품질 검증"],
  ["주문 경계", "실거래 상태"],
  ["거래 경계", "실거래 상태"],
  ["추천 총점", "최종 추천 점수"],
  ["총점 반영", "최종 점수 반영"],
  ["총점 미반영", "최종 점수 미반영"],
  ["점수 가중치", "점수 반영 비중"],
  ["가중치", "반영 비중"],
  ["financial statement model", "재무제표 모델"],
  ["valuation target range", "밸류에이션 목표가 범위"],
  ["industry competitive position", "산업 경쟁 위치"],
  ["equity research artifact", "AI 기업 리서치"],
  ["research artifact", "리서치 결과"],
  ["SEC/companyfacts", "SEC 표준 재무 원천"],
  ["SEC companyfacts", "SEC 표준 재무 원천"],
  ["segment", "사업부"],
  ["footnote", "주석"],
  ["guidance", "가이던스"],
  ["fundamental 구성요소", "재무·밸류에이션 항목"],
  ["투자 논리 lifecycle", "투자 논리 생애주기"],
  ["source event/AI evidence", "원천 이벤트/투자 근거"],
] as const;

const STOCK_TERMS = [
  ["AI 기업 리서치", "기업 리서치"],
  ["AI 리서치", "기업 리서치"],
  ["AI 분석 연결", "투자 근거 연결"],
  ["저장된 AI 구조화 결과", "저장된 투자 근거"],
  ["AI 구조화 결과", "투자 근거"],
  ["AI 구조화", "투자 영향"],
  ["뉴스 AI", "뉴스 근거"],
  ["accumulate_candidate", "분할 매수 후보"],
  ["hold_candidate", "보유 유지 후보"],
  ["reduce_watch", "비중 축소 관찰"],
  ["thesis", "투자 논리"],
  ["evidence review", "근거 확인"],
  ["paper validation gate", "가상 매매 검증"],
  ["paper validation", "가상 매매 검증"],
  ["valuation", "밸류에이션"],
  ["fund/ETF source layer", "ETF·펀드 근거"],
  ["fund_company_financial_model_not_applicable", "ETF·펀드라 기업 재무 모델 비적용"],
  ["source blocker", "부족한 원천 근거"],
  ["blocker", "차단 사유"],
  ["sec_companyfacts_missing_us_gaap_facts", "SEC 표준 재무 항목 없음"],
  ["financial_period_source_linkage", "재무 기간 원천 연결"],
  ["fundamental 구성요소 가중치", "재무·밸류에이션 항목 반영 비중"],
  ["SEC/companyfacts", "SEC 표준 재무 원천"],
  ["SEC companyfacts", "SEC 표준 재무 원천"],
  ["us-gaap", "미국 표준 회계 항목"],
  ["RAG", "저장 근거 관계망"],
  ["live DB smoke", "운영 데이터 연결 점검"],
  ["live DB", "운영 데이터"],
  ["fixture endpoint", "샘플 연결 경로"],
  ["fixture_not_available", "아직 없음"],
  ["fixture_fallback", "샘플 데이터 대기"],
  ["fixture", "샘플 데이터"],
  ["not_available", "아직 없음"],
  ["not available", "아직 없음"],
  ["read_only_fallback", "읽기 전용 대기"],
  ["stored_relationship_context", "저장 근거 관계망"],
  ["stored relationship context", "저장 근거 관계망"],
  ["Broad US Equity", "미국 광범위 주식"],
  ["ref.instrument", "상품 분류 기준"],
  ["gate", "확인 조건"],
  ["via", "기준"],
  ["상세 검토 가능", "상세 근거 확인"],
  ["검토 가능", "근거 확인"],
  ["확인 필요", "보강 필요"],
] as const;

const EVIDENCE_TERMS = [
  ["fixture에는 AI 근거 가시성 trace가 없어 기본 경로만 표시한다.", "저장된 상세 추적 정보가 부족해 확인 가능한 경로만 표시합니다."],
  ["fixture에는 validator 상세 이유가 없다.", "품질 차단 상세 사유가 아직 저장되지 않았습니다."],
  ["fixture 기준 번역 trace가 없다.", "번역 추적 정보가 아직 저장되지 않았습니다."],
  ["추천 연결 trace는 live DB에서 확인한다.", "추천 영향 정보는 최신 데이터에서 확인합니다."],
  ["live DB", "최신 운영 데이터"],
  ["validator", "품질 기준"],
  ["trace", "추적 정보"],
  ["fixture", "현재 데이터"],
  ["write", "쓰기 작업"],
  ["뉴스 AI 후보", "뉴스 투자 근거"],
  ["AI 후보", "투자 근거"],
  ["보유검토", "보유 상태 판단"],
  ["입력 후보", "입력 항목"],
  ["통과 후보", "통과 항목"],
  ["검토 후보", "판단 항목"],
  ["후보 상태", "항목 상태"],
] as const;

const PORTFOLIO_TERMS = [
  ["read_only_no_order", "읽기 전용, 실거래 주문 차단"],
  ["broker submit", "증권사 주문 제출"],
  ["broker", "증권사"],
  ["order boundary", "실거래 상태"],
  ["order_boundary", "실거래 상태"],
  ["eval_run_id", "검증 기록"],
  ["source_cadence_eval_run_id", "실행 주기 기록"],
  ["active share", "벤치마크와 다른 비중"],
  ["drift", "벤치마크 괴리"],
  ["benchmark", "벤치마크"],
  ["child runner", "후속 실행 기록"],
  ["runner", "실행 기록"],
  ["artifact", "결과 기록"],
  ["paper validation", "가상 매매 검증"],
  ["blocked", "차단"],
  ["pending", "대기"],
  ["no_op", "대기"],
  ["weight review", "추천 산식 변경 여부"],
  ["weight", "비중"],
  ["가중치", "추천 산식 반영 비중"],
  ["주문 경계", "실거래 상태"],
  ["가상 거래", "가상 매매"],
  ["커버리지", "연결 상태"],
  ["커버됨", "연결됨"],
] as const;

const PORTFOLIO_CODES: Record<string, string> = {
  add_blocked_until_evidence: "근거 보강 전 증액 금지",
  benchmark_drift_review: "벤치마크 괴리 확인",
  contradicted: "반박됨",
  execute_calibration: "누적평가 실행",
  execute_feedback: "사후평가 실행",
  has_contradictions: "반박 근거 있음",
  hold_with_thesis: "투자 논리 유지",
  needs_more_data: "추가 성과 필요",
  needs_position_review: "비중 점검 필요",
  needs_thesis_update: "투자 논리 보강",
  no_op_wait_for_outcome_window: "성과 관찰 기간 대기",
  reduce_review: "축소 필요성 확인",
  reduce_watch: "축소 관찰",
  review_required: "점검 필요",
  run_calibration_now: "누적평가 실행 필요",
  run_feedback_now: "사후평가 실행 필요",
  too_early: "관찰 기간 부족",
  validated: "검증됨",
  watch_small_position: "작은 비중 관찰",
  within_budget: "한도 내",
};

function applyTerms(value: string, terms: readonly (readonly [string, string])[]) {
  return terms.reduce((text, [from, to]) => text.replaceAll(from, to), value);
}

function normalizeValue(value: string | number | boolean | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "";
  }
  if (typeof value === "number") {
    return value.toLocaleString("ko-KR");
  }
  if (typeof value === "boolean") {
    return value ? "예" : "아니오";
  }
  return koLabel(koCode(value));
}

export function recommendationCopy(value: string | number | boolean | null | undefined) {
  const normalized = typeof value === "string" ? normalizeValue(applyTerms(value, RECOMMENDATION_TERMS)) : normalizeValue(value);
  return applyTerms(investorCopy(normalized), RECOMMENDATION_TERMS);
}

export function stockCopy(value: string | null | undefined) {
  const normalized = applyTerms(value ?? "", STOCK_TERMS);
  return applyTerms(investorCopy(koLabel(koCode(normalized))), STOCK_TERMS)
    .replaceAll("확인한다.", "확인합니다.")
    .replaceAll("확인해야 한다.", "확인이 필요합니다.")
    .replaceAll("분할 매수 후보 후보", "분할 매수 후보");
}

export function evidenceCopy(value: string | null | undefined) {
  const normalized = applyTerms(value ?? "", EVIDENCE_TERMS);
  return applyTerms(investorCopy(koLabel(koCode(normalized))), EVIDENCE_TERMS);
}

export function portfolioCopy(value: string | number | boolean | null | undefined) {
  if (typeof value === "string" && PORTFOLIO_CODES[value]) {
    return PORTFOLIO_CODES[value];
  }
  const normalized = typeof value === "string" ? applyTerms(value, PORTFOLIO_TERMS) : normalizeValue(value);
  const text = typeof normalized === "string" ? koLabel(koCode(normalized)) : normalized;
  return applyTerms(investorCopy(text), PORTFOLIO_TERMS)
    .replaceAll("확인 대상", "검토 후보")
    .replaceAll("확인 필요", "점검 필요")
    .replaceAll("확인한다", "표시합니다")
    .replaceAll("확인해야", "확인이 필요합니다");
}
