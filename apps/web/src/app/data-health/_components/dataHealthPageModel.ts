import type { DataHealthTriageBucket } from "@/components/operations/DataHealthOverview";
import type { PageDecisionMapProps } from "@/components/research/PageDecisionMap";
import { koCode } from "@/lib/korean-labels";
import { buildOperationsViewModel } from "@/lib/presentation";

import {
  buildDataHealthDataGapCards,
  buildDataHealthDecisionFlowCards,
} from "./DataHealthDecisionFlowModel";
import { buildDataHealthAutomationDetailSection } from "./dataHealthAutomationDetailModel";
import { buildDataHealthOverviewCollectionCards } from "./dataHealthCollectionStatusModel";
import { buildDataHealthDetailDecisionCards } from "./dataHealthDetailDecisionCardModel";
import { buildDataHealthExecutionHistoryRows } from "./dataHealthExecutionHistoryModel";
import {
  buildDataHealthCommandCards,
  buildDataHealthHeadline,
  buildDataHealthMetaItems,
} from "./dataHealthOverviewCardModel";
import { buildDataHealthRuntimeDetailPanels } from "./dataHealthRuntimeDetailPanelModel";
import {
  liveAiInvocationTitle,
  runStateLabel,
  qualityAuditSampleGroups,
} from "./dataHealthModel";
import { buildDataHealthPageState } from "./dataHealthPageStateModel";
import {
  buildDataHealthDecisionMapSteps,
  buildDataHealthOpenGateChips,
  buildDataHealthTossBrokerSection,
  buildDataHealthTriageOverviewBuckets,
  type DataHealthTossBrokerSectionModel,
} from "./dataHealthPageSupportModel";
import type { DataHealthData } from "./dataHealthTypes";

export type DataHealthPageModel = {
  readonly automationDetailSection: ReturnType<typeof buildDataHealthAutomationDetailSection>;
  readonly commandCenterCards: ReturnType<typeof buildDataHealthCommandCards>;
  readonly data: DataHealthData;
  readonly dataGapCards: ReturnType<typeof buildDataHealthDataGapCards>;
  readonly dataHealthHeadline: string;
  readonly dataHealthMetaItems: readonly string[];
  readonly decisionFlowCards: ReturnType<typeof buildDataHealthDecisionFlowCards>;
  readonly decisionMap: PageDecisionMapProps;
  readonly detailDecisionCards: ReturnType<typeof buildDataHealthDetailDecisionCards>;
  readonly ec2SchedulerInstalled: boolean;
  readonly executionHistoryRows: ReturnType<typeof buildDataHealthExecutionHistoryRows>;
  readonly gateTriageStatus: string;
  readonly headerDescription: string;
  readonly headerTitle: string;
  readonly liveAiInvocationHealth: NonNullable<DataHealthData["live_ai_invocation_health"]>;
  readonly newsAiEvalQuality: NonNullable<DataHealthData["news_ai_eval_quality"]>;
  readonly openAiProviderHealth: NonNullable<DataHealthData["openai_provider_health"]>;
  readonly overviewCollectionCards: ReturnType<typeof buildDataHealthOverviewCollectionCards>;
  readonly qualityAudit: NonNullable<DataHealthData["cycle_ai_quality_audit"]>;
  readonly qualityAuditSamples: ReturnType<typeof qualityAuditSampleGroups>;
  readonly runs: ReturnType<typeof buildDataHealthPageState>["runs"];
  readonly runtimeDetailPanels: ReturnType<typeof buildDataHealthRuntimeDetailPanels>;
  readonly schedulerCadenceGroups: ReturnType<typeof buildDataHealthPageState>["schedulerCadenceGroups"];
  readonly tossBrokerSection: DataHealthTossBrokerSectionModel;
  readonly triageOverviewBuckets: readonly DataHealthTriageBucket[];
};

export function buildDataHealthPageModel(data: DataHealthData): DataHealthPageModel {
  const operationsViewModel = buildOperationsViewModel(data);
  const state = buildDataHealthPageState(data);
  const overviewCollectionCards = buildDataHealthOverviewCollectionCards({
    data,
    runs: state.runs,
    tossMarketData: state.tossMarketData,
  });
  const dataHealthHeadline = buildDataHealthHeadline({
    failedPipelines: state.failedPipelines,
    openGateCount: data.open_gates.length,
  });

  return {
    automationDetailSection: buildDataHealthAutomationDetailSection({
      data,
      ec2SchedulerInstalled: state.ec2SchedulerInstalled,
      localWorker: state.localWorker,
      manualSmoke: state.manualSmoke,
      profileScheduler: state.profileScheduler,
      provider: state.providerBudget.provider,
      runs: state.runs,
      schedulerActivation: state.schedulerActivation,
    }),
    commandCenterCards: buildDataHealthCommandCards({
      allTimersActive: state.profileScheduler.timer_count > 0
        && state.profileScheduler.active_timer_count === state.profileScheduler.timer_count,
      dataQualityReady: state.dataQualityReady,
      dueNowGateCount: state.gateTriageBuckets.find((bucket) => bucket.key === "due-now")?.gates.length ?? 0,
      failedPipelines: state.failedPipelines,
      fixNowGateCount: state.gateTriageBuckets.find((bucket) => bucket.key === "fix-now")?.gates.length ?? 0,
      investmentReviewGateCount:
        state.gateTriageBuckets.find((bucket) => bucket.key === "investment-review")?.gates.length ?? 0,
      liveAiInvocationHealth: state.liveAiInvocationHealth,
      managedWaitGateCount: state.gateTriageBuckets.find((bucket) => bucket.key === "managed-wait")?.gates.length ?? 0,
      newsAiEvalQuality: state.newsAiEvalQuality,
      openGateCount: data.open_gates.length,
      outcomeWaitMonitor: state.outcomeWaitMonitor,
      professionalQuality: state.professionalQuality,
      professionalSourceGaps: state.professionalSourceGaps,
      profileScheduler: state.profileScheduler,
      qualityAudit: state.qualityAudit,
      safeInvestmentBoundary: state.safeInvestmentBoundary,
      sourceLimitGateCount: state.gateTriageBuckets.find((bucket) => bucket.key === "source-limit")?.gates.length ?? 0,
    }),
    data,
    dataGapCards: buildDataHealthDataGapCards({
      crossAssetHealthOk: state.runs.crossAssetRun?.health_status === "ok",
      fundSourceGapCount: state.professionalSourceGaps.fund_source_gap_count,
      tossAttentionRequired: state.tossMarketData.sync.attention_required,
    }),
    dataHealthHeadline,
    dataHealthMetaItems: buildDataHealthMetaItems({
      openGateCount: data.open_gates.length,
      outcomeWaitMonitor: state.outcomeWaitMonitor,
      providerBudget: state.providerBudget,
      schedulerActivation: state.schedulerActivation,
    }),
    decisionFlowCards: buildDataHealthDecisionFlowCards({
      aiAttentionRequired: state.liveAiInvocationHealth.attention_required,
      aiInvocationLabel: liveAiInvocationTitle(state.liveAiInvocationHealth),
      crossAssetHealthOk: state.runs.crossAssetRun?.health_status === "ok",
      crossAssetIndicatorRunLabel: runStateLabel(state.runs.crossAssetIndicatorRun),
      crossAssetRunLabel: runStateLabel(state.runs.crossAssetRun),
      dataQualityReady: state.dataQualityReady,
      decisionRunLabel: runStateLabel(state.runs.decisionRun),
      latestPriceDateLabel: state.activeRecommendationPriceFreshness.global_latest_trade_date || "미확인",
      manualWeightReviewAllowed: state.outcomeWaitMonitor.manual_weight_review_allowed,
      marketPriceRunLabel: runStateLabel(state.runs.marketPriceRun),
      newsRunLabel: runStateLabel(state.runs.newsRun),
      nextRecommendationDueDateLabel: state.outcomeMaturity.next_due_date || "미확인",
      outcomeWeightReviewBlocked: state.outcomeWaitMonitor.weight_review_blocked,
      priceAttentionRequired: state.activeRecommendationPriceFreshness.attention_required,
      recommendationOutcomeRunLabel: runStateLabel(state.runs.recommendationOutcomeRun),
      remediationRunLabel: runStateLabel(state.runs.remediationRun),
      safeInvestmentBoundary: state.safeInvestmentBoundary,
      tossAttentionRequired: state.tossMarketData.sync.attention_required,
      tossBrokerSubmitAllowed: state.tossMarketData.sync.broker_submit_allowed,
      tossComparisonLabel: koCode(state.tossMarketData.provider_comparison.status),
      tossSyncLabel: koCode(state.tossMarketData.sync.status),
    }),
    decisionMap: {
      density: "compact",
      description: "세부 실행 기록은 뒤로 보내고, 투자 화면 신뢰도에 직접 영향을 주는 지점부터 확인합니다.",
      eyebrow: "운영 화면 읽는 순서",
      steps: buildDataHealthDecisionMapSteps({
        activeRecommendationPriceFreshness: state.activeRecommendationPriceFreshness,
        data,
        dataHealthHeadline,
        failedPipelines: state.failedPipelines,
        liveAiInvocationHealth: state.liveAiInvocationHealth,
        outcomeMaturity: state.outcomeMaturity,
        overviewCollectionCount: overviewCollectionCards.length,
        qualityAuditStatus: state.qualityAudit.status,
        schedulerActivation: state.schedulerActivation,
      }),
      title: "장애, 데이터, AI, 자동 실행만 먼저 본다",
    } satisfies PageDecisionMapProps,
    detailDecisionCards: buildDataHealthDetailDecisionCards({
      benchmarkDriftQuality: state.benchmarkDriftQuality,
      liveAiInvocationHealth: state.liveAiInvocationHealth,
      openAiProviderHealth: state.openAiProviderHealth,
      outcomeCalibration: state.outcomeCalibration,
      outcomeDueActionRouter: state.outcomeDueActionRouter,
      portfolioReviewActionRouter: state.portfolioReviewActionRouter,
      portfolioReviewCadence: state.portfolioReviewCadence,
      portfolioReviewCalibration: state.portfolioReviewCalibration,
      portfolioReviewFeedback: state.portfolioReviewFeedback,
      portfolioReviewHistory: state.portfolioReviewHistory,
      professionalDepth: state.professionalDepth,
      professionalNextAction: state.professionalNextAction,
      professionalQuality: state.professionalQuality,
      professionalRecommendationAudit: state.professionalRecommendationAudit,
      professionalSourceGaps: state.professionalSourceGaps,
      tossMarketData: state.tossMarketData,
    }),
    ec2SchedulerInstalled: state.ec2SchedulerInstalled,
    executionHistoryRows: buildDataHealthExecutionHistoryRows(data),
    gateTriageStatus: state.gateTriageStatus,
    headerDescription: `${operationsViewModel.summary}. ${operationsViewModel.nextAction}`,
    headerTitle: operationsViewModel.statusLabel,
    liveAiInvocationHealth: state.liveAiInvocationHealth,
    newsAiEvalQuality: state.newsAiEvalQuality,
    openAiProviderHealth: state.openAiProviderHealth,
    overviewCollectionCards,
    qualityAudit: state.qualityAudit,
    qualityAuditSamples: state.qualityAuditSamples,
    runs: state.runs,
    runtimeDetailPanels: buildDataHealthRuntimeDetailPanels({
      activeRecommendationPriceFreshness: state.activeRecommendationPriceFreshness,
      alertDestination: state.alertDestination,
      artifactRunner: state.artifactRunner,
      authRbac: state.authRbac,
      budgetUsage: state.budgetUsage,
      data,
      openGateChips: buildDataHealthOpenGateChips(data, state.openGateDetails),
      openGateDetails: state.openGateDetails,
      productionApiServer: state.productionApiServer,
      providerBudget: state.providerBudget,
      schedulerActivation: state.schedulerActivation,
    }),
    schedulerCadenceGroups: state.schedulerCadenceGroups,
    tossBrokerSection: buildDataHealthTossBrokerSection(state.tossMarketData),
    triageOverviewBuckets: buildDataHealthTriageOverviewBuckets(state.visibleGateTriageBuckets),
  };
}
