import Link from "next/link";
import type { Route } from "next";
import { Fragment } from "react";

import { CandlestickChart } from "@/components/candlestick-chart";
import { NewsTitleBlock } from "@/components/news-title-block";
import { ProfessionalResearchFlow, type ResearchFlowStep } from "@/components/professional-research-flow";
import { SignedReturnBadge } from "@/components/research/SignedReturnBadge";
import { ValuationTargetRangeCard } from "@/components/valuation-target-range-card";
import { getAiEvidenceNeighborhood, getRecommendationDetail, getStockDetail } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";
import { buildStockViewModel, stockCopy, stockProductKind } from "@/lib/presentation";
import type { AiEvidenceNeighborhoodData, RecommendationPositionReference, StockDetailData } from "@/lib/types";

import { StockEvidenceNeighborhoodPanel } from "./_components/StockEvidenceNeighborhoodPanel";
import { StockFinancialStatementModelPanel } from "./_components/StockFinancialStatementModelPanel";
import { StockFundInstrumentAnalysisPanel } from "./_components/StockFundInstrumentAnalysisPanel";
import { StockIndustryCompetitivePositionPanel } from "./_components/StockIndustryCompetitivePositionPanel";
import { StockProfessionalEvidenceAuditPanel } from "./_components/StockProfessionalEvidenceAuditPanel";
import { StockProfessionalSourceGuardrailPanel } from "./_components/StockProfessionalSourceGuardrailPanel";
import { StockResearchHeader } from "./_components/StockResearchHeader";

export const dynamic = "force-dynamic";
export const metadata = { title: "종목 상세" };

type StockDetailPageProps = {
  params: Promise<{ symbol: string }>;
};

type ProfessionalSourceGuardrail = StockDetailData["professional_source_guardrail"];
type StockMarketCorrelation = StockDetailData["market_correlations"][number];

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

function formatCoefficient(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "미측정";
  }
  return new Intl.NumberFormat("ko-KR", {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
    signDisplay: "exceptZero",
  }).format(value);
}

function correlationRelationshipLabel(label: string) {
  if (label === "strong_positive") {
    return "강한 동행";
  }
  if (label === "strong_negative") {
    return "강한 반대";
  }
  if (label === "moderate_positive") {
    return "보통 동행";
  }
  if (label === "moderate_negative") {
    return "보통 반대";
  }
  return "약하거나 불명확";
}

function correlationTone(correlation: StockMarketCorrelation) {
  if (correlation.relationship_label.includes("strong")) {
    return "detail-path-card is-watch";
  }
  if (correlation.relationship_label.includes("moderate")) {
    return "detail-path-card is-good";
  }
  return "detail-path-card";
}

function priceSourceProviderLabel(value: string | null | undefined) {
  if (!value || value === "missing") {
    return "원천 대기";
  }
  return userFacingStockText(koCode(value));
}

function formatDate(value: string) {
  return value ? value.slice(0, 10) : "날짜 없음";
}

function recommendationHref(recommendationId: string) {
  return `/recommendations/${recommendationId}` as Route;
}

function thesisHref(thesisId: string) {
  return `/theses/${thesisId}` as Route;
}

function evidenceHref(evidenceId: string | null) {
  return evidenceId ? (`/ai-evidence/${evidenceId}` as Route) : null;
}

function sourceDocumentHref(documentId: string | null) {
  return documentId ? (`/source-documents/${documentId}` as Route) : null;
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

function providerLabel(provider: string) {
  if (provider === "codex_oauth") {
    return "심화 근거 분석";
  }
  if (provider === "fixture") {
    return "검증용 샘플 분석";
  }
  return koCode(provider);
}

function userFacingStockText(value: string | null | undefined) {
  return stockCopy(value);
}

function valuationSensitivityLabel(key: string) {
  const labels: Record<string, string> = {
    "base case": "기준 시나리오",
    base_case: "기준 시나리오",
    confidence: "신뢰도",
    "upside case": "상승 시나리오",
    upside_case: "상승 시나리오",
    downside_case: "하락 시나리오",
  };
  return labels[key] ?? labels[key.toLowerCase()] ?? userFacingStockText(koCode(key));
}

function stockDecisionOutcome(
  data: StockDetailData,
  guardrail: ProfessionalSourceGuardrail,
  hasPriceData: boolean,
) {
  if (guardrail.blocked) {
    return {
      tone: "blocked",
      label: "입력 차단",
      title: `${data.symbol} 상태: 투자 판단 입력 제외`,
      body: userFacingStockText(guardrail.summary),
    };
  }
  if (data.recommendation && data.position) {
    return {
      tone: "ready",
      label: "추천·보유 연결",
      title: `${data.symbol} 투자 리서치`,
      body: "보유 중인 추천 관찰 종목이다. 가격, 포지션, 재무·밸류에이션, 뉴스·사이클 근거를 같은 화면에서 정리한다.",
    };
  }
  if (data.recommendation) {
    return {
      tone: "ready",
      label: "추천 근거 있음",
      title: `${data.symbol} 투자 리서치`,
      body: "추천 근거가 있는 관찰 종목이다. 점수 구성, 기업 분석, 뉴스·사이클 근거, 실거래 차단 상태를 함께 정리한다.",
    };
  }
  if (data.position) {
    return {
      tone: "watch",
      label: "보유 상태",
      title: `${data.symbol} 투자 리서치`,
      body: "보유 포지션은 있으나 최신 추천이 없다. 보유 이유와 최근 뉴스·상위 흐름의 충돌 여부를 먼저 정리한다.",
    };
  }
  if (!hasPriceData) {
    return {
      tone: "watch",
      label: "가격 보강 필요",
      title: `${data.symbol} 상태: 가격 데이터 부족`,
      body: "뉴스·상위 흐름은 볼 수 있지만 가격 차트와 수익률 판단은 아직 보류한다.",
    };
  }
  return {
    tone: "neutral",
    label: "관찰 종목",
    title: `${data.symbol} 투자 리서치`,
    body: "가격 데이터는 있으나 추천·보유 연결은 아직 없다. 뉴스와 사이클 근거가 쌓이는 관찰 단계다.",
  };
}

function competitivePositionLabel(value: string) {
  const labels: Record<string, string> = {
    leader: "경쟁 우위",
    advantaged: "우위 후보",
    in_line: "평균권",
    challenged: "열위 검토",
    insufficient_data: "데이터 부족",
  };
  return labels[value] ?? userFacingStockText(koCode(value));
}

function competitivePositionSummary(position: NonNullable<StockDetailData["industry_competitive_position"]>, symbol: string) {
  const peerGroup = userFacingStockText(position.peer_group_name ?? position.peer_group_code ?? "비교군");
  const sector = userFacingStockText(position.sector_name ?? position.sector_code ?? "섹터 분류 대기");
  return `${symbol}은 ${peerGroup} 기준으로 ${competitivePositionLabel(position.competitive_position)} 상태다. ${sector} 안에서 수익성, 성장성, 재무 방어력, 가격 결정력 추정 지표를 함께 비교한다.`;
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

function ResearchList({ title, items, emptyText }: { title: string; items: string[]; emptyText: string }) {
  return (
    <article className="bento-card">
      <span className="metric-sub">{title}</span>
      <div className="bento-list compact-list">
        {items.length > 0 ? (
          items.map((item) => (
            <div className="bento-list-item" key={item}>{userFacingStockText(item)}</div>
          ))
        ) : (
          <div className="empty-state">{emptyText}</div>
        )}
      </div>
    </article>
  );
}

function cleanFlowText(
  value: string | null | undefined,
  options: {
    themeKey: string;
    symbol: string;
    impactDirection: string;
  },
) {
  const { themeKey, symbol, impactDirection } = options;
  if (!value) {
    return `${koCode(themeKey)} 흐름이 ${koCode(symbol)}에 ${koCode(impactDirection)} 방향으로 전파됐다. 노출도와 신뢰도는 위 수치를 기준으로 본다.`;
  }
  if (/flow propagated to/i.test(value) || /directly exposed/i.test(value)) {
    return `${koCode(themeKey)} 흐름이 ${koCode(symbol)}에 ${koCode(impactDirection)} 방향으로 전파됐다. 자세한 근거는 상세 버튼에서 본다.`;
  }
  const interpretation = value.match(/해석:\s*(.*?)(?:\s*근거:|;\s*노출 근거:|$)/)?.[1]?.trim();
  const evidence = value.match(/근거:\s*(.*?)(?:;\s*노출 근거:|$)/)?.[1]?.trim();
  const exposure = value.match(/노출 근거:\s*(.*)$/)?.[1]?.trim();
  const parts = [
    interpretation ? `해석: ${koLabel(interpretation)}` : null,
    evidence ? `근거: ${koLabel(evidence)}` : null,
    exposure
      ? `노출: ${
          /directly exposed/i.test(exposure)
            ? "이 종목은 해당 테마의 자금 지원·상용화 뉴스에 직접 노출된다."
            : koLabel(exposure)
        }`
      : null,
  ].filter(Boolean);
  if (parts.length > 0) {
    return parts.join(" ");
  }
  return koLabel(value);
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
  const professionalResearchSteps: ResearchFlowStep[] = [
    {
      id: "business",
      label: "01",
      title: "사업 개요",
      status: equityResearch ? "리서치 생성" : "리서치 대기",
      tone: equityResearch ? "ready" : "watch",
      body: equityResearch?.korean_summary
        ? userFacingStockText(equityResearch.korean_summary)
        : "이 종목의 사업 설명 결과가 아직 없다. 현재 화면에서는 가격, 뉴스, 상위 흐름까지만 신뢰할 수 있다.",
      facts: [
        { label: "종목", value: `${data.symbol} · ${data.name}` },
        { label: "시장", value: `${data.market_code} · ${data.currency_code}` },
      ],
    },
    {
      id: "financial-quality",
      label: "02",
      title: "재무 품질",
      status: sourceBlocked
        ? "투자 판단 차단"
        : financialStatementModel.status === "available" || financialStatementModel.status === "partial"
          ? `${financialStatementModel.computed_metric_count}개 지표`
          : "재무 모델 대기",
      tone: sourceBlocked
        ? "blocked"
        : financialStatementModel.status === "available" || financialStatementModel.status === "partial"
          ? "ready"
          : "watch",
      body: sourceBlocked
        ? userFacingStockText(sourceGuardrail.summary)
        : financialStatementModel.status === "available" || financialStatementModel.status === "partial" || financialStatementModel.source_data_blocker
          ? userFacingStockText(financialStatementModel.summary)
          : "매출, 마진, 현금흐름, 부채, 이익 품질을 확인할 정규화 재무 모델이 아직 충분하지 않다.",
      facts: [
        { label: "최근 기간", value: financialStatementModel.latest_period_end || "없음" },
        { label: "계산 지표", value: `${financialStatementModel.computed_metric_count}개` },
        { label: "데이터 공백", value: `${financialStatementModel.data_gap_count}개` },
        { label: "근거 상태", value: sourceBlocked ? sourceGuardrail.blocker_label : "차단 없음" },
      ],
    },
    {
      id: "peer-position",
      label: "03",
      title: "피어·경쟁 위치",
      status: industryPosition ? competitivePositionLabel(industryPosition.competitive_position) : "비교군 표시 대기",
      tone: industryPosition ? "ready" : "watch",
      body: industryPosition
        ? competitivePositionSummary(industryPosition, data.symbol)
        : "동일 산업·테마 비교군 안에서 수익성, 성장성, 재무 안정성, 가격 결정력 추정 지표를 보여주는 데이터가 아직 없다.",
      facts: industryPosition
        ? [
            { label: "비교군", value: industryPosition.peer_group_name ?? industryPosition.peer_group_code ?? "미분류" },
            { label: "종합 경쟁력", value: formatPercent(industryPosition.moat_score) },
            { label: "경쟁 강도", value: formatPercent(industryPosition.rivalry_risk_score) },
          ]
        : undefined,
      href: data.recommendation ? recommendationHref(data.recommendation.recommendation_id) : undefined,
      hrefLabel: data.recommendation ? "추천 상세에서 같이 보기" : undefined,
    },
    {
      id: "valuation",
      label: "04",
      title: "밸류에이션",
      status: hasTargetRange ? `${valuationTargetRange.method_count}개 목표가 산출` : (valuationItems.length ? `${valuationItems.length}개 민감도` : "산출 대기"),
      tone: hasTargetRange || valuationItems.length ? "ready" : "watch",
      body: hasTargetRange
        ? "현재가 대비 목표가 하단·기준·상단과 안전마진을 비교한다. 이 값은 추천 점수를 바로 바꾸지 않고 가격 근거로만 사용한다."
        : valuationItems.length
          ? "현금흐름, 상대 배수, 시나리오 범위가 추천 점수를 바로 바꾸지는 않지만, 비싸게 사는지 여부를 확인하는 핵심 입력이다."
        : "아직 목표가 범위, 안전마진, 시나리오 민감도가 충분히 저장되지 않았다.",
      facts:
        hasTargetRange
          ? [
              { label: "기준 목표가", value: formatCurrency(valuationTargetRange.target_base, valuationTargetRange.currency_code) },
              { label: "기준 상승여지", value: formatPercent(valuationTargetRange.upside_base) },
              { label: "산출 방법", value: `${valuationTargetRange.method_count}개` },
            ]
          : valuationItems.length > 0
          ? valuationItems.slice(0, 3).map((item) => ({
              label: valuationSensitivityLabel(item.key),
              value: userFacingStockText(item.value),
            }))
          : [{ label: "상태", value: "밸류에이션 결과 대기" }],
    },
    {
      id: "news-cycle",
      label: "05",
      title: "뉴스·사이클 영향",
      status: `${data.recent_events.length + data.macro_flow_impacts.length}개 뉴스·흐름 · ${marketCorrelationCount}개 동조성`,
      tone: data.recent_events.length + data.macro_flow_impacts.length + marketCorrelationCount > 0 ? "ready" : "neutral",
      body:
        data.recent_events.length + data.macro_flow_impacts.length + marketCorrelationCount > 0
          ? "직접 종목 뉴스, 거시·테마 흐름 전파, 시장 지표와의 동조성을 분리했다. 동조성은 원인 단정이 아니라 리스크 점검 입력이다."
          : "아직 이 종목에 연결된 직접 뉴스, 상위 흐름 전파, 시장 동조성 근거가 없다.",
      facts: [
        { label: "직접 뉴스", value: `${data.recent_events.length}개` },
        { label: "상위 흐름", value: `${data.macro_flow_impacts.length}개` },
        { label: "시장 동조성", value: `${marketCorrelationCount}개` },
      ],
      href: "/intelligence" as Route,
      hrefLabel: "뉴스 근거 흐름 보기",
    },
    {
      id: "thesis",
      label: "06",
      title: "투자 논리 생애주기",
      status: linkedThesisId ? "투자 논리 연결" : "투자 논리 없음",
      tone: linkedThesisId ? "ready" : "blocked",
      body: linkedThesisId
        ? "왜 사는지, 무엇이 맞아야 하는지, 무엇이 틀리면 나가는지가 투자 논리 화면에 연결됐다."
        : "중장기 투자 시스템에서는 투자 논리 없이 추천이나 보유 판단을 신뢰하면 안 된다.",
      href: linkedThesisId ? thesisHref(linkedThesisId) : undefined,
      hrefLabel: linkedThesisId ? "투자 논리 열기" : undefined,
    },
    {
      id: "paper-validation",
      label: "07",
      title: "가상 매매·실거래 상태",
      status: sourceBlocked ? "가상 검증 입력 차단" : data.position ? "보유 상태 있음" : data.recommendation ? "추천 근거 있음" : "거래 입력 전",
      tone: sourceBlocked ? "blocked" : "neutral",
      body: sourceBlocked
        ? `${userFacingStockText(sourceGuardrail.next_action)} 실제 증권사 주문 전송은 계속 닫혀 있다.`
        : "실제 증권사 주문 전송은 닫혀 있다. 추천이 생겨도 가상 매매 검증과 리스크 상태가 먼저다.",
      href: "/paper-trading" as Route,
      hrefLabel: "가상 매매 상태 보기",
    },
  ];
  const stockOutcome = stockDecisionOutcome(data, sourceGuardrail, hasPriceData);
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

      <ProfessionalResearchFlow
        eyebrow="리서치 구조"
        title={`${data.symbol} 투자 판단 지도`}
        summary="사업, 재무, 비교군, 밸류에이션, 뉴스·사이클, 투자 논리, 가상 매매 검증을 한 종목 안에서 정렬했다."
        footer="읽기 전용 리서치 화면이다. 추천 점수와 주문은 이 화면에서 바뀌지 않는다."
        steps={professionalResearchSteps}
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

      <section className="bento-grid reveal delay-2" id="stock-price-data" aria-label="가격 데이터와 차트">
        <article className="bento-card span-3">
          <div className="section-heading">
            <div>
              <span className="metric-sub">1. 가격 데이터</span>
              <h2>가격 흐름은 데이터 출처와 추세가 먼저다</h2>
            </div>
            <Link className="btn btn-secondary" href="/data-health">
              수집 상태 보기
            </Link>
          </div>
          <CandlestickChart
            bars={data.candles}
            currencyCode={data.currency_code}
            provider={data.market_data_provider}
            tossEvidence={data.toss_provider_evidence}
          />
        </article>

        <article className="bento-card">
          <span className="metric-label">가격 데이터</span>
          <strong className="metric-value">{data.summary.bar_count.toLocaleString("ko-KR")}</strong>
          <span className="metric-sub">수집된 거래일 수</span>
          <div className="stock-meta-grid">
            <span>저가 종가</span>
            <strong>{formatCurrency(data.summary.low_close, data.currency_code)}</strong>
            <span>고가 종가</span>
            <strong>{formatCurrency(data.summary.high_close, data.currency_code)}</strong>
            <span>거래량</span>
            <strong>{formatNumber(data.latest_price.volume)}</strong>
            <span>전일 대비</span>
            <strong>
              <SignedReturnBadge value={latestChangePct} />
            </strong>
          </div>
          <div className="stock-meta-grid" style={{ marginTop: "1rem" }}>
            <span>분석 기준</span>
            <strong>{data.market_data_provider.analysis_price_source.provider}</strong>
            <span>계산 반영</span>
            <strong>{data.market_data_provider.analysis_price_source.used_for_scoring ? "추천·사이클 사용" : "미사용"}</strong>
            <span>브로커 참고</span>
            <strong>{data.market_data_provider.broker_price_source.label}</strong>
            <span>토스 상태</span>
            <strong>{data.toss_provider_evidence.comparison.status_label}</strong>
          </div>
          <p style={{ color: "var(--text-secondary)", marginBottom: 0 }}>
            {data.market_data_provider.price_basis_note} 토스증권 가격은 계좌·호가 현실 확인용이며 총점에는 아직 반영하지 않는다.
          </p>
        </article>
      </section>

      <section className="bento-card span-4 reveal delay-2" id="stock-market-correlations" aria-label="시장 동조성">
        <div className="section-heading">
          <div>
          <span className="metric-sub">2. 시장 동조성</span>
            <h2>{data.symbol}과 같이 움직인 시장 변수</h2>
          </div>
          <Link className="btn btn-secondary" href="/market-map">
            시장 지도 보기
          </Link>
        </div>
        <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
          상관관계는 최근 수익률이 같이 움직인 정도다. 원인을 단정하지 않고, 포트폴리오 집중·헤지 필요성·추천 리스크의 보조 입력으로만 사용한다.
        </p>
        {data.market_correlations.length > 0 ? (
          <div className="detail-path-grid">
            {data.market_correlations.slice(0, 6).map((correlation) => (
              <article
                className={correlationTone(correlation)}
                key={`${correlation.primary_asset_key}-${correlation.comparison_asset_key}-${correlation.lookback_days}`}
              >
                <span>
                  {correlationRelationshipLabel(correlation.relationship_label)} · {correlation.lookback_days}일 · 신뢰도{" "}
                  {formatPercent(correlation.confidence)}
                </span>
                <strong>
                  {correlation.primary_display_name} ↔ {correlation.comparison_display_name}
                </strong>
                <small>
                  상관계수 {formatCoefficient(correlation.correlation)} · 베타 {formatCoefficient(correlation.beta)} · 관측{" "}
                  {correlation.observation_count.toLocaleString("ko-KR")}개
                </small>
                <p>{correlation.summary_ko}</p>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            아직 이 종목의 시장 동조성이 계산되지 않았다. 장마감 후 상관관계 분석이 실행되면 지수·섹터·금리·달러·원자재와의 관계가 표시된다.
          </div>
        )}
      </section>

      <section className="bento-grid reveal delay-3" id="stock-recommendation-status" aria-label="추천과 보유 상태">
        <article className="bento-card span-2">
          <div className="section-heading">
            <div>
              <span className="metric-sub">3. 추천 판단</span>
              <h2>추천 근거와 거래 경계</h2>
            </div>
            {data.recommendation ? (
              <Link className="btn btn-primary" href={recommendationHref(data.recommendation.recommendation_id)}>
                추천 상세
              </Link>
            ) : null}
          </div>
          {data.recommendation ? (
            <div className="stock-meta-grid">
              <span>판단</span>
              <strong>{koCode(data.recommendation.action)}</strong>
              <span>점수</span>
              <strong>{formatPercent(data.recommendation.score)}</strong>
              <span>상태</span>
              <strong>{koCode(data.recommendation.status)}</strong>
              <span>투자 논리</span>
              {data.recommendation.linked_thesis_id ? (
                <Link href={thesisHref(data.recommendation.linked_thesis_id)}>
                  투자 논리 열기
                </Link>
              ) : (
                <strong>없음</strong>
              )}
            </div>
          ) : (
            <div className="empty-state">이 종목은 아직 추천 점수와 투자 논리가 붙지 않았다.</div>
          )}
        </article>

        <article className="bento-card span-2">
          <div className="section-heading">
            <div>
              <span className="metric-sub">4. 보유 상태</span>
              <h2>보유 포지션과 평가손익</h2>
            </div>
            <Link className="btn btn-secondary" href="/portfolio/coverage">
              포트폴리오 보기
            </Link>
          </div>
          {data.position ? (
            <div className="stock-meta-grid">
              <span>포트폴리오</span>
              <strong>{koLabel(data.position.portfolio_name)}</strong>
              <span>수량</span>
              <strong>{formatNumber(portfolioQuantity)}</strong>
              <span>평단가</span>
              <strong>{portfolioAverageCost !== null ? formatCurrency(portfolioAverageCost, data.currency_code) : "추천 원장 대기"}</strong>
              <span>평가액</span>
              <strong>{formatCurrency(portfolioMarketValue, data.currency_code)}</strong>
              <span>평가 가격</span>
              <strong>{formatCurrency(data.position.market_price, data.currency_code)}</strong>
              <span>평가손익</span>
              <strong>
                {portfolioUnrealizedPnl !== null
                  ? `${formatCurrency(portfolioUnrealizedPnl, data.currency_code)} · ${formatPercent(portfolioUnrealizedPnlPct)}`
                  : "추천 원장 대기"}
              </strong>
            </div>
          ) : (
            <div className="empty-state">현재 포트폴리오 스냅샷에는 보유 포지션이 없다.</div>
          )}
        </article>
      </section>

      <div id="stock-valuation">
        <ValuationTargetRangeCard
          valuation={valuationTargetRange}
          eyebrow="전문 밸류에이션"
          title={`${data.symbol} 목표가 범위`}
        />
      </div>

      <section className="bento-card span-4 reveal delay-3" id="stock-equity-research" aria-label="기업 리서치 리포트">
        <div className="section-heading">
          <div>
            <span className="metric-sub">기업 리서치 리포트</span>
            <h2>{equityResearch ? userFacingStockText(equityResearch.title) : `${data.symbol} 기업 리서치가 아직 생성되지 않았다`}</h2>
          </div>
          {equityResearch ? (
            <span className="bento-badge" style={{ margin: 0 }}>
              {providerLabel(equityResearch.provider)} • {equityResearch.as_of_date}
            </span>
          ) : null}
        </div>
        {equityResearch ? (
          <>
            <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
              {userFacingStockText(equityResearch.korean_summary)}
            </p>
            <div className="status-rail compact-rail" aria-label="기업 리서치 범위">
              <div className="rail-cell">
                <span>핵심 변화</span>
                <strong>{equityResearch.key_points.length}</strong>
                <small>사업·재무 포인트</small>
              </div>
              <div className="rail-cell">
                <span>촉매</span>
                <strong>{equityResearch.catalysts.length}</strong>
                <small>좋아질 조건</small>
              </div>
              <div className="rail-cell">
                <span>리스크</span>
                <strong>{equityResearch.risks.length}</strong>
                <small>틀릴 수 있는 이유</small>
              </div>
              <div className="rail-cell">
                <span>무효화 조건</span>
                <strong>{equityResearch.invalidation_conditions.length}</strong>
                <small>투자 논리 재검토 기준</small>
              </div>
            </div>
            <div className="bento-grid" style={{ marginTop: "18px" }}>
              <ResearchList
                title="핵심 포인트"
                items={equityResearch.key_points}
                emptyText="핵심 변화가 아직 구조화되지 않았다."
              />
              <ResearchList
                title="촉매"
                items={equityResearch.catalysts}
                emptyText="상승 촉매가 아직 구조화되지 않았다."
              />
              <ResearchList
                title="리스크"
                items={equityResearch.risks}
                emptyText="리스크가 아직 구조화되지 않았다."
              />
              <ResearchList
                title="무효화 조건"
                items={equityResearch.invalidation_conditions}
                emptyText="투자 논리 무효화 조건이 아직 구조화되지 않았다."
              />
            </div>
            {valuationItems.length > 0 ? (
              <div className="stock-meta-grid" style={{ marginTop: "18px" }}>
                {valuationItems.map((item) => (
                  <Fragment key={item.key}>
                    <span>{valuationSensitivityLabel(item.key)}</span>
                    <strong>{userFacingStockText(item.value)}</strong>
                  </Fragment>
                ))}
              </div>
            ) : null}
            {equityResearch.source_document_ids.length > 0 ? (
              <div className="btn-row">
                {equityResearch.source_document_ids.slice(0, 3).map((documentId, index) => (
                  <Link className="btn btn-secondary" href={sourceDocumentHref(documentId) ?? "/data-health"} key={documentId}>
                    원천 문서 {index + 1}
                  </Link>
                ))}
              </div>
            ) : null}
            <p style={{ color: "var(--text-muted)", marginBottom: 0 }}>
              이 리포트는 저장된 읽기 전용 분석이다. 추천 점수와 주문은 직접 변경하지 않으며,
              추천 상세의 재무·밸류에이션 근거와 성과 평가는 별도로 본다.
            </p>
          </>
        ) : (
          <div className="empty-state">
            아직 이 종목의 기업 리서치 결과가 없다. 자동 분석이 완료되면 사업 설명, 핵심 재무 변화,
            촉매, 리스크, 무효화 조건, 밸류에이션 민감도가 이곳에 표시된다.
          </div>
        )}
      </section>

      <StockIndustryCompetitivePositionPanel position={industryPosition} symbol={data.symbol} />

      <StockEvidenceNeighborhoodPanel neighborhood={neighborhood} />

      <section className="bento-card span-4 reveal delay-4" id="stock-flow-impacts">
        <div className="section-heading">
          <div>
            <span className="metric-sub">5. 상위 흐름 전파</span>
            <h2>회사명이 없어도 거시·테마 흐름은 종목에 영향을 줄 수 있다</h2>
          </div>
          <Link className="btn btn-secondary" href="/intelligence">
            흐름 분석 보기
          </Link>
        </div>
        <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
          회사가 직접 언급되지 않은 뉴스라도 금리, 에너지, AI 반도체 같은 상위 흐름이면 노출도에 따라 이 종목으로 영향이 전파된다.
        </p>
        <div className="bento-list">
          {data.macro_flow_impacts.length > 0 ? (
            data.macro_flow_impacts.map((flow) => {
              const evidence = evidenceHref(flow.ai_evidence_id);
              const sourceDocument = sourceDocumentHref(flow.source_document_id);
              const flowRationale = cleanFlowText(flow.rationale, {
                themeKey: flow.theme_key,
                symbol: data.symbol,
                impactDirection: flow.impact_direction,
              });
              return (
                <div className="bento-list-item" key={`${flow.event_id}-${flow.theme_key}`}>
                  <div>
                    <span className="metric-sub">
                      {formatDate(flow.event_at)} • {koCode(flow.theme_key)} • {koCode(flow.impact_direction)}
                    </span>
                    <NewsTitleBlock
                      title={flow.title}
                      koreanTitle={flow.korean_title}
                      koreanSummary={flow.korean_summary}
                      translationConfidence={flow.translation_confidence}
                      symbol={data.symbol}
                      themeKey={flow.theme_key}
                      impactDirection={flow.impact_direction}
                      impactScore={flow.impact_score}
                    />
                    <span>
                      전파 강도 {formatPercent(flow.impact_score)} · 노출도 {formatPercent(flow.exposure_weight)} · 신뢰도 {formatPercent(flow.confidence)}
                    </span>
                    {flowRationale ? <span className="flow-rationale">{flowRationale}</span> : null}
                  </div>
                  <div className="btn-row" style={{ marginTop: 0 }}>
                    <Link className="btn btn-secondary" href={`/themes/${encodeURIComponent(flow.theme_key)}?asOfDate=${encodeURIComponent(data.as_of_date)}` as Route}>
                      흐름 보기
                    </Link>
                    {evidence ? <Link className="btn btn-secondary" href={evidence}>근거 상세</Link> : null}
                    {sourceDocument ? <Link className="btn btn-secondary" href={sourceDocument}>근거 문서</Link> : null}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="empty-state">
              아직 이 종목으로 전파된 상위 흐름이 없다. 직접 뉴스만 있거나 종목 민감도 연결이 부족한 상태다.
            </div>
          )}
        </div>
      </section>

      <section className="bento-card span-4 reveal delay-4" id="stock-direct-events">
        <div className="section-heading">
          <div>
            <span className="metric-sub">6. 직접 뉴스</span>
            <h2>회사나 티커가 직접 연결된 뉴스만 따로 본다</h2>
          </div>
          <Link className="btn btn-secondary" href={`/events?symbol=${encodeURIComponent(data.symbol)}` as Route}>
            수집 뉴스
          </Link>
        </div>
        <div className="bento-list">
          {data.recent_events.length > 0 ? (
            data.recent_events.map((event) => {
              const evidence = evidenceHref(event.ai_evidence_id);
              const sourceDocument = sourceDocumentHref(event.source_document_id);
              return (
                <div className="bento-list-item" key={event.event_id}>
                  <div>
                    <span className="metric-sub">{formatDate(event.event_at)} • {koCode(event.event_type)}</span>
                    <NewsTitleBlock
                      title={event.title}
                      koreanTitle={event.korean_title}
                      koreanSummary={event.korean_summary}
                      translationConfidence={event.translation_confidence}
                      symbol={data.symbol}
                      impactDirection={event.impact_direction}
                      impactScore={event.impact_score}
                    />
                    <span>{koCode(event.impact_direction)} • 영향도 {formatPercent(event.impact_score)}</span>
                  </div>
                  <div className="btn-row" style={{ marginTop: 0 }}>
                    {evidence ? <Link className="btn btn-secondary" href={evidence}>근거 상세</Link> : null}
                    {sourceDocument ? <Link className="btn btn-secondary" href={sourceDocument}>근거 문서</Link> : null}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="empty-state">아직 이 종목에 연결된 이벤트가 없다.</div>
          )}
        </div>
      </section>
    </div>
  );
}
