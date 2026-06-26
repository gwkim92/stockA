import { portfolioCopy } from "@/lib/presentation";

export function formatCoveragePercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "미측정";
  }
  return `${Math.round(value * 1000) / 10}%`;
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
  return portfolioCopy(value);
}

export function recordPresent(value: string | null | undefined) {
  return value ? "기록 있음" : "기록 없음";
}

export function orderBoundaryLabel(value: string | null | undefined) {
  if (!value) {
    return "실거래 상태 미기록";
  }
  if (value === "read_only_no_order") {
    return "주문 차단";
  }
  return userFacingText(value);
}

export function riskBudgetLabel(status: string) {
  if (status === "within_budget") {
    return "한도 내";
  }
  if (status === "needs_position_review") {
    return "비중 점검 필요";
  }
  if (status === "missing_position_snapshot") {
    return "스냅샷 없음";
  }
  return userFacingText(status);
}

export function concentrationStatusLabel(status: string) {
  if (status === "within_budget") {
    return "집중도 한도 내";
  }
  if (status === "needs_concentration_review") {
    return "집중도 점검 필요";
  }
  if (status === "classification_gap") {
    return "분류 보강 필요";
  }
  if (status === "missing_position_snapshot") {
    return "스냅샷 없음";
  }
  return userFacingText(status);
}

export function concentrationStatusClass(status: string) {
  if (status === "needs_concentration_review") {
    return "risk-high";
  }
  if (status === "classification_gap" || status === "missing_position_snapshot") {
    return "risk-medium";
  }
  return "risk-low";
}

export function exposureStatusLabel(status: string) {
  if (status === "over_limit") {
    return "한도 초과";
  }
  if (status === "within_limit") {
    return "한도 내";
  }
  return userFacingText(status);
}

export function candidateSeverityClass(severity: string) {
  if (severity === "high") {
    return "risk-high";
  }
  if (severity === "medium") {
    return "risk-medium";
  }
  return "risk-low";
}

export function candidateDirectionLabel(direction: string) {
  if (direction === "overweight") {
    return "과대 보유";
  }
  if (direction === "underweight") {
    return "과소 보유";
  }
  return userFacingText(direction);
}

export function sizingBandClass(reviewBand: string) {
  if (reviewBand === "reduce_review") {
    return "risk-high";
  }
  if (reviewBand === "add_blocked_until_evidence") {
    return "risk-medium";
  }
  return "risk-low";
}

export function feedbackStatusClass(status: string) {
  if (status === "has_contradictions" || status === "contradicted") {
    return "risk-high";
  }
  if (status === "needs_more_data" || status === "too_early" || status === "missing" || status === "missing_history") {
    return "risk-medium";
  }
  return "risk-low";
}

export function calibrationStatusClass(status: string) {
  if (status === "contradiction_review_required") {
    return "risk-high";
  }
  if (status === "insufficient_history" || status === "collect_more_feedback" || status === "missing") {
    return "risk-medium";
  }
  return "risk-low";
}

export function cadenceStatusClass(status: string) {
  if (status === "missing_evidence_review_required") {
    return "risk-high";
  }
  if (status === "run_feedback_now" || status === "run_calibration_now" || status === "missing") {
    return "risk-medium";
  }
  return "risk-low";
}

export function actionRouterStatusClass(status: string) {
  if (status.startsWith("blocked_")) {
    return "risk-high";
  }
  if (status === "missing" || status.endsWith("_ready")) {
    return "risk-medium";
  }
  return "risk-low";
}

export function actionRouterLabel(status: string, executed: boolean, routeAction: string) {
  if (executed) {
    return routeAction === "execute_calibration" ? "누적평가 실행됨" : "사후평가 실행됨";
  }
  if (status === "no_op_wait_for_outcome_window") {
    return "성과 관찰 기간 대기";
  }
  if (status.startsWith("blocked_")) {
    return "가드레일 차단";
  }
  return userFacingText(status);
}

export function orderSubmitLabel(allowed: boolean) {
  return `실거래 주문 ${allowed ? "허용" : "금지"}`;
}

export function formatScore(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "없음";
  }
  return `${Math.round(value * 100)}점`;
}
