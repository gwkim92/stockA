import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { InvestmentViewModel } from "@/lib/presentation";

import { RecommendationDecisionHeader } from "./RecommendationDecisionHeader";
import { RecommendationMarketCorrelationsPanel } from "./RecommendationMarketCorrelationsPanel";

const viewModel: InvestmentViewModel = {
  title: "AAPL 추천",
  summary: "추천 판단 요약",
  statusLabel: "근거 보강 대기",
  statusTone: "watch",
  investmentImpact: "가격과 재무 근거를 함께 봅니다.",
  nextAction: "근거 공백을 확인합니다.",
  sourceLimitReason: "원천 제한 없음",
  metrics: [],
};

describe("recommendation decision copy", () => {
  it("keeps news evidence and deterministic cycle evidence distinct", () => {
    render(
      <RecommendationDecisionHeader
        asOfDate="2026-07-11"
        counts={{
          blockedStepCount: 0,
          financialMetricCount: 5,
          fundHoldingCount: null,
          marketCorrelationCount: 2,
          readyStepCount: 5,
          totalStepCount: 6,
          watchStepCount: 1,
        }}
        execution={{
          brokerSubmitAllowed: false,
          orderStatusLabel: "읽기 전용, 실거래 주문 차단",
          paperValidationAllowed: false,
        }}
        horizonLabel="장기"
        positionStatusLabel="미보유"
        productKind="company_stock"
        recommendationLabel="관찰"
        symbol="AAPL"
        viewModel={viewModel}
      />,
    );

    expect(
      screen.getByText("재무, 밸류에이션, 산업 위치를 뉴스와 사이클 근거와 분리한다."),
    ).toBeInTheDocument();
  });

  it("uses complete Korean sentences for market-correlation guidance", () => {
    render(<RecommendationMarketCorrelationsPanel correlations={[]} symbol="AAPL" />);

    expect(
      screen.getByText(
        "이 영역은 추천 점수를 바꾸지 않습니다. 최근 수익률 동조성으로 포트폴리오 집중도, 헤지 필요성, 동행 위험을 점검합니다. 상관관계만으로 원인을 확정하지 않습니다.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("아직 이 추천 종목의 시장 동조성이 계산되지 않았습니다. 계산 후 추천 리스크 점검에 활용합니다."),
    ).toBeInTheDocument();
  });
});
