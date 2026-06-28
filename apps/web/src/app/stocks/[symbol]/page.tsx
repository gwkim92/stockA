import Link from "next/link";
import type { Route } from "next";

import { getAiEvidenceNeighborhood, getRecommendationDetail, getStockDetail } from "@/lib/frontend-api";
import { koCode } from "@/lib/korean-labels";
import { buildStockViewModel, stockCopy, stockProductKind } from "@/lib/presentation";
import type { RecommendationPositionReference, StockDetailData } from "@/lib/types";

import { StockEvidenceNeighborhoodPanel } from "./_components/StockEvidenceNeighborhoodPanel";
import { StockFinancialStatementModelPanel } from "./_components/StockFinancialStatementModelPanel";
import { StockFundInstrumentAnalysisPanel } from "./_components/StockFundInstrumentAnalysisPanel";
import { StockIndustryCompetitivePositionPanel } from "./_components/StockIndustryCompetitivePositionPanel";
import { StockNewsImpactSections } from "./_components/StockNewsImpactSections";
import { StockPriceAndMarketSections } from "./_components/StockPriceAndMarketSections";
import { StockProfessionalEvidenceAuditPanel } from "./_components/StockProfessionalEvidenceAuditPanel";
import { StockProfessionalSourceGuardrailPanel } from "./_components/StockProfessionalSourceGuardrailPanel";
import { StockRecommendationPositionPanel } from "./_components/StockRecommendationPositionPanel";
import { StockResearchHeader } from "./_components/StockResearchHeader";
import { StockValuationResearchPanel } from "./_components/StockValuationResearchPanel";

export const dynamic = "force-dynamic";
export const metadata = { title: "종목 상세" };

type StockDetailPageProps = {
  params: Promise<{ symbol: string }>;
};

function formatCurrency(value: number | null, currencyCode: string) {
  if (value === null) {
    return "가격 없음";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: currencyCode,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "없음";
  }
  return value.toLocaleString("ko-KR");
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "미측정";
  }
  return `${Math.round(value * 1000) / 10}%`;
}

function latestDailyChangePct(data: StockDetailData) {
  if (data.latest_price.change_pct !== null && data.latest_price.change_pct !== undefined) {
    return data.latest_price.change_pct;
  }
  const latestBars = data.price_bars
    .filter((bar) => bar.adjusted_close !== null && bar.adjusted_close !== undefined)
    .slice(-2);
  const previousClose = latestBars[0]?.adjusted_close;
  const latestClose = latestBars[1]?.adjusted_close;
  if (!previousClose || latestClose === null || latestClose === undefined) {
    return null;
  }
  return (latestClose - previousClose) / previousClose;
}

function priceSourceProviderLabel(value: string | null | undefined) {
  if (!value || value.toLowerCase() === "missing") {
    return "원천 대기";
  }
  return userFacingStockText(koCode(value));
}

function priceSourceStatusLabel(value: string | null | undefined) {
  const normalized = (value ?? "").trim().toLowerCase();
  if (!normalized || normalized === "missing") {
    return "가격 데이터 대기";
  }
  if (normalized === "fresh" || normalized === "available" || normalized === "succeeded" || normalized === "ok") {
    return "사용 가능";
  }
  if (normalized === "stale") {
    return "최신성 주의";
  }
  return userFacingStockText(koCode(value));
}

function brokerRealityStatusLabel(data: StockDetailData) {
  if (data.toss_provider_evidence.status === "available" || data.toss_provider_evidence.used_for_account) {
    return "토스증권 기준 수집됨";
  }
  const brokerStatus = data.market_data_provider.broker_price_source.status;
  if (brokerStatus && brokerStatus !== "missing") {
    return priceSourceStatusLabel(brokerStatus);
  }
  return "토스증권 데이터 대기";
}

function brokerRealityContextLabel(data: StockDetailData) {
  const evidence = data.toss_provider_evidence;
  if (evidence.used_for_scoring) {
    return "추천 점수에 반영 중";
  }
  if (evidence.used_for_account) {
    return "계좌·보유·가상 매매 검증 참고, 추천 점수 미반영";
  }
  if (evidence.status === "available") {
    return "가격 기준 차이를 검증 중이며 추천 점수에는 반영하지 않습니다";
  }
  return "실제 증권사 기준 데이터가 들어오면 브로커 현실 확인에 사용합니다";
}

function recommendationHref(recommendationId: string) {
  return `/recommendations/${recommendationId}` as Route;
}

function thesisHref(thesisId: string) {
  return `/theses/${thesisId}` as Route;
}

async function loadRecommendationPositionContext(recommendationId: string | null | undefined) {
  if (!recommendationId) {
    return null;
  }
  try {
    const response = await getRecommendationDetail(recommendationId);
    return response.data.position_context;
  } catch {
    return null;
  }
}

function userFacingStockText(value: string | null | undefined) {
  return stockCopy(value);
}

function valuationSensitivityItems(value: Record<string, unknown>) {
  return Object.entries(value)
    .map(([key, rawValue]) => {
      if (rawValue === null || rawValue === undefined || rawValue === "") {
        return null;
      }
      const text =
        typeof rawValue === "number"
          ? rawValue.toLocaleString("ko-KR")
          : typeof rawValue === "string"
            ? rawValue
            : JSON.stringify(rawValue);
      return { key, value: text };
    })
    .filter((item): item is { key: string; value: string } => item !== null);
}

export default async function StockDetailPage({ params }: StockDetailPageProps) {
  const { symbol } = await params;
  const [response, neighborhoodResponse] = await Promise.all([
    getStockDetail(symbol),
    getAiEvidenceNeighborhood(symbol),
  ]);
  const data = response.data;
  const neighborhood = neighborhoodResponse.data;
  const hasPriceData = data.summary.bar_count > 0 && data.latest_price.close !== null;
  const equityResearch = data.equity_research;
  const industryPosition = data.industry_competitive_position;
  const financialStatementModel = data.financial_statement_model;
  const valuationTargetRange = data.valuation_target_range;
  const sourceGuardrail = data.professional_source_guardrail;
  const sourceBlocked = sourceGuardrail.blocked;
  const hasTargetRange = valuationTargetRange.status === "available";
  const valuationItems = equityResearch ? valuationSensitivityItems(equityResearch.valuation_sensitivity) : [];
  const hasEvidenceOnlyData =
    !hasPriceData && (data.macro_flow_impacts.length > 0 || data.recent_events.length > 0);
  const linkedThesisId = data.recommendation?.linked_thesis_id ?? neighborhood.theses[0]?.thesis_id ?? null;
  const marketCorrelationCount = data.market_correlations.length;
  const stockNewsCount = data.recent_events.length + data.macro_flow_impacts.length;
  const latestChangePct = latestDailyChangePct(data);
  const recommendationPositionContext: RecommendationPositionReference | null = await loadRecommendationPositionContext(
    data.recommendation?.recommendation_id,
  );
  const portfolioQuantity = recommendationPositionContext?.quantity ?? data.position?.quantity ?? null;
  const portfolioAverageCost = recommendationPositionContext?.average_cost ?? null;
  const portfolioUnrealizedPnl = recommendationPositionContext?.unrealized_pnl ?? null;
  const portfolioUnrealizedPnlPct = recommendationPositionContext?.unrealized_pnl_pct ?? null;
  const portfolioMarketValue = recommendationPositionContext?.market_value ?? data.position?.market_value ?? null;
  const stockProduct = stockProductKind(data);
  const stockViewModel = buildStockViewModel(data);
  const stockPriceLabel = hasPriceData ? formatCurrency(data.latest_price.close, data.currency_code) : "가격 없음";
  const stockPriceSourceLabel = `분석 기준 가격 · ${priceSourceProviderLabel(data.market_data_provider.analysis_price_source.provider)}`;
  const analysisPriceStatusLabel = priceSourceStatusLabel(
    data.market_data_provider.analysis_price_source.freshness_status || data.market_data_provider.freshness_status,
  );
  const brokerStatusLabel = brokerRealityStatusLabel(data);
  const brokerContextLabel = brokerRealityContextLabel(data);
  const positionQuantityLabel = portfolioQuantity === null ? "수량 없음" : `수량 ${formatNumber(portfolioQuantity)}`;
  const positionAverageCostLabel = portfolioAverageCost === null ? "평단 대기" : formatCurrency(portfolioAverageCost, data.currency_code);
  const positionUnrealizedPnlLabel =
    portfolioUnrealizedPnl === null || portfolioUnrealizedPnlPct === null
      ? "평가손익 대기"
      : `${formatCurrency(portfolioUnrealizedPnl, data.currency_code)} · ${formatPercent(portfolioUnrealizedPnlPct)}`;
  const recommendationHeaderHref = data.recommendation ? recommendationHref(data.recommendation.recommendation_id) : null;
  const recommendationHeaderLabel = data.recommendation ? koCode(data.recommendation.action) : "추천 없음";
  const recommendationHeaderContext = data.recommendation
    ? `점수 ${formatPercent(data.recommendation.score)} · ${koCode(data.recommendation.status)}`
    : "아직 이 종목에 연결된 추천 판단서가 없다.";

  return (
    <div className="pageStack decision-page">
      <StockResearchHeader
        symbol={data.symbol}
        name={data.name}
        marketCode={data.market_code}
        asOfDate={data.as_of_date}
        productKind={stockProduct}
        sourceBlocked={sourceBlocked}
        linkedThesisHref={linkedThesisId ? thesisHref(linkedThesisId) : null}
        viewModel={stockViewModel}
        price={{
          analysisStatusLabel: analysisPriceStatusLabel,
          brokerContextLabel,
          brokerStatusLabel,
          priceLabel: stockPriceLabel,
          changePct: latestChangePct,
          priceSourceLabel: stockPriceSourceLabel,
        }}
        position={{
          statusLabel: data.position ? "보유 중" : "미보유",
          quantityLabel: positionQuantityLabel,
          averageCostLabel: positionAverageCostLabel,
          unrealizedPnlLabel: positionUnrealizedPnlLabel,
        }}
        recommendation={{
          href: recommendationHeaderHref,
          label: recommendationHeaderLabel,
          context: recommendationHeaderContext,
        }}
        counts={{
          stockNewsCount,
          directNewsCount: data.recent_events.length,
          macroFlowCount: data.macro_flow_impacts.length,
          marketCorrelationCount,
          financialMetricCount: financialStatementModel.computed_metric_count,
          fundHoldingCount: data.fund_instrument_analysis?.holding_count ?? null,
        }}
      />

      <StockProfessionalEvidenceAuditPanel
        data={data}
        neighborhood={neighborhood}
        linkedThesisId={linkedThesisId}
        hasPriceData={hasPriceData}
      />

      <StockProfessionalSourceGuardrailPanel guardrail={sourceGuardrail} symbol={data.symbol} />

      <StockFinancialStatementModelPanel model={financialStatementModel} symbol={data.symbol} />

      <StockFundInstrumentAnalysisPanel analysis={data.fund_instrument_analysis} />

      {hasEvidenceOnlyData ? (
        <section className="bento-card reveal delay-1" aria-label="가격 데이터 부족 안내">
          <div className="section-heading stacked-heading">
            <span className="metric-sub">데이터 상태 구분</span>
            <h2>가격 데이터가 부족해 시장 흐름 노출부터 보여준다</h2>
          </div>
          <p style={{ color: "var(--text-secondary)", marginBottom: 0 }}>
            {data.symbol}은 현재 뉴스·테마 흐름에는 연결되어 있지만, 이 서버의 가격 캔들 수집 대상에는 아직 충분히
            포함되지 않았다. 따라서 가격 차트와 수익률은 판단하지 않고, 아래 상위 흐름/원천 뉴스만 본다.
          </p>
        </section>
      ) : null}

      <StockPriceAndMarketSections data={data} latestChangePct={latestChangePct} />

      <StockRecommendationPositionPanel
        data={data}
        portfolioQuantity={portfolioQuantity}
        portfolioAverageCost={portfolioAverageCost}
        portfolioMarketValue={portfolioMarketValue}
        portfolioUnrealizedPnl={portfolioUnrealizedPnl}
        portfolioUnrealizedPnlPct={portfolioUnrealizedPnlPct}
      />

      <StockValuationResearchPanel data={data} valuationItems={valuationItems} />

      <StockIndustryCompetitivePositionPanel position={industryPosition} symbol={data.symbol} />

      <StockEvidenceNeighborhoodPanel neighborhood={neighborhood} />

      <StockNewsImpactSections data={data} />
    </div>
  );
}
