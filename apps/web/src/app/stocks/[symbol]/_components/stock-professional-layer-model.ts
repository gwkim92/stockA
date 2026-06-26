import type { Route } from "next";

import { koCode } from "@/lib/korean-labels";
import type { AiEvidenceNeighborhoodData, StockDetailData } from "@/lib/types";

import { formatPercent, stockSourceLabel, stockText } from "./stock-detail-panel-format";

export type StockProfessionalLayerStatus = "complete" | "partial" | "pending" | "blocked" | "missing" | "not_applicable";

export type StockProfessionalLayer = {
  readonly key: string;
  readonly label: string;
  readonly status: StockProfessionalLayerStatus;
  readonly detail: string;
  readonly source: string;
  readonly href?: Route | `#${string}`;
  readonly hrefLabel?: string;
};

function valuationSensitivityItems(value: Record<string, unknown>) {
  return Object.values(value).filter((rawValue) => rawValue !== null && rawValue !== undefined && rawValue !== "");
}

function recommendationHref(recommendationId: string) {
  return `/recommendations/${recommendationId}` as Route;
}

function thesisHref(thesisId: string) {
  return `/theses/${thesisId}` as Route;
}

function competitivePositionLabel(value: string) {
  const labels: Record<string, string> = {
    leader: "경쟁 우위",
    advantaged: "우위 후보",
    in_line: "평균권",
    challenged: "열위 검토",
    insufficient_data: "데이터 부족",
  };
  return labels[value] ?? stockSourceLabel(value);
}

function financialModelStatus(data: StockDetailData, isFundLike: boolean): StockProfessionalLayerStatus {
  if (isFundLike) {
    return "not_applicable";
  }
  if (data.professional_source_guardrail.blocked) {
    return "blocked";
  }
  if (data.financial_statement_model.status === "available") {
    return "complete";
  }
  if (data.financial_statement_model.status === "partial" || data.financial_statement_model.computed_metric_count > 0) {
    return "partial";
  }
  return "missing";
}

function valuationStatus(data: StockDetailData, isFundLike: boolean, valuationItemCount: number): StockProfessionalLayerStatus {
  if (isFundLike) {
    return "not_applicable";
  }
  if (data.valuation_target_range.status === "available") {
    return "complete";
  }
  if (valuationItemCount > 0) {
    return "partial";
  }
  return "missing";
}

export function buildStockProfessionalLayers({
  data,
  neighborhood,
  linkedThesisId,
  hasPriceData,
}: {
  readonly data: StockDetailData;
  readonly neighborhood: AiEvidenceNeighborhoodData;
  readonly linkedThesisId: string | null;
  readonly hasPriceData: boolean;
}): readonly StockProfessionalLayer[] {
  const guardrail = data.professional_source_guardrail;
  const isFundLike = guardrail.status === "fund_or_etf_company_model_not_applicable" || data.fund_instrument_analysis !== null;
  const valuationItemCount = data.equity_research ? valuationSensitivityItems(data.equity_research.valuation_sensitivity).length : 0;
  const newsCount = data.recent_events.length + data.macro_flow_impacts.length;
  const aiEvidenceCount = neighborhood.summary.ai_artifact_count;

  return [
    {
      key: "business_research",
      label: "사업 리서치",
      status: data.equity_research ? "complete" : "missing",
      detail: data.equity_research
        ? `기업 리서치가 ${data.equity_research.as_of_date} 기준으로 저장됐다. 사업 설명, 촉매, 리스크, 무효화 조건을 아래에서 본다.`
        : "사업 설명, 촉매, 리스크, 무효화 조건을 요약한 기업 리서치가 아직 없다.",
      source: "기업 리서치",
      href: "#stock-equity-research",
      hrefLabel: "기업 리서치",
    },
    {
      key: "financial_model",
      label: "재무제표 모델",
      status: financialModelStatus(data, isFundLike),
      detail: isFundLike
        ? "ETF·펀드형 상품은 개별 기업 재무제표 모델 대신 보유종목, 비용률, NAV, 추적 차이를 본다."
        : guardrail.blocked
          ? stockText(guardrail.summary)
          : data.financial_statement_model.computed_metric_count > 0
            ? `정규화 재무 지표 ${data.financial_statement_model.computed_metric_count}개가 계산됐다. 데이터 공백은 ${data.financial_statement_model.data_gap_count}개다.`
            : "매출, 마진, 현금흐름, 부채, 희석 같은 정규화 재무 지표가 아직 충분하지 않다.",
      source: "재무제표 정규화",
      href: "#stock-financial-model",
      hrefLabel: "재무 근거",
    },
    {
      key: "fund_source",
      label: "ETF·펀드 근거",
      status: isFundLike ? (data.fund_instrument_analysis ? "complete" : "missing") : "not_applicable",
      detail: data.fund_instrument_analysis
        ? `보유종목 ${data.fund_instrument_analysis.holding_count}개, 커버리지 ${formatPercent(data.fund_instrument_analysis.holdings_coverage_weight)}가 연결됐다.`
        : isFundLike
          ? "펀드형 상품으로 분류됐지만 보유종목, 비용률, NAV, 추적차이 원천이 아직 충분하지 않다."
          : "일반 기업 종목이므로 ETF·펀드 근거 레이어는 적용하지 않는다.",
      source: "ETF·펀드 분석",
      href: "#stock-fund-analysis",
      hrefLabel: "ETF·펀드 근거",
    },
    {
      key: "peer_industry",
      label: "피어·산업 위치",
      status: isFundLike ? "not_applicable" : data.industry_competitive_position ? "complete" : "missing",
      detail: isFundLike
        ? "ETF·펀드형 상품은 기업 peer 대신 보유종목 구성과 벤치마크 노출을 본다."
        : data.industry_competitive_position
          ? `${data.industry_competitive_position.peer_group_name ?? data.industry_competitive_position.peer_group_code ?? "비교군"} 기준 ${competitivePositionLabel(data.industry_competitive_position.competitive_position)} 상태다.`
          : "같은 산업·테마 비교군 안의 상대 위치가 아직 연결되지 않았다.",
      source: "산업·피어 분석",
      href: "#stock-industry-position",
      hrefLabel: "산업 위치",
    },
    {
      key: "valuation",
      label: "밸류에이션",
      status: valuationStatus(data, isFundLike, valuationItemCount),
      detail: isFundLike
        ? "ETF·펀드형 상품은 DCF 목표가 대신 NAV 괴리, 비용률, 추적 차이, 유동성을 본다."
        : data.valuation_target_range.status === "available"
          ? `목표가 범위 ${data.valuation_target_range.method_count}개 방법과 기준 상승여지 ${formatPercent(data.valuation_target_range.upside_base)}가 연결됐다.`
          : valuationItemCount > 0
            ? "기업 리서치의 밸류에이션 민감도는 있으나 목표가 범위 snapshot은 아직 부족하다."
            : "DCF-lite, 상대 배수, 시나리오 범위, SOTP 목표가가 아직 충분히 연결되지 않았다.",
      source: "밸류에이션 snapshot",
      href: "#stock-valuation",
      hrefLabel: "가격 근거",
    },
    {
      key: "news_cycle",
      label: "뉴스·사이클",
      status: newsCount > 0 || aiEvidenceCount > 0 ? "complete" : "missing",
      detail:
        newsCount > 0 || aiEvidenceCount > 0
          ? `직접 뉴스 ${data.recent_events.length}개, 상위 흐름 ${data.macro_flow_impacts.length}개, 심화 근거 ${aiEvidenceCount}개가 연결됐다.`
          : "이 종목에 연결된 직접 뉴스, 상위 흐름 전파, 투자 근거가 아직 없다.",
      source: "뉴스·AI 근거",
      href: "#stock-flow-impacts",
      hrefLabel: "뉴스·흐름",
    },
    {
      key: "thesis",
      label: "투자 논리",
      status: linkedThesisId ? "complete" : "blocked",
      detail: linkedThesisId
        ? "매수 이유, 유지 조건, 무효화 조건을 추적할 투자 논리가 연결됐다."
        : "투자 논리가 없으면 중장기 추천이나 보유 판단에 쓰면 안 된다.",
      source: "투자 논리",
      href: linkedThesisId ? thesisHref(linkedThesisId) : undefined,
      hrefLabel: linkedThesisId ? "투자 논리" : undefined,
    },
    {
      key: "recommendation",
      label: "추천 영향",
      status: data.recommendation ? "complete" : "missing",
      detail: data.recommendation
        ? `최신 추천 ${koCode(data.recommendation.action)}, 점수 ${formatPercent(data.recommendation.score)}가 연결됐다.`
        : "아직 이 종목을 대상으로 한 최신 추천 신호가 없다.",
      source: "추천 신호",
      href: data.recommendation ? recommendationHref(data.recommendation.recommendation_id) : undefined,
      hrefLabel: data.recommendation ? "추천 상세" : undefined,
    },
    {
      key: "paper_boundary",
      label: "가상 매매·실거래",
      status: guardrail.blocked ? "blocked" : data.recommendation ? "pending" : "missing",
      detail: guardrail.blocked
        ? "원천 근거가 차단되어 가상 매매 검증 입력도 차단한다. 실거래 주문은 계속 닫혀 있다."
        : data.recommendation
          ? "추천이 있어도 성과 측정창과 가상 매매 검증을 거치기 전에는 weight 변경과 실거래 주문으로 넘기지 않는다."
          : "추천 신호가 없으므로 가상 매매 검증 입력 대상도 아직 아니다.",
      source: "가상 매매와 주문 경계",
      href: "/paper-trading",
      hrefLabel: "가상 매매",
    },
    {
      key: "price_history",
      label: "가격 데이터",
      status: hasPriceData ? "complete" : "missing",
      detail: hasPriceData
        ? `가격 캔들 ${data.summary.bar_count}개가 수집됐다. 가격은 판단 보조 근거이며 주문을 만들지 않는다.`
        : "가격 캔들이 부족해 가격 흐름과 수익률 판단은 아직 제한된다.",
      source: "분석 기준 가격",
      href: "#stock-price-data",
      hrefLabel: "가격 차트",
    },
  ];
}
