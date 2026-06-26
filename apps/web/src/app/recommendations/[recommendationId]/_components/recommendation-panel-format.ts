import { koCode } from "@/lib/korean-labels";
import { recommendationCopy } from "@/lib/presentation";

export function userFacingRecommendationText(value: string | number | boolean | null | undefined) {
  return recommendationCopy(value);
}

export function formatPanelPercent(value: number) {
  return `${(value * 100).toLocaleString("ko-KR", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}%`;
}

export function formatPanelOptionalPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "미측정";
  }
  return formatPanelPercent(value);
}

export function formatPanelCompactNumber(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "없음";
  }
  return new Intl.NumberFormat("ko-KR", {
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatPanelCurrency(value: number | null | undefined, currencyCode: string) {
  if (value === null || value === undefined) {
    return "데이터 없음";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: currencyCode,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatPanelFundCurrency(value: number | null | undefined, currencyCode: string) {
  if (value === null || value === undefined) {
    return "가격 자료 없음";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: currencyCode,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatPanelExpenseRatio(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "비용률 자료 없음";
  }
  return `${(value * 100).toLocaleString("ko-KR", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 4,
  })}%`;
}

export function fundPanelStatusLabel(status: string) {
  if (status === "collected" || status === "available") {
    return "수집 완료";
  }
  if (status === "missing") {
    return "데이터 없음";
  }
  if (status === "stale") {
    return "오래된 자료";
  }
  return koCode(status);
}

export function recommendationPanelOrderBoundaryLabel(value: string | null | undefined) {
  if (!value) {
    return "실거래 상태 미기록";
  }
  if (value === "read_only_no_order") {
    return "읽기 전용, 실거래 주문 차단";
  }
  return userFacingRecommendationText(value);
}
