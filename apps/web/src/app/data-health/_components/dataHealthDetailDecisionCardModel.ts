import { koCode } from "@/lib/korean-labels";

import type { DataHealthDetailDecisionCard } from "./DataHealthDetailDecisionCardsSection";
import {
  buildPortfolioReviewCadenceCard,
  buildPortfolioReviewCalibrationCard,
  buildPortfolioReviewFeedbackCard,
  buildPortfolioReviewHistoryCard,
} from "./dataHealthDetailPortfolioCardModel";
import {
  actionRouterStatusClass,
  actionRouterTitle,
  benchmarkDriftQualityExplanation,
  benchmarkDriftQualityTitle,
  benchmarkDriftQualityTone,
  formatPercent,
  liveAiInvocationExplanation,
  liveAiInvocationTitle,
  liveAiInvocationTone,
  openAiProviderExplanation,
  openAiProviderTitle,
  openAiProviderTone,
  operationCopy,
  outcomeCalibrationExplanation,
  outcomeCalibrationTitle,
  outcomeCalibrationTone,
  outcomeDueActionRouterTitle,
  professionalDepthTitle,
  professionalDepthTone,
  professionalNextActionTone,
  professionalQualityTone,
  professionalRecommendationAuditTone,
  professionalSourceGapExplanation,
  professionalSourceGapTitle,
  professionalSourceGapTone,
} from "./dataHealthModel";
import type {
  BenchmarkDriftQuality,
  LiveAiInvocationHealth,
  OpenAiProviderHealth,
  PortfolioReviewDecisionFeedback,
  PortfolioReviewDecisionHistory,
  PortfolioReviewFeedbackActionRouter,
  PortfolioReviewFeedbackCadence,
  PortfolioReviewFeedbackCalibration,
  ProfessionalAnalysisDepth,
  ProfessionalAnalysisNextAction,
  ProfessionalAnalysisQuality,
  ProfessionalRecommendationCoverageAudit,
  ProfessionalSourceGapPrioritization,
  RecommendationOutcomeCalibration,
  RecommendationOutcomeDueActionRouter,
  TossInvestMarketData,
} from "./dataHealthTypes";

type DataHealthDetailDecisionCardInput = {
  readonly benchmarkDriftQuality: BenchmarkDriftQuality;
  readonly liveAiInvocationHealth: LiveAiInvocationHealth;
  readonly openAiProviderHealth: OpenAiProviderHealth;
  readonly outcomeCalibration: RecommendationOutcomeCalibration;
  readonly outcomeDueActionRouter: RecommendationOutcomeDueActionRouter;
  readonly portfolioReviewActionRouter: PortfolioReviewFeedbackActionRouter;
  readonly portfolioReviewCadence: PortfolioReviewFeedbackCadence;
  readonly portfolioReviewCalibration: PortfolioReviewFeedbackCalibration;
  readonly portfolioReviewFeedback: PortfolioReviewDecisionFeedback;
  readonly portfolioReviewHistory: PortfolioReviewDecisionHistory;
  readonly professionalDepth: ProfessionalAnalysisDepth;
  readonly professionalNextAction: ProfessionalAnalysisNextAction;
  readonly professionalQuality: ProfessionalAnalysisQuality;
  readonly professionalRecommendationAudit: ProfessionalRecommendationCoverageAudit;
  readonly professionalSourceGaps: ProfessionalSourceGapPrioritization;
  readonly tossMarketData: TossInvestMarketData;
};

export function buildDataHealthDetailDecisionCards({
  benchmarkDriftQuality,
  liveAiInvocationHealth,
  openAiProviderHealth,
  outcomeCalibration,
  outcomeDueActionRouter,
  portfolioReviewActionRouter,
  portfolioReviewCadence,
  portfolioReviewCalibration,
  portfolioReviewFeedback,
  portfolioReviewHistory,
  professionalDepth,
  professionalNextAction,
  professionalQuality,
  professionalRecommendationAudit,
  professionalSourceGaps,
  tossMarketData,
}: DataHealthDetailDecisionCardInput): readonly DataHealthDetailDecisionCard[] {
  return [
    {
      body: `토스증권 데이터는 브로커 현실 확인용이다. 분석 기준 가격 대체 전 검증 상태는 ${koCode(tossMarketData.provider_comparison.status)}이고 실주문은 차단된다.`,
      cta: "토스 데이터 보기",
      href: "#toss-market-data",
      label: "토스증권 데이터",
      title: tossMarketData.sync.status === "succeeded"
        ? `캔들 ${tossMarketData.sync.candle_bar_count.toLocaleString("ko-KR")}개`
        : koCode(tossMarketData.sync.status),
      tone: tossMarketData.sync.attention_required ? "risk-medium" : "risk-low",
    },
    {
      body: liveAiInvocationExplanation(liveAiInvocationHealth),
      cta: "실제 호출 보기",
      href: "#live-ai-invocation-health",
      label: "실제 AI 호출",
      title: liveAiInvocationTitle(liveAiInvocationHealth),
      tone: liveAiInvocationTone(liveAiInvocationHealth),
    },
    {
      body: openAiProviderExplanation(openAiProviderHealth),
      cta: "잔액·예비 경로 보기",
      href: "#openai-provider-health",
      label: "OpenAI 잔액",
      title: openAiProviderTitle(openAiProviderHealth),
      tone: openAiProviderTone(openAiProviderHealth),
    },
    {
      body: benchmarkDriftQualityExplanation(benchmarkDriftQuality),
      cta: "벤치마크 품질 보기",
      href: "#benchmark-drift-quality",
      label: "벤치마크 괴리",
      title: benchmarkDriftQualityTitle(benchmarkDriftQuality),
      tone: benchmarkDriftQualityTone(benchmarkDriftQuality),
    },
    buildPortfolioReviewHistoryCard(portfolioReviewHistory),
    buildPortfolioReviewFeedbackCard(portfolioReviewFeedback),
    buildPortfolioReviewCalibrationCard(portfolioReviewCalibration),
    buildPortfolioReviewCadenceCard(portfolioReviewCadence),
    {
      body: portfolioReviewActionRouter.status === "loaded"
        ? operationCopy(portfolioReviewActionRouter.reason)
        : "실행 주기 판단을 실제 사후평가/누적평가 실행 또는 대기로 변환한 기록이 아직 없다.",
      cta: "라우터 판단 보기",
      href: "#portfolio-review-action-router",
      label: "검토 실행 라우터",
      title: actionRouterTitle(portfolioReviewActionRouter),
      tone: actionRouterStatusClass(portfolioReviewActionRouter.action_status),
    },
    {
      body: outcomeCalibrationExplanation(outcomeCalibration),
      cta: "표본 상태 보기",
      href: "#outcome-calibration",
      label: "성과검증",
      title: outcomeCalibrationTitle(outcomeCalibration),
      tone: outcomeCalibrationTone(outcomeCalibration),
    },
    {
      body: outcomeDueActionRouter.status === "loaded"
        ? operationCopy(outcomeDueActionRouter.reason)
        : "성과 측정창 상태를 실제 누적평가 실행 또는 대기로 변환한 기록이 아직 없다.",
      cta: "라우터 보기",
      href: "#outcome-calibration",
      label: "성과 실행 라우터",
      title: outcomeDueActionRouterTitle(outcomeDueActionRouter),
      tone: actionRouterStatusClass(outcomeDueActionRouter.action_status),
    },
    {
      body: professionalSourceGapExplanation(professionalSourceGaps),
      cta: "소스 공백 보기",
      href: "#professional-source-gaps",
      label: "전문 분석 소스",
      title: professionalSourceGapTitle(professionalSourceGaps),
      tone: professionalSourceGapTone(professionalSourceGaps),
    },
    {
      body: operationCopy(professionalQuality.summary),
      cta: "품질 판정 보기",
      href: "#professional-analysis-quality",
      label: "전문 분석 품질",
      title: professionalQuality.title,
      tone: professionalQualityTone(professionalQuality),
    },
    {
      body: operationCopy(professionalRecommendationAudit.summary),
      cta: "추천별 감사 보기",
      href: "#professional-recommendation-coverage-audit",
      label: "추천별 전문 감사",
      title: professionalRecommendationAudit.title,
      tone: professionalRecommendationAuditTone(professionalRecommendationAudit),
    },
    {
      body: operationCopy(professionalNextAction.summary),
      cta: "다음 행동 보기",
      href: "#professional-next-action",
      label: "전문 분석 다음 행동",
      title: professionalNextAction.title,
      tone: professionalNextActionTone(professionalNextAction),
    },
    {
      body: `활성 후보 ${professionalDepth.active_candidate_count}개 중 ${professionalDepth.complete_candidate_count}개가 필요한 전문 분석 근거를 채웠고, 평균 연결률은 ${formatPercent(professionalDepth.average_coverage_ratio)}이다.`,
      cta: "깊이 보기",
      href: "#professional-analysis-depth",
      label: "전문 분석 깊이",
      title: professionalDepthTitle(professionalDepth),
      tone: professionalDepthTone(professionalDepth),
    },
  ];
}
