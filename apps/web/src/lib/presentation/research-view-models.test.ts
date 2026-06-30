import { describe, expect, it } from "vitest";

import {
  brokerDataUseLabel,
  brokerOrderBoundaryLabel,
  formatBasisPointDiff,
  paperTradingStateLabel,
  recommendationExecutionStatus,
  recommendationProductLabel,
  stockProductLabel,
} from "./index";

describe("professional investment view models", () => {
  it("separates company and ETF/fund product labels", () => {
    expect(recommendationProductLabel("company_stock")).toBe("개별 회사 주식");
    expect(recommendationProductLabel("fund_or_etf")).toBe("ETF·펀드");
    expect(stockProductLabel("company_stock")).toBe("개별 회사 주식");
    expect(stockProductLabel("fund_or_etf")).toBe("ETF·펀드");
  });

  it("keeps broker execution blocked unless the backend explicitly allows it", () => {
    expect(
      recommendationExecutionStatus({
        broker_submit_allowed: false,
        paper_validation_input_allowed: false,
      }),
    ).toEqual({
      statusLabel: "실행 차단",
      statusTone: "blocked",
      nextAction: "차단 사유와 부족한 근거를 해소하기 전에는 주문 후보로 보지 않습니다.",
    });
  });

  it("distinguishes paper trading states from system failures", () => {
    expect(paperTradingStateLabel("execution_ready")).toEqual({ label: "가상 검증 가능", tone: "ready" });
    expect(paperTradingStateLabel("safety_blocked")).toEqual({ label: "안전장치 차단", tone: "blocked" });
    expect(paperTradingStateLabel("data_limited")).toEqual({ label: "데이터 부족", tone: "source_limited" });
    expect(paperTradingStateLabel("approval_required")).toEqual({ label: "승인 필요", tone: "watch" });
    expect(paperTradingStateLabel("live_trading_disabled")).toEqual({ label: "실거래 비활성", tone: "blocked" });
  });

  it("uses one broker reality vocabulary across investor pages", () => {
    expect(
      brokerDataUseLabel({
        used_for_account: true,
        used_for_execution: false,
        used_for_scoring: false,
      }),
    ).toBe("계좌 검증");
    expect(brokerOrderBoundaryLabel("read_only_no_order")).toBe("읽기 전용, 실거래 주문 차단");
    expect(formatBasisPointDiff(0.123456)).toBe("0.123bp");
    expect(formatBasisPointDiff(null)).toBe("미측정");
  });
});
