import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RecommendationProfessionalAuditPanel } from "./recommendation-professional-audit-panel";
import {
  auditCopy,
  auditLayerDetailCopy,
  professionalAuditStatusLabel,
  professionalAuditSummary,
  type ProfessionalAuditTone,
} from "./recommendation-professional-audit-model";
import type { ProfessionalEvidenceAudit } from "../lib/types";

const audit: ProfessionalEvidenceAudit = {
  as_of_date: "2026-06-24",
  automatic_order_allowed: false,
  automatic_weight_change_allowed: false,
  available_layer_count: 5,
  blocked_evidence_gate_count: 1,
  blocked_layer_count: 1,
  broker_submit_allowed: false,
  coverage_ratio: 0.72,
  evidence_quality_status: "source_limited",
  expected_layer_count: 8,
  holding_review_status: "pending",
  layer_checks: [
    {
      detail: "정기 재무제표 원천이 없어 전문 판단 입력에서 차단한다.",
      href: "/stocks/EROK",
      key: "financial_model",
      label: "financial statement model",
      source: "SEC companyfacts",
      status: "blocked",
    },
    {
      detail: "상위 흐름과 뉴스 근거는 연결되어 있다.",
      href: "/ai-evidence/results",
      key: "news_evidence",
      label: "news evidence",
      source: "AI evidence",
      status: "complete",
    },
  ],
  missing_layer_count: 2,
  missing_layer_labels: ["valuation", "peer comparison"],
  missing_layers: ["valuation", "peer_comparison"],
  next_action: "standard periodic filing이 들어오기 전까지 전문 판단 입력에서 제외한다.",
  order_boundary: "read_only_no_order",
  paper_validation_input_allowed: false,
  paper_validation_status: "blocked_source",
  partial_layer_count: 1,
  pending_layer_count: 2,
  product_type: "operating_company",
  professional_decision_status: "blocked",
  recommendation: "watch",
  recommendation_id: "recommendation-67",
  recommendation_scoring_mutated: false,
  score: 0.42,
  score_policy: "automatic weight change is blocked until outcome maturity.",
  source_blocker: {
    blocked: true,
    blocker_code: "sec_companyfacts_missing_us_gaap_facts",
    blocker_label: "SEC 표준 재무 원천 부족",
    next_action: "정기 재무제표가 공시될 때까지 대기한다.",
    source_run_id: "run-1",
    summary: "companyfacts에 us-gaap 재무 항목이 없다.",
  },
  status: "source_blocked",
  summary: "전문 분석 원천이 부족해 추천을 기록으로만 보존한다.",
  symbol: "EROK",
  title: "전문 원천 차단 추천",
  warning_evidence_gate_count: 2,
};

describe("RecommendationProfessionalAuditPanel", () => {
  it("summarizes professional audit status before layer details", () => {
    render(<RecommendationProfessionalAuditPanel audit={audit} />);

    expect(screen.getByRole("heading", { name: "전문 원천 차단 추천" })).toBeInTheDocument();
    expect(screen.getByText("전문 원천 차단")).toBeInTheDocument();
    expect(screen.getByText("72.0%")).toBeInTheDocument();
    expect(screen.getByText("읽기 전용, 실거래 주문 차단")).toBeInTheDocument();
    expect(screen.getByText("SEC 표준 재무 원천 부족")).toBeInTheDocument();
    expect(screen.getByText("밸류에이션")).toBeInTheDocument();
    expect(screen.getByText("성과 표본이 충분해질 때까지 추천 비중 변경은 금지됩니다.")).toBeInTheDocument();
    expect(screen.queryByText(/automatic/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/source_limited/i)).not.toBeInTheDocument();

    const layerDetails = screen.getByText("전문 분석 레이어 자세히 보기").closest("details");
    const policyDetails = screen.getByText("추천 산식과 주문 경계 확인").closest("details");
    expect(layerDetails?.hasAttribute("open")).toBe(false);
    expect(policyDetails?.hasAttribute("open")).toBe(false);
  });

  it("keeps deterministic professional audit summary counts", () => {
    expect(professionalAuditSummary(audit)).toEqual({
      blockedOrPendingCount: 3,
      isSourceBlocked: true,
      tone: "blocked" satisfies ProfessionalAuditTone,
    });
  });

  it("translates common source phrases into investor-facing Korean", () => {
    expect(professionalAuditStatusLabel("paper_validation_pending")).toBe("가상 매매 검증 대기");
    expect(auditCopy("성과 측정 윈도우가 끝날 때까지 반영 비중 변경을 금지한다.")).toBe(
      "성과 측정 기간이 끝날 때까지 추천 비중 변경을 금지한다.",
    );
    expect(auditCopy("Gross Expense Ratio and tracking difference")).toBe("총 보수율 및 추적 차이");
    expect(auditLayerDetailCopy("news evidence", "Stock market today: Dow futures fall")).toBe(
      "뉴스 근거가 연결되어 있습니다. 원천 뉴스와 AI 해석은 관련 화면에서 확인합니다.",
    );
    expect(auditLayerDetailCopy("뉴스·투자 근거", "Stock market today: Dow futures fall")).toBe(
      "뉴스 근거가 연결되어 있습니다. 원천 뉴스와 AI 해석은 관련 화면에서 확인합니다.",
    );
  });
});
