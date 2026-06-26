import type { Route } from "next";

import { portfolioCopy } from "@/lib/presentation";
import type { TradingReadinessData } from "@/lib/types";

export function formatPaperPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "미측정";
  }
  return `${Math.round(value * 1000) / 10}%`;
}

export function formatPaperCurrency(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "가격 없음";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatBrokerCash(value: number | null | undefined, currencyCode: string) {
  if (value === null || value === undefined) {
    return `${currencyCode} 정보 없음`;
  }
  try {
    return new Intl.NumberFormat("ko-KR", {
      style: "currency",
      currency: currencyCode,
      maximumFractionDigits: currencyCode === "KRW" ? 0 : 2,
    }).format(value);
  } catch {
    return `${value.toLocaleString("ko-KR")} ${currencyCode}`;
  }
}

export function recordString(record: Record<string, unknown> | undefined, key: string) {
  const value = record?.[key];
  return typeof value === "string" ? value : "";
}

export function recordNumber(record: Record<string, unknown> | undefined, key: string) {
  const value = record?.[key];
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : null;
  }
  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

export function userFacingText(value: string | number | boolean | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "";
  }
  if (typeof value === "number") {
    return value.toLocaleString("ko-KR");
  }
  if (typeof value === "boolean") {
    return value ? "예" : "아니오";
  }
  return portfolioCopy(value)
    .replaceAll("broker", "증권사")
    .replaceAll("blocked", "차단")
    .replaceAll("pending", "대기")
    .replaceAll("approved", "허용")
    .replaceAll("drift", "벤치마크 괴리");
}

export function orderBoundaryLabel(value: string | null | undefined) {
  if (!value) {
    return "실거래 상태 미기록";
  }
  if (value === "read_only_no_order") {
    return "읽기 전용, 실거래 주문 차단";
  }
  return userFacingText(value);
}

export function riskClass(value: string) {
  if (value === "high") {
    return "risk-high";
  }
  if (value === "medium") {
    return "risk-medium";
  }
  return "risk-low";
}

export function recommendationHref(recommendationId: string | null) {
  return recommendationId ? (`/recommendations/${recommendationId}` as Route) : null;
}

export function thesisHref(thesisId: string | null) {
  return thesisId ? (`/theses/${thesisId}` as Route) : null;
}

export function paperValidationState(trading: TradingReadinessData) {
  if (trading.audit_summary.submitted_to_broker_count > 0) {
    return {
      title: "실제 주문 전송 기록 있음",
      tone: "risk-high",
      detail: "실제 주문 전송 기록이 있으므로 감사 기록과 계좌 내역을 먼저 대조해야 합니다.",
    };
  }
  if (trading.gate_summary.blocked_count > 0 || trading.paper_validation.blocked_reasons.length > 0) {
    return {
      title: "가상 매매 항목 있음 · 실제 주문 차단",
      tone: "risk-high",
      detail: "가상 매매 항목은 만들 수 있지만 안전 조건이 닫혀 있어 실제 주문으로 넘어가지 않습니다.",
    };
  }
  if (trading.paper_validation.approved_action_count > 0) {
    return {
      title: "가상 매매 검증 통과 항목 있음 · 실제 주문 금지",
      tone: "risk-medium",
      detail: "가상 매매 검증을 통과한 항목이 있어도 실거래는 닫혀 있습니다. 거래 안전 승인, 증권사 연결, 계좌 권한, 주문 한도, 감사 기록이 모두 필요합니다.",
    };
  }
  return {
    title: "가상 매매 항목 대기 · 실제 주문 없음",
    tone: "risk-medium",
    detail: "추천 신호와 현재 보유 내역이 맞물릴 때 가상 매매 항목이 생성됩니다.",
  };
}
