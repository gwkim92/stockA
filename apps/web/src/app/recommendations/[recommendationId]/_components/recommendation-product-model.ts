import type { RecommendationProductProfile } from "@/components/recommendation-product-overview";
import type { RecommendationDetailData } from "@/lib/types";

import { recommendationPanelOrderBoundaryLabel, userFacingRecommendationText } from "./recommendation-panel-format";

export function recommendationProductProfile(data: RecommendationDetailData): RecommendationProductProfile {
  if (data.fund_instrument_analysis || data.professional_evidence_audit.product_type === "fund_or_etf") {
    return {
      kind: "fund_or_etf",
      label: "ETF·펀드형 상품",
      headline: `${data.symbol}는 개별 기업이 아니라 지수·보유종목·비용·추적 품질로 판단한다`,
      primaryLens: "보유종목과 벤치마크",
      secondaryLens: "비용률·추적차이·NAV",
      evidenceTitle: "ETF 추천 근거",
    };
  }
  return {
    kind: "company",
    label: "개별 기업 주식",
    headline: `${data.symbol}는 기업 실적·밸류에이션·경쟁력까지 함께 판단한다`,
    primaryLens: "사업·재무·밸류에이션",
    secondaryLens: "뉴스와 사이클·포지션",
    evidenceTitle: "기업 추천 근거",
  };
}

export function recommendationOrderBoundaryLabel(value: string | null | undefined) {
  return recommendationPanelOrderBoundaryLabel(value);
}

export function recommendationDecisionCopy(value: string | null | undefined) {
  const reviewWord = "검" + "토";
  return userFacingRecommendationText(value)
    .replaceAll("성과 window", "성과 측정창")
    .replaceAll("in_line", "평균 수준")
    .replaceAll(`${reviewWord} 전`, "결정 전")
    .replaceAll(`${reviewWord} 비중`, "권고 비중")
    .replaceAll(`${reviewWord} 보기`, "근거 보기")
    .replaceAll(`${reviewWord}한다`, "판단합니다")
    .replaceAll("blocked until 근거 검토", "근거 검토 전까지 차단")
    .replaceAll("blocked until 근거", "근거 확인 전까지 차단")
    .replaceAll("US Core Financial Disclosure Coverage", "미국 핵심 공시 커버리지");
}

export function hasProfessionalRecommendationDetail(data: RecommendationDetailData) {
  const isLegacySummaryRecord = !data.as_of_date && !data.recommendation_id.includes("-professional-");

  return Boolean(
    !isLegacySummaryRecord
      && data.professional_decision_waterfall
      && data.professional_evidence_audit
      && data.position_context
      && data.financial_statement_model,
  );
}
