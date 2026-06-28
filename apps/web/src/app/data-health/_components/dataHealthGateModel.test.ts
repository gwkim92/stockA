import { describe, expect, it } from "vitest";

import type { OpenGateDetail } from "./dataHealthTypes";
import { buildGateTriageBuckets, gateTriageKey, gateTriageSummary } from "./dataHealthGateModel";

function gate(category: string, summary: string): OpenGateDetail {
  return {
    gate_id: "recommendation_outcome_maturity_attention",
    label: "추천 성과 측정창",
    category,
    category_label: "성과 실행 필요",
    severity: "medium",
    status_label: "성과 보정 실행 필요",
    summary,
    next_action: "성과 산출과 calibration을 지금 실행한다.",
    order_boundary: "read_only_no_order",
    automatic_action_allowed: false,
  };
}

describe("gateTriageKey", () => {
  it("routes due outcome work separately from managed waits", () => {
    expect(gateTriageKey(gate("outcome_due", "성과 산출 가능 후보가 있다."))).toBe("due-now");
    expect(gateTriageKey(gate("outcome_wait", "성과 측정일까지 기다린다."))).toBe("managed-wait");
  });
});

describe("gateTriageSummary", () => {
  it("prioritizes due outcome work after hard operational blockers", () => {
    const buckets = buildGateTriageBuckets([gate("outcome_due", "성과 산출 가능 후보가 있다.")]);

    expect(gateTriageSummary(buckets, 1)).toContain("성과 실행");
  });
});
