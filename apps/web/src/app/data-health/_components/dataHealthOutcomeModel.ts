import type {
  OutcomeMaturityWaitMonitor,
  PortfolioReviewFeedbackActionRouter,
  RecommendationOutcomeCalibration,
  RecommendationOutcomeDueActionRouter,
  RecommendationOutcomeMaturity,
} from "./dataHealthTypes";

import { koCode } from "@/lib/korean-labels";

import { statusRiskClass } from "./dataHealthCopyModel";

export function actionRouterTitle(router: PortfolioReviewFeedbackActionRouter) {
  if (router.child_runner.executed) {
    return router.route_action === "execute_calibration" ? "누적평가 실행됨" : "사후평가 실행됨";
  }
  if (router.action_status.startsWith("blocked_")) {
    return "가드레일 차단";
  }
  if (router.action_status === "no_op_wait_for_outcome_window") {
    return "성과 관찰 기간 대기";
  }
  if (router.action_status === "no_op_calibration_current") {
    return "최신 평가 유지";
  }
  return koCode(router.action_status);
}

export function outcomeCalibrationTitle(calibration: RecommendationOutcomeCalibration) {
  if (calibration.status === "ready_for_manual_weight_review") {
    return "성과 표본 충족";
  }
  if (calibration.status === "collect_more_outcomes_keep_weights") {
    return "성과 표본 축적 중";
  }
  if (calibration.status === "backfill_candidates_remain") {
    return "성과 산출 후보 남음";
  }
  if (calibration.status === "price_history_gaps_remain") {
    return "가격 이력 보강 필요";
  }
  if (calibration.status === "no_due_outcome_window") {
    return "성과 측정일 대기";
  }
  if (calibration.status === "missing") {
    return "성과 보정 결과 없음";
  }
  return koCode(calibration.status);
}

export function outcomeCalibrationExplanation(calibration: RecommendationOutcomeCalibration) {
  if (calibration.status === "ready_for_manual_weight_review") {
    return "성과 표본과 전문 분석 근거 연결률 기준을 통과했다. 그래도 자동 추천 산식 변경은 금지이고 별도 검토 작업이 필요하다.";
  }
  if (calibration.status === "collect_more_outcomes_keep_weights") {
    return "성과 표본은 있지만 추천 산식 반영 비중을 바꾸기에는 아직 더 많은 성과와 부진 사례가 필요하다.";
  }
  if (calibration.status === "backfill_candidates_remain") {
    return "이미 수집된 가격 이력으로 성과를 더 산출할 수 있다. 추천 품질 평가 전에 성과 보강 작업을 다시 실행해야 한다.";
  }
  if (calibration.status === "price_history_gaps_remain") {
    return "성과를 계산해야 할 추천은 있지만 entry/exit 가격 이력이 부족하다. 캔들 보강이 먼저다.";
  }
  if (calibration.status === "no_due_outcome_window") {
    return "선택한 중장기 기간의 성과 측정일이 아직 오지 않았다. 추천 산식 반영 비중은 그대로 두고 표본이 쌓일 때까지 기다린다.";
  }
  if (calibration.status === "missing") {
    return "추천 성과 표본과 컴포넌트 보정 진단이 아직 생성되지 않았다.";
  }
  return "추천 성과 보정 상태 확인이 필요합니다.";
}

export function outcomeCalibrationTone(calibration: RecommendationOutcomeCalibration) {
  if (calibration.status === "ready_for_manual_weight_review") {
    return "risk-low";
  }
  if (calibration.status === "collect_more_outcomes_keep_weights") {
    return "risk-medium";
  }
  return "risk-high";
}

export function outcomeMaturityTitle(maturity: RecommendationOutcomeMaturity) {
  if (maturity.status === "not_due") {
    return "성과 측정일 대기";
  }
  if (maturity.status === "due_outcomes_ready") {
    return "성과 산출 가능";
  }
  if (maturity.status === "overdue_outcomes_ready") {
    return "성과 산출 지연";
  }
  if (maturity.status === "blocked_by_price_gaps") {
    return "가격 이력 보강 필요";
  }
  if (maturity.status === "complete_current_window") {
    return "현재 창 측정 완료";
  }
  return koCode(maturity.status);
}

export function outcomeMaturityExplanation(maturity: RecommendationOutcomeMaturity) {
  if (maturity.status === "not_due") {
    return maturity.next_due_date
      ? `${maturity.next_due_date}에 ${maturity.next_due_count}개 추천×기간 성과 측정창이 처음 열린다. 그 전까지 추천 산식 검토는 대기한다.`
      : "아직 성과 측정 가능한 추천×기간이 없다. 추천 산식 검토는 대기한다.";
  }
  if (maturity.status === "due_outcomes_ready") {
    return `${maturity.ready_for_backfill_count}개 추천×기간 성과를 산출할 수 있다. 성과 보강과 누적평가를 먼저 실행해야 한다.`;
  }
  if (maturity.status === "overdue_outcomes_ready") {
    return `${maturity.overdue_count}개 추천×기간 성과 산출이 지연됐다. 추천 산식 검토 전에 성과 보강을 실행해야 한다.`;
  }
  if (maturity.status === "blocked_by_price_gaps") {
    return `${maturity.price_gap_count}개 추천×기간은 가격 이력 부족으로 성과 계산이 막혔다. 캔들 보강이 먼저다.`;
  }
  if (maturity.status === "complete_current_window") {
    return "현재 측정 가능한 성과창은 모두 처리됐다. 다음 측정일 전까지 추천 산식 변경은 하지 않는다.";
  }
  return "추천 성과 측정창 상태를 본다.";
}

export function outcomeMaturityTone(maturity: RecommendationOutcomeMaturity) {
  if (maturity.status === "not_due" || maturity.status === "complete_current_window") {
    return "risk-medium";
  }
  if (maturity.status === "due_outcomes_ready") {
    return "risk-medium";
  }
  return "risk-high";
}

export function outcomeDueActionRouterTitle(router: RecommendationOutcomeDueActionRouter) {
  if (router.child_runner.executed) {
    return "성과 보정 실행됨";
  }
  if (router.action_status === "execute_outcome_calibration_ready") {
    return "성과 보정 실행 대기";
  }
  if (router.action_status === "blocked_by_price_gaps") {
    return "가격 이력 때문에 차단";
  }
  if (router.action_status === "no_op_wait_until_next_due_date") {
    return "다음 측정일까지 대기";
  }
  if (router.action_status === "no_op_current_window_complete") {
    return "현재 측정창 처리 완료";
  }
  if (router.action_status.startsWith("blocked_")) {
    return "가드레일 차단";
  }
  return koCode(router.action_status);
}

export function outcomeWaitMonitorTone(monitor: OutcomeMaturityWaitMonitor) {
  if (monitor.status === "action_due" || monitor.status === "blocked_or_missing_evidence") {
    return "risk-high";
  }
  if (monitor.status === "manual_weight_review_possible") {
    return "risk-low";
  }
  return "risk-medium";
}
