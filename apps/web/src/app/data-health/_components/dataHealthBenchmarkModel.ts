import type { BenchmarkDriftQuality } from "./dataHealthTypes";

import { koCode } from "@/lib/korean-labels";

import { statusRiskClass } from "./dataHealthCopyModel";

export function benchmarkDriftQualityTitle(quality: BenchmarkDriftQuality) {
  if (quality.status === "ok") {
    return "벤치마크 구성 신뢰 가능";
  }
  if (!quality.attention_required && quality.status === "drift_outlier_review") {
    return "큰 괴리 검토 관리 중";
  }
  if (quality.status === "partial_composition") {
    return "부분 구성비로만 계산됨";
  }
  if (quality.status === "stale_composition") {
    return "구성 기준일 오래됨";
  }
  if (quality.status === "missing_benchmark_composition") {
    return "벤치마크 구성비 없음";
  }
  if (quality.status === "drift_outlier_review") {
    return "큰 괴리 종목 있음";
  }
  if (quality.status === "missing_guardrail") {
    return "위험 예산 평가 없음";
  }
  return koCode(quality.status);
}

export function benchmarkDriftQualityExplanation(quality: BenchmarkDriftQuality) {
  if (quality.status === "ok") {
    return "구성비 확인률과 기준일이 충분해 벤치마크 대비 괴리를 보조 위험 지표로 볼 수 있다. 추천 산식 반영 비중은 자동 변경하지 않는다.";
  }
  if (!quality.attention_required && quality.status === "drift_outlier_review") {
    return quality.managed_review_reason || "큰 벤치마크 괴리는 검토 후보로 저장됐고 자동 주문 없이 성과 관찰을 기다린다.";
  }
  if (quality.status === "partial_composition") {
    return "현재 벤치마크 보유종목 일부만 들어와 있다. 괴리 숫자는 계산됐지만 전체 SPY 대비 괴리로 해석하면 안 된다.";
  }
  if (quality.status === "stale_composition") {
    return "벤치마크 구성 기준일이 오래되어 최신 지수 구성과 다를 수 있다. holdings 파일을 다시 적재해야 한다.";
  }
  if (quality.status === "missing_benchmark_composition") {
    return "벤치마크 구성비가 없어 포트폴리오가 SPY와 얼마나 다른지 계산하지 못했다.";
  }
  if (quality.status === "drift_outlier_review") {
    return "벤치마크 대비 전체 괴리 또는 개별 종목 괴리가 커서 포트폴리오 위험 예산 검토가 필요하다.";
  }
  if (quality.status === "missing_guardrail") {
    return "위험 예산 평가가 아직 없어 벤치마크 괴리 품질도 판단할 수 없다.";
  }
  return "벤치마크 괴리 품질 상태 확인이 필요합니다.";
}

export function benchmarkDriftQualityTone(quality: BenchmarkDriftQuality) {
  if (!quality.attention_required && quality.status === "drift_outlier_review") {
    return "risk-medium";
  }
  if (quality.status === "ok") {
    return "risk-low";
  }
  if (quality.status === "partial_composition" || quality.status === "stale_composition") {
    return "risk-medium";
  }
  return "risk-high";
}

export function decisionSeverityClass(severity: string) {
  if (severity === "high") {
    return "risk-high";
  }
  if (severity === "medium") {
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
  if (
    status === "insufficient_history"
    || status === "collect_more_feedback"
    || status === "missing"
  ) {
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
