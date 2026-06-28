import { render, screen } from "@testing-library/react";
import type { Route } from "next";
import { describe, expect, it } from "vitest";

import type { InvestmentViewModel } from "@/lib/presentation";

import { StockResearchHeader } from "./StockResearchHeader";

const viewModel: InvestmentViewModel = {
  investmentImpact: "사업, 재무, 밸류에이션, 피어, 뉴스, 사이클, thesis를 한 화면에 정리합니다.",
  metrics: [],
  nextAction: "연결된 추천 상세에서 실행 차단 사유와 가상 검증 상태를 확인합니다.",
  sourceLimitReason: "분석 기준 데이터와 브로커 참고 데이터의 역할을 분리해 표시합니다.",
  statusLabel: "추천 근거 있음",
  statusTone: "ready",
  summary: "AAPL · 상승 · 보유 중",
  title: "AAPL 개별 회사 주식 리서치",
};

describe("StockResearchHeader", () => {
  it("shows analysis price state and Toss broker reality without raw provider wording", () => {
    render(
      <StockResearchHeader
        asOfDate="2026-06-25"
        counts={{
          directNewsCount: 2,
          financialMetricCount: 18,
          fundHoldingCount: null,
          macroFlowCount: 3,
          marketCorrelationCount: 4,
          stockNewsCount: 5,
        }}
        linkedThesisHref={"/theses/thesis-1" as Route}
        marketCode="NASDAQ"
        name="Apple Inc."
        position={{
          averageCostLabel: "$180.00",
          quantityLabel: "수량 10",
          statusLabel: "보유 중",
          unrealizedPnlLabel: "$120.00 · 6.5%",
        }}
        price={{
          analysisStatusLabel: "사용 가능",
          brokerContextLabel: "계좌·보유·가상 매매 검증 참고, 추천 점수 미반영",
          brokerStatusLabel: "토스증권 기준 수집됨",
          changePct: 0.012,
          priceLabel: "$192.00",
          priceSourceLabel: "분석 기준 가격 · Twelve Data",
        }}
        productKind="company_stock"
        recommendation={{
          context: "점수 68% · 활성",
          href: "/recommendations/recommendation-1" as Route,
          label: "분할 매수 후보",
        }}
        sourceBlocked={false}
        symbol="AAPL"
        viewModel={viewModel}
      />,
    );

    expect(screen.getByRole("heading", { name: "AAPL 종목 분석서" })).toBeInTheDocument();
    expect(screen.getByText("분석 기준 가격 상태")).toBeInTheDocument();
    expect(screen.getByText("토스증권 브로커 현실")).toBeInTheDocument();
    expect(screen.getByText("토스증권 기준 수집됨")).toBeInTheDocument();
    expect(screen.getByText(/추천 점수 미반영/)).toBeInTheDocument();
    expect(screen.queryByText(/canonical|shadow|broker_submit_allowed|pipeline|runner|artifact/i)).not.toBeInTheDocument();
  });
});
