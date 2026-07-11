import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { StockDetailData } from "@/lib/types";

import { StockProfessionalSourceGuardrailPanel } from "./StockProfessionalSourceGuardrailPanel";

const fundGuardrail = {
  automatic_order_allowed: false,
  blocked: false,
  blocker_code: "fund_company_financial_model_not_applicable",
  blocker_label: "ETF는 회사 재무제표 모델 대상이 아님",
  broker_submit_allowed: false,
  next_action: "보유 구성과 추적 품질을 확인한다.",
  order_boundary: "read_only_no_order",
  paper_validation_input_allowed: true,
  professional_decision_use_allowed: true,
  score_policy: "recommendation_weights_unchanged",
  source_data_blocker: null,
  status: "fund_or_etf_company_model_not_applicable",
  summary: "ETF는 회사 재무제표 대신 보유 구성으로 판단한다.",
} satisfies StockDetailData["professional_source_guardrail"];

describe("StockProfessionalSourceGuardrailPanel", () => {
  it("keeps the fund boundary concise in the status rail and detailed below it", () => {
    render(<StockProfessionalSourceGuardrailPanel guardrail={fundGuardrail} symbol="SPY" />);

    expect(screen.getByText("회사 재무모델 비대상")).toBeInTheDocument();
    expect(screen.getByText("개별 기업 재무제표 대신 보유 구성으로 판단")).toBeInTheDocument();
  });
});
