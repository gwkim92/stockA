import { describe, expect, it } from "vitest";
import { runStateLabel, runQualityExplanation } from "./dataHealthRunModel";
import { statusRiskClass } from "./dataHealthCopyModel";
import type { PipelineRun } from "./dataHealthTypes";

describe("scheduled collection waiting", () => {
  it("explains a completed schedule without claiming a current data timestamp", () => {
    const run = { latest_status: "succeeded", health_status: "scheduled_wait" } as PipelineRun;
    expect(runStateLabel(run)).toContain("다음 일정 대기");
    expect(runQualityExplanation(run)).toContain("완료 시각");
    expect(statusRiskClass(run.health_status)).toBe("risk-low");
  });
  it("preserves visible stale and failed states", () => {
    expect(statusRiskClass("stale")).toBe("risk-medium");
    expect(statusRiskClass("failed")).toBe("risk-high");
    expect(runStateLabel({latest_status:"failed",health_status:"failed"} as PipelineRun)).not.toContain("대기");
  });
});
