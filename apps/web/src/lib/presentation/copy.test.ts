import { describe, expect, it } from "vitest";

import { investorCopy } from "./copy";

describe("investorCopy", () => {
  it("removes internal execution terminology from investor text", () => {
    expect(investorCopy("pipeline-run-42 runner artifact fallback")).toBe(
      "최근 작업 기록 실행 기록 결과 기록 보조 경로",
    );
  });

  it("uses a neutral fallback for missing text", () => {
    expect(investorCopy(null)).toBe("정보 없음");
  });

  it("translates known decision and coverage codes", () => {
    expect(investorCopy("monitor_or_accumulate")).toBe("관찰 또는 분할 매수");
    expect(investorCopy("needs_thesis_review")).toBe("투자 논리 보강 필요");
    expect(investorCopy("coverage status missing_thesis")).toBe("투자 논리 연결 누락");
    expect(investorCopy("covered thesis and outcome remain valid")).toBe(
      "투자 논리와 성과 측정이 유효합니다.",
    );
  });
});
