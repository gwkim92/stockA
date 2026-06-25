import { koCode, koLabel } from "../lib/korean-labels";
import { recommendationCopy } from "../lib/presentation";
import type { ProfessionalEvidenceAudit } from "../lib/types";

export type ProfessionalAuditTone = "ready" | "watch" | "blocked";
export type ProfessionalAuditRiskClass = "risk-low" | "risk-medium" | "risk-high";

const AUDIT_COPY_LABELS: Readonly<Record<string, string>> = {
  "AI evidence": "AI 투자 근거",
  "SEC companyfacts": "SEC 표준 재무 원천",
  "financial statement model": "재무제표 모델",
  "news evidence": "뉴스 근거",
  "peer comparison": "피어 비교",
  "automatic weight change is blocked until outcome maturity.": "성과 표본이 충분해질 때까지 추천 비중 변경은 금지됩니다.",
  paper_validation_pending: "가상 매매 검증 대기",
  pending: "대기",
  source_limited: "원천 한계 관리",
  valuation: "밸류에이션",
};

const HANGUL_PATTERN = /[가-힣]/;

export function auditCopy(value: string | number | boolean | null | undefined): string {
  if (typeof value === "string" && AUDIT_COPY_LABELS[value]) {
    return AUDIT_COPY_LABELS[value];
  }
  const translated = recommendationCopy(value);
  const reviewWord = koLabel("review");
  return translated
    .replaceAll("automatic", "자동")
    .replaceAll("source limited", "원천 한계 관리")
    .replaceAll("outcome", "성과")
    .replaceAll("review", reviewWord)
    .replaceAll(`${reviewWord} status`, `${reviewWord} 상태`)
    .replaceAll(`${reviewWord} 전`, "결정 전")
    .replaceAll("weight change", "비중 변경")
    .replaceAll("반영 비중 change", "비중 변경")
    .replaceAll("반영 비중 변경", "추천 비중 변경")
    .replaceAll("추천 추천 비중", "추천 비중")
    .replaceAll("성과 측정 윈도우가", "성과 측정 기간이")
    .replaceAll("성과 측정 윈도우", "성과 측정 기간")
    .replaceAll("periodic filing", "정기 공시")
    .replaceAll("standard 정기 공시", "표준 정기 공시")
    .replaceAll("companyfacts", "SEC 표준 재무 데이터")
    .replaceAll("us-gaap", "US-GAAP")
    .replaceAll("stack and macro flow", "사이클 스택과 상위 흐름")
    .replaceAll("사이클 사이클 스택", "사이클 스택")
    .replaceAll("equity research", "AI 리서치")
    .replaceAll("fund source layer", "펀드 원천 근거")
    .replaceAll("Gross Expense Ratio", "총 보수율")
    .replaceAll("총 보수율를", "총 보수율을")
    .replaceAll("tracking difference", "추적 차이")
    .replaceAll("기업 peer", "기업 피어")
    .replaceAll(" and ", " 및 ")
    .replaceAll(`${reviewWord} 보기`, "근거 보기")
    .replaceAll(`${reviewWord}한다`, "판단합니다")
    .replaceAll("US Core Financial Disclosure Coverage", "미국 핵심 공시 커버리지");
}

export function auditLayerDetailCopy(layerLabel: string, detail: string): string {
  if ((layerLabel === "news evidence" || detail.length > 32) && !HANGUL_PATTERN.test(detail)) {
    return "뉴스 근거가 연결되어 있습니다. 원천 뉴스와 AI 해석은 관련 화면에서 확인합니다.";
  }
  return auditCopy(detail);
}

export function professionalAuditTone(audit: ProfessionalEvidenceAudit): ProfessionalAuditTone {
  if (audit.status === "source_blocked" || audit.blocked_layer_count > 0) {
    return "blocked";
  }
  if (audit.status === "ready_for_review") {
    return "ready";
  }
  return "watch";
}

export function professionalAuditRiskClass(audit: ProfessionalEvidenceAudit): ProfessionalAuditRiskClass {
  const tone = professionalAuditTone(audit);
  if (tone === "blocked") {
    return "risk-high";
  }
  if (tone === "ready") {
    return "risk-low";
  }
  return "risk-medium";
}

export function professionalAuditStatusLabel(status: string): string {
  const labels: Readonly<Record<string, string>> = {
    ready_for_review: "전문 근거 확인",
    source_blocked: "전문 원천 차단",
    source_limited: "원천 한계 관리",
    pending: "검토 대기",
  };
  return labels[status] ?? auditCopy(status);
}

export function professionalLayerTone(status: string): ProfessionalAuditTone {
  if (status === "complete") {
    return "ready";
  }
  if (status === "blocked") {
    return "blocked";
  }
  return "watch";
}

export function professionalLayerStatusLabel(status: string): string {
  const labels: Readonly<Record<string, string>> = {
    complete: "확인됨",
    partial: "일부 확인",
    missing: "부족",
    blocked: "차단",
    pending: "대기",
    not_applicable: "비적용",
  };
  return labels[status] ?? koCode(status);
}

export function professionalProductLabel(productType: string): string {
  if (productType === "fund_or_etf") {
    return "ETF·펀드형";
  }
  return "일반 기업";
}

export function orderBoundaryLabel(value: string | null | undefined): string {
  if (!value) {
    return "실거래 상태 미기록";
  }
  if (value === "read_only_no_order") {
    return "읽기 전용, 실거래 주문 차단";
  }
  return auditCopy(value);
}

export function professionalAuditSummary(audit: ProfessionalEvidenceAudit) {
  return {
    blockedOrPendingCount: audit.blocked_layer_count + audit.pending_layer_count,
    isSourceBlocked: audit.source_blocker.blocked,
    tone: professionalAuditTone(audit),
  };
}
