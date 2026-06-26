import { koCode } from "@/lib/korean-labels";
import { stockCopy } from "@/lib/presentation";
import type { StockDetailData } from "@/lib/types";

type FinancialStatementModel = StockDetailData["financial_statement_model"];
type FinancialMetricSnapshot = FinancialStatementModel["metrics"][number];

const sourceLabels: Record<string, string> = {
  companyfacts_financial_statement_model: "SEC 재무제표 정규화",
  sec_companyfacts: "SEC 재무 원천",
  static_source_blocker_classification: "원천 한계 분류",
};

const fundStatusLabels: Record<string, string> = {
  available: "사용 가능",
  collected: "수집 완료",
  stale: "오래된 자료",
  missing: "자료 없음",
};

export function stockText(value: string | null | undefined) {
  return stockCopy(value);
}

export function stockSourceLabel(value: string | null | undefined) {
  if (!value) {
    return "원천 정보 없음";
  }
  return sourceLabels[value] ?? stockText(koCode(value));
}

export function fundStatusLabel(value: string) {
  return fundStatusLabels[value] ?? stockText(koCode(value));
}

export function formatCurrency(value: number | null | undefined, currencyCode: string) {
  if (value === null || value === undefined) {
    return "가격 자료 없음";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: currencyCode,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatCompactNumber(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "자료 없음";
  }
  return new Intl.NumberFormat("ko-KR", {
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "측정 전";
  }
  return `${Math.round(value * 1000) / 10}%`;
}

export function formatFinancialMetricValue(metric: FinancialMetricSnapshot) {
  if (metric.metric_value === null) {
    if (metric.metric_status === "insufficient_history") {
      return "비교 기간 부족";
    }
    return "원천 데이터 부족";
  }
  if (metric.metric_unit === "ratio") {
    return formatPercent(metric.metric_value);
  }
  return formatCompactNumber(metric.metric_value);
}

export function financialMetricTone(metric: FinancialMetricSnapshot) {
  if (metric.metric_status !== "computed" || metric.metric_value === null) {
    return "risk-medium";
  }
  if (metric.polarity === "lower_is_better") {
    return metric.metric_value <= 0.35 ? "risk-low" : metric.metric_value <= 0.75 ? "risk-medium" : "risk-high";
  }
  if (metric.polarity === "higher_is_better") {
    return metric.metric_value >= 0.2 ? "risk-low" : metric.metric_value >= 0 ? "risk-medium" : "risk-high";
  }
  return "risk-medium";
}
