import type { DataHealthDetailDecisionCard } from "./DataHealthDetailDecisionCardsSection";
import { cadenceStatusClass, calibrationStatusClass, operationCopy } from "./dataHealthModel";
import type {
  PortfolioReviewDecisionFeedback,
  PortfolioReviewDecisionHistory,
  PortfolioReviewFeedbackCadence,
  PortfolioReviewFeedbackCalibration,
} from "./dataHealthTypes";

export function buildPortfolioReviewHistoryCard(
  portfolioReviewHistory: PortfolioReviewDecisionHistory,
): DataHealthDetailDecisionCard {
  return {
    body: portfolioReviewHistory.status === "loaded"
      ? portfolioReviewHistory.attention_required
        ? `최신 ${portfolioReviewHistory.as_of_date} 기준으로 벤치마크 ${portfolioReviewHistory.benchmark_decision_count}개, 포지션 크기 ${portfolioReviewHistory.position_sizing_decision_count}개 결정을 감사 이력으로 남겼다.`
        : operationCopy(portfolioReviewHistory.managed_review_reason)
      : "현재 화면의 검토 후보는 보이지만 저장된 검토 이력으로는 아직 남지 않았다.",
    cta: "검토 이력 보기",
    href: "#portfolio-review-history",
    label: "포트폴리오 검토 이력",
    title: portfolioReviewHistory.status === "loaded"
      ? portfolioReviewHistory.attention_required
        ? `${portfolioReviewHistory.decision_count}개 결정 저장됨`
        : "검토 이력 관리 중"
      : "검토 결정 이력 없음",
    tone: portfolioReviewHistory.attention_required ? "risk-medium" : "risk-low",
  };
}

export function buildPortfolioReviewFeedbackCard(
  portfolioReviewFeedback: PortfolioReviewDecisionFeedback,
): DataHealthDetailDecisionCard {
  return {
    body: portfolioReviewFeedback.status === "loaded"
      ? `저장된 검토 결정 ${portfolioReviewFeedback.decision_count}개를 후속 성과, 가상 매매 검증, 가격 변화와 대조했다.`
      : "검토 결정 이력은 저장됐지만 아직 이후 성과와 대조한 사후평가 기록이 없다.",
    cta: "사후평가 보기",
    href: "#portfolio-review-feedback",
    label: "검토 사후평가",
    title: portfolioReviewFeedback.status === "loaded"
      ? `${portfolioReviewFeedback.validated_count}개 검증 · ${portfolioReviewFeedback.contradicted_count}개 반박`
      : "사후평가 없음",
    tone: portfolioReviewFeedback.feedback_status === "has_contradictions"
      ? "risk-high"
      : portfolioReviewFeedback.feedback_status === "needs_more_data"
        ? "risk-medium"
        : "risk-low",
  };
}

export function buildPortfolioReviewCalibrationCard(
  portfolioReviewCalibration: PortfolioReviewFeedbackCalibration,
): DataHealthDetailDecisionCard {
  return {
    body: portfolioReviewCalibration.status === "loaded"
      ? `성숙 표본 ${portfolioReviewCalibration.mature_decision_count}/${portfolioReviewCalibration.min_mature_decisions}개, 사후평가 ${portfolioReviewCalibration.feedback_run_count}/${portfolioReviewCalibration.min_feedback_runs}회. ${portfolioReviewCalibration.estimated_maturity_date ? `예상 성숙일은 ${portfolioReviewCalibration.estimated_maturity_date}이다.` : operationCopy(portfolioReviewCalibration.weight_review_block_reason)}`
      : "단일 사후평가만으로 추천 산식 반영 비중을 바꾸지 않기 위해 누적평가가 필요하다.",
    cta: "신뢰도 보기",
    href: "#portfolio-review-calibration",
    label: "검토 신뢰도",
    title: portfolioReviewCalibration.status === "loaded"
      ? portfolioReviewCalibration.managed_wait
        ? "관리된 대기"
        : portfolioReviewCalibration.weight_review_blocked
          ? "추천 산식 변경 금지"
          : "성과 표본 충족"
      : "누적평가 없음",
    tone: portfolioReviewCalibration.managed_wait
      ? "risk-low"
      : calibrationStatusClass(portfolioReviewCalibration.calibration_status),
  };
}

export function buildPortfolioReviewCadenceCard(
  portfolioReviewCadence: PortfolioReviewFeedbackCadence,
): DataHealthDetailDecisionCard {
  return {
    body: portfolioReviewCadence.status === "loaded"
      ? operationCopy(portfolioReviewCadence.reason)
      : "사후평가와 누적평가를 언제 다시 돌릴지 아직 계산되지 않았다.",
    cta: "실행시점 보기",
    href: "#portfolio-review-cadence",
    label: "검토 실행시점",
    title: portfolioReviewCadence.should_run_now
      ? "지금 실행 필요"
      : portfolioReviewCadence.should_wait
        ? "대기"
        : "상태 확인",
    tone: cadenceStatusClass(portfolioReviewCadence.cadence_status),
  };
}
