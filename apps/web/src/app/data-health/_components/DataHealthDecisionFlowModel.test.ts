import { describe, expect, it } from "vitest";

import {
  buildDataHealthDataGapCards,
  buildDataHealthDecisionFlowCards,
  type DataHealthDecisionFlowModelInput,
} from "./DataHealthDecisionFlowModel";

const baseDecisionInput: DataHealthDecisionFlowModelInput = {
  aiAttentionRequired: false,
  aiInvocationLabel: "정상",
  crossAssetHealthOk: true,
  crossAssetIndicatorRunLabel: "성공",
  crossAssetRunLabel: "성공",
  dataQualityReady: true,
  decisionRunLabel: "성공",
  latestPriceDateLabel: "2026-06-25",
  manualWeightReviewAllowed: false,
  marketPriceRunLabel: "성공",
  newsRunLabel: "성공",
  nextRecommendationDueDateLabel: "2026-07-01",
  outcomeWeightReviewBlocked: true,
  priceAttentionRequired: false,
  recommendationOutcomeRunLabel: "대기",
  remediationRunLabel: "성공",
  safeInvestmentBoundary: true,
  tossAttentionRequired: false,
  tossBrokerSubmitAllowed: false,
  tossComparisonLabel: "검증 중",
  tossSyncLabel: "성공",
};

describe("DataHealthDecisionFlowModel", () => {
  it("maps real decision-flow inputs into user-facing cards", () => {
    const cards = buildDataHealthDecisionFlowCards(baseDecisionInput);

    expect(cards).toHaveLength(6);
    expect(cards[0]).toMatchObject({
      label: "01 뉴스·AI",
      title: "뉴스 근거 사용 가능",
      tone: "ready",
    });
    expect(cards[1]).toMatchObject({
      title: "분석 가격 최신",
      statusLabel: "성공 · 최신 가격일 2026-06-25",
      tone: "ready",
    });
    expect(cards[5]).toMatchObject({
      title: "성과 표본 대기",
      impact: "반영 비중 변경 금지",
      tone: "watch",
    });
    expect(JSON.stringify(cards)).not.toMatch(/pipeline|runner|artifact|fallback|canonical|shadow|raw_/i);
  });

  it("turns AI, price, and investment boundary failures into blocking cards", () => {
    const cards = buildDataHealthDecisionFlowCards({
      ...baseDecisionInput,
      aiAttentionRequired: true,
      dataQualityReady: false,
      priceAttentionRequired: true,
      safeInvestmentBoundary: false,
    });

    expect(cards.find((card) => card.label === "01 뉴스·AI")?.tone).toBe("block");
    expect(cards.find((card) => card.label === "02 시장 가격")?.tone).toBe("block");
    expect(cards.find((card) => card.label === "05 추천·보유")?.tone).toBe("block");
  });

  it("classifies data gaps by current policy without changing scoring", () => {
    const cards = buildDataHealthDataGapCards({
      crossAssetHealthOk: false,
      fundSourceGapCount: 2,
      tossAttentionRequired: true,
    });

    expect(cards.find((card) => card.label === "섹터 폭·신용·유동성")?.tone).toBe("watch");
    expect(cards.find((card) => card.label === "ETF·펀드 원천")).toMatchObject({
      priority: "보강 필요",
      tone: "block",
    });
    expect(cards.find((card) => card.label === "토스 계좌·체결")?.nextAction).toBe("브로커 수집 상태 확인");
    expect(JSON.stringify(cards)).toContain("반영 비중 0");
  });
});
