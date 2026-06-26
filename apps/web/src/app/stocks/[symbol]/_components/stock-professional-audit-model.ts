import type { StockDetailData } from "@/lib/types";

import type { StockProfessionalLayer, StockProfessionalLayerStatus } from "./stock-professional-layer-model";
import { stockSourceLabel } from "./stock-detail-panel-format";

export type StockProfessionalAuditCounts = {
  readonly completeCount: number;
  readonly partialCount: number;
  readonly pendingCount: number;
  readonly blockedCount: number;
  readonly missingLayers: readonly StockProfessionalLayer[];
  readonly applicableLayers: readonly StockProfessionalLayer[];
  readonly coverageRatio: number;
};

export function stockProfessionalLayerStatusLabel(status: StockProfessionalLayerStatus) {
  const labels: Record<StockProfessionalLayerStatus, string> = {
    complete: "완료",
    partial: "일부",
    pending: "대기",
    blocked: "차단",
    missing: "근거 없음",
    not_applicable: "비적용",
  };
  return labels[status];
}

export function stockProfessionalLayerTone(status: StockProfessionalLayerStatus) {
  if (status === "complete" || status === "not_applicable") {
    return "risk-low";
  }
  if (status === "blocked") {
    return "risk-high";
  }
  return "risk-medium";
}

export function stockProfessionalAuditStatus(counts: Pick<StockProfessionalAuditCounts, "blockedCount" | "missingLayers" | "pendingCount">) {
  if (counts.blockedCount > 0) {
    return {
      tone: "risk-high",
      title: "전문 판단 입력 차단",
      summary: "차단된 원천 근거가 있어 종목 분석을 투자 판단이나 가상 매매 입력으로 넘기면 안 된다.",
    };
  }
  if (counts.missingLayers.length > 0) {
    return {
      tone: "risk-medium",
      title: "근거 보강 필요",
      summary: "중장기 판단에 필요한 전문 근거가 일부 빠져 있다. 추천이나 보유 판단 전에 빠진 레이어가 먼저다.",
    };
  }
  if (counts.pendingCount > 0) {
    return {
      tone: "risk-medium",
      title: "성과 검증 대기",
      summary: "핵심 근거는 연결됐지만 성과 측정창이나 가상 매매 검증 상태가 아직 끝나지 않았다.",
    };
  }
  return {
    tone: "risk-low",
    title: "전문 근거 연결",
    summary: "전문 분석 레이어가 연결됐다. 읽기 전용 상태이며 산식 변경과 실거래 주문은 하지 않는다.",
  };
}

export function professionalGuardrailTone(guardrail: StockDetailData["professional_source_guardrail"]) {
  if (guardrail.blocked) {
    return "risk-high";
  }
  if (!guardrail.paper_validation_input_allowed || !guardrail.professional_decision_use_allowed) {
    return "risk-medium";
  }
  return "risk-low";
}

export function professionalGuardrailTitle(guardrail: StockDetailData["professional_source_guardrail"]) {
  if (guardrail.blocked) {
    return "투자 판단 입력 차단";
  }
  if (guardrail.status === "fund_or_etf_company_model_not_applicable") {
    return "ETF·펀드 경계 적용";
  }
  return "투자 판단 입력 가능";
}

export function orderBoundaryLabel(value: string | null | undefined) {
  if (value === "read_only_no_order") {
    return "읽기 전용, 주문 차단";
  }
  return stockSourceLabel(value);
}

export function stockProfessionalAuditCounts(layers: readonly StockProfessionalLayer[]): StockProfessionalAuditCounts {
  const applicableLayers = layers.filter((layer) => layer.status !== "not_applicable");
  const completeCount = applicableLayers.filter((layer) => layer.status === "complete").length;
  const partialCount = applicableLayers.filter((layer) => layer.status === "partial").length;
  const pendingCount = applicableLayers.filter((layer) => layer.status === "pending").length;
  const blockedCount = applicableLayers.filter((layer) => layer.status === "blocked").length;
  const missingLayers = applicableLayers.filter((layer) => layer.status === "missing");
  const coverageRatio =
    applicableLayers.length > 0 ? (completeCount + partialCount * 0.5) / applicableLayers.length : 1;
  return {
    applicableLayers,
    completeCount,
    partialCount,
    pendingCount,
    blockedCount,
    missingLayers,
    coverageRatio,
  };
}
