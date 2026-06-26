import type {
  ProfessionalAnalysisDepth,
  ProfessionalAnalysisNextAction,
  ProfessionalAnalysisQuality,
  ProfessionalRecommendationCoverageAudit,
  ProfessionalSourceGapPrioritization,
} from "./dataHealthTypes";

import { koCode } from "@/lib/korean-labels";

import { statusRiskClass } from "./dataHealthCopyModel";

export function professionalSourceGapTitle(gaps: ProfessionalSourceGapPrioritization) {
  if (gaps.status === "ok") {
    return "전문 분석 소스 정상";
  }
  if (!gaps.attention_required && gaps.source_blocker_count > 0) {
    return "원천 한계 관리 중";
  }
  if (gaps.status === "source_blockers_present") {
    return "원천 차단 종목 있음";
  }
  if (gaps.status === "high_priority_gaps") {
    return "우선 보강 소스 있음";
  }
  if (gaps.status === "fund_source_gaps") {
    return "펀드 분석 소스 보강 필요";
  }
  if (gaps.status === "fund_company_model_not_applicable") {
    return "펀드는 기업 재무 모델 제외";
  }
  if (gaps.status === "coverage_gaps_present") {
    return "분석 근거 누락 있음";
  }
  return koCode(gaps.status);
}

export function professionalSourceGapExplanation(gaps: ProfessionalSourceGapPrioritization) {
  if (gaps.status === "ok") {
    return "활성 추천 기준으로 핵심 재무·밸류에이션·리서치 원천 공백이 없다.";
  }
  if (!gaps.attention_required && gaps.source_blocker_count > 0) {
    return "원천 데이터가 부족한 종목은 남겨두되, 전문 판단과 가상 매매 검증 입력에서는 이미 차단했다. 새 정기 공시나 전용 parser가 생기면 다시 본다.";
  }
  if (gaps.status === "source_blockers_present") {
    return "SEC companyfacts나 원천 공시 연결이 막힌 종목이 있다. 합성 재무를 만들지 말고 원천 가능 여부부터 확인해야 합니다.";
  }
  if (gaps.status === "high_priority_gaps") {
    return "추천 또는 보유 노출이 있는 종목의 재무·피어·밸류에이션·리서치 근거가 비어 있다. 이 종목부터 보강한다.";
  }
  if (gaps.status === "fund_source_gaps") {
    return "ETF·펀드형 상품은 기업 재무제표가 아니라 보유종목, 비용, NAV, 추적차이 원천이 판단 근거다.";
  }
  if (gaps.status === "fund_company_model_not_applicable") {
    return "ETF·펀드형 상품은 기업 재무 모델 대상이 아니다. 별도 펀드 분석 근거로 본다.";
  }
  return "전문가식 분석에 필요한 원천 근거 중 일부가 비어 있어 추천 산식 검토 전 보강해야 한다.";
}

export function professionalSourceGapTone(gaps: ProfessionalSourceGapPrioritization) {
  if (!gaps.attention_required) {
    return "risk-low";
  }
  if (gaps.status === "ok" || gaps.status === "fund_company_model_not_applicable") {
    return "risk-low";
  }
  if (gaps.status === "coverage_gaps_present" || gaps.status === "fund_source_gaps") {
    return "risk-medium";
  }
  return "risk-high";
}

export function professionalNextActionTone(nextAction: ProfessionalAnalysisNextAction) {
  if (
    nextAction.status === "managed_outcome_wait"
    || nextAction.status === "professional_inputs_ready"
    || nextAction.status === "manual_weight_review_possible"
  ) {
    return "risk-low";
  }
  if (nextAction.status === "outcome_or_weight_review_blocked") {
    return "risk-medium";
  }
  return "risk-high";
}

export function professionalQualityTone(quality: ProfessionalAnalysisQuality) {
  if (
    quality.status === "ready_waiting_outcome"
    || quality.status === "ready_for_manual_review"
    || quality.status === "managed_source_limited"
  ) {
    return "risk-low";
  }
  if (quality.status === "coverage_gaps_present") {
    return "risk-medium";
  }
  return "risk-high";
}

export function professionalRecommendationAuditTone(audit: ProfessionalRecommendationCoverageAudit) {
  if (audit.status === "ready_for_review") {
    return "risk-low";
  }
  if (audit.status === "paper_validation_pending" || audit.status === "coverage_gaps_present") {
    return "risk-medium";
  }
  return "risk-high";
}

export function professionalDepthTitle(depth: ProfessionalAnalysisDepth) {
  if (depth.status === "complete") {
    return "전문 분석 근거 충족";
  }
  if (depth.status === "mostly_covered") {
    return "대부분 갖춰짐";
  }
  if (depth.status === "source_limited") {
    return "원천 한계 포함";
  }
  if (depth.status === "coverage_gaps_present") {
    return "분석 근거 보강 필요";
  }
  if (depth.status === "missing_active_candidates") {
    return "활성 후보 없음";
  }
  return koCode(depth.status);
}

export function professionalDepthTone(depth: ProfessionalAnalysisDepth) {
  if (depth.status === "complete" || depth.status === "mostly_covered") {
    return "risk-low";
  }
  if (depth.status === "source_limited") {
    return "risk-medium";
  }
  return "risk-high";
}

export function professionalDepthStatusLabel(status: string) {
  if (status === "complete") {
    return "완비";
  }
  if (status === "mostly_covered") {
    return "대부분 완비";
  }
  if (status === "source_blocked") {
    return "원천 차단";
  }
  if (status === "partial") {
    return "일부 부족";
  }
  if (status === "fund_source_ready") {
    return "펀드 근거 준비";
  }
  return koCode(status);
}

export function professionalDepthItemTone(status: string) {
  if (status === "complete" || status === "fund_source_ready") {
    return "risk-low";
  }
  if (status === "mostly_covered" || status === "partial") {
    return "risk-medium";
  }
  return "risk-high";
}

export function professionalRecommendationAuditItemTone(status: string) {
  if (status === "ready_for_review") {
    return "risk-low";
  }
  if (status === "paper_validation_pending" || status === "coverage_gap") {
    return "risk-medium";
  }
  return "risk-high";
}
