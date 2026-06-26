import type { StockDetailData } from "../types";

import { stockCopy } from "./investment-copy";
import { formatSignedPercent } from "./returns";
import type { InvestmentViewModel } from "./view-model";

export type StockProductKind = "company_stock" | "fund_or_etf";

export function stockProductKind(data: Pick<StockDetailData, "fund_instrument_analysis" | "professional_source_guardrail">): StockProductKind {
  if (data.fund_instrument_analysis || data.professional_source_guardrail.status === "fund_or_etf_company_model_not_applicable") {
    return "fund_or_etf";
  }
  return "company_stock";
}

export function stockProductLabel(kind: StockProductKind): string {
  if (kind === "fund_or_etf") {
    return "ETF·펀드";
  }
  return "개별 회사 주식";
}

export function latestDailyChangePct(data: Pick<StockDetailData, "price_bars">): number | null {
  const latestBars = [...data.price_bars]
    .filter((bar) => bar.adjusted_close !== null)
    .sort((left, right) => right.trade_date.localeCompare(left.trade_date));
  const latestClose = latestBars[0]?.adjusted_close ?? null;
  const previousClose = latestBars[1]?.adjusted_close ?? null;
  if (latestClose === null || previousClose === null || previousClose === 0) {
    return null;
  }
  return (latestClose - previousClose) / previousClose;
}

export function buildStockViewModel(data: StockDetailData): InvestmentViewModel {
  const kind = stockProductKind(data);
  const move = formatSignedPercent(latestDailyChangePct(data));
  const held = data.position && data.position.quantity !== null && data.position.quantity !== 0;
  const sourceBlocked = data.professional_source_guardrail.blocked;
  const latestPrice = data.latest_price.close;

  return {
    title: `${data.symbol} ${stockProductLabel(kind)} 리서치`,
    summary: `${data.name} · ${move.a11yLabel} · ${held ? "보유 중" : "미보유"}`,
    statusLabel: sourceBlocked ? "원천 근거 제한" : data.recommendation ? "추천 근거 있음" : "추천 없음",
    statusTone: sourceBlocked ? "source_limited" : data.recommendation ? "ready" : "watch",
    investmentImpact:
      kind === "fund_or_etf"
        ? "구성종목, 추적 지표, 비용, NAV 괴리, 유동성과 시장 노출을 분리해 표시합니다."
        : "사업, 재무, 밸류에이션, 피어, 뉴스, 사이클, thesis를 한 화면에 정리합니다.",
    nextAction: data.recommendation
      ? "연결된 추천 상세에 실행 차단 사유와 가상 검증 상태가 이어집니다."
      : "추천이 없으면 가격 흐름과 원천 근거의 충분성이 우선입니다.",
    sourceLimitReason: sourceBlocked
      ? stockCopy(data.professional_source_guardrail.blocker_code)
      : "분석 기준 데이터와 브로커 참고 데이터의 역할을 분리해 표시합니다.",
    metrics: [
      { label: "전일 대비", value: move.label, context: move.a11yLabel },
      { label: "현재 가격", value: latestPrice === null ? "가격 없음" : latestPrice.toLocaleString("ko-KR"), context: data.currency_code },
      { label: "보유 상태", value: held ? "보유 중" : "미보유", context: data.position?.portfolio_name ?? "포트폴리오 미연결" },
      { label: "상품 유형", value: stockProductLabel(kind), context: "분석 레이아웃 분기 기준" },
    ],
  };
}
