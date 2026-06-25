import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  RecommendationScoreAuditPanel,
} from "./recommendation-score-audit-panel";
import { scoreAuditSummary, type RecommendationScoreAuditData } from "./recommendation-score-audit-model";

const auditData: RecommendationScoreAuditData = {
  linked_thesis_id: "thesis-11",
  outcome: {
    absolute_return: 0,
    alpha: 0,
    benchmark_return: 0,
    label: "unmeasured",
    measurement_end_date: "",
  },
  score: 0.615,
  score_components: [
    {
      component: "macro_flow_score",
      evidence_id: "macro-flow-spy-2026-06-24",
      value: 0.111,
      weight: 0.1,
    },
    {
      component: "valuation_margin_score",
      evidence_id: "fundamental-spy-2026-06-24",
      value: 0.5,
      weight: 0,
    },
  ],
  symbol: "SPY",
};

describe("RecommendationScoreAuditPanel", () => {
  it("summarizes active and explanatory score inputs before detailed provenance", () => {
    render(<RecommendationScoreAuditPanel data={auditData} />);

    expect(screen.getByRole("heading", { name: "점수는 먼저 요약하고, 세부 근거는 필요할 때만 펼쳐본다" })).toBeInTheDocument();
    expect(screen.getByText("61.5%")).toBeInTheDocument();
    expect(screen.getByText("2개")).toBeInTheDocument();
    expect(screen.getByText("1개")).toBeInTheDocument();
    expect(screen.getByText("판단 보조 1개")).toBeInTheDocument();
    expect(screen.getAllByText("측정 전").length).toBeGreaterThan(0);

    const detailToggle = screen.getByText("점수 항목 자세히 보기").closest("details");
    expect(detailToggle).not.toBeNull();
    expect(detailToggle?.hasAttribute("open")).toBe(false);
  });

  it("keeps active score counts deterministic for the route summary", () => {
    expect(scoreAuditSummary(auditData)).toEqual({
      activeComponents: 1,
      explanatoryComponents: 1,
      measured: false,
      totalComponents: 2,
    });
  });
});
