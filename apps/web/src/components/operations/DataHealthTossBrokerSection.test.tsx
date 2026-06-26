import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DataHealthTossBrokerSection } from "./DataHealthTossBrokerSection";

describe("DataHealthTossBrokerSection", () => {
  it("keeps Toss data framed as broker reality without opening live orders", () => {
    render(
      <DataHealthTossBrokerSection
        cadenceCountLabel="4개"
        candleCountLabel="300개"
        comparisonLookbackLabel="20거래일 · 허용 25bps"
        comparisonStatusLabel="검증 중"
        orderBoundaryLabel="주문 차단"
        orderSubmitLabel="증권사 주문 제출 차단"
        requestedSymbolCountLabel="10개"
        syncStatusLabel="성공"
        syncStatusTone="risk-low"
        title="토스증권 데이터 수집 중"
      />,
    );

    expect(screen.getByRole("heading", { name: "토스증권 데이터 수집 중" })).toBeInTheDocument();
    expect(screen.getByText("토스증권 브로커 데이터")).toBeInTheDocument();
    expect(screen.getByText(/브로커 현실 데이터/)).toBeInTheDocument();
    expect(screen.getByText("증권사 주문 제출 차단")).toBeInTheDocument();
    expect(screen.queryByText(/canonical|shadow|broker_submit_allowed/i)).not.toBeInTheDocument();
  });
});
