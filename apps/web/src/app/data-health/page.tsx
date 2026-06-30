import type { Route } from "next";
import {
  DataHealthAutomationDetailSection,
} from "@/components/operations/DataHealthAutomationDetailSection";
import {
  DataHealthOverview,
  type DataHealthTriageBucket,
} from "@/components/operations/DataHealthOverview";
import type { DataHealthRuntimeChip } from "@/components/operations/DataHealthRuntimeDetailPanels";
import { DataHealthTossBrokerSection } from "@/components/operations/DataHealthTossBrokerSection";
import { OperationsConsoleHeader } from "@/components/operations/OperationsConsoleHeader";
import { PageDecisionMap } from "@/components/research/PageDecisionMap";
import { getDataHealth } from "@/lib/frontend-api";
import { koCode } from "@/lib/korean-labels";
import { buildOperationsViewModel } from "@/lib/presentation";
import type { DataHealthData } from "@/lib/types";

import { DataHealthAiFallbackWarning } from "./_components/DataHealthAiFallbackWarning";
import { DataHealthDataGapScorecards } from "./_components/DataHealthDataGapScorecards";
import {
  buildDataHealthDataGapCards,
  buildDataHealthDecisionFlowCards,
} from "./_components/DataHealthDecisionFlowModel";
import { DataHealthDecisionFlowStatus } from "./_components/DataHealthDecisionFlowStatus";
import {
  DataHealthDetailDecisionCardsSection,
} from "./_components/DataHealthDetailDecisionCardsSection";
import { DataHealthExecutionLogDetails } from "./_components/DataHealthExecutionLogDetails";
import { DataHealthInvestmentQualityDetails } from "./_components/DataHealthInvestmentQualityDetails";
import { DataHealthLiveAiInvocationSection } from "./_components/DataHealthLiveAiInvocationSection";
import { DataHealthNewsAiEvalQualitySection } from "./_components/DataHealthNewsAiEvalQualitySection";
import { DataHealthOpenAiProviderSection } from "./_components/DataHealthOpenAiProviderSection";
import { DataHealthQualityAuditSection } from "./_components/DataHealthQualityAuditSection";
import { DataHealthSchedulerCadenceSection } from "./_components/DataHealthSchedulerCadenceSection";
import { buildDataHealthAutomationDetailSection } from "./_components/dataHealthAutomationDetailModel";
import { buildDataHealthOverviewCollectionCards } from "./_components/dataHealthCollectionStatusModel";
import { buildDataHealthDetailDecisionCards } from "./_components/dataHealthDetailDecisionCardModel";
import { buildDataHealthExecutionHistoryRows } from "./_components/dataHealthExecutionHistoryModel";
import {
  buildDataHealthCommandCards,
  buildDataHealthHeadline,
  buildDataHealthMetaItems,
} from "./_components/dataHealthOverviewCardModel";
import { buildDataHealthRuntimeDetailPanels } from "./_components/dataHealthRuntimeDetailPanelModel";
import {
  DEFAULT_ACTIVE_RECOMMENDATION_PRICE_FRESHNESS,
  DEFAULT_ALERT_DESTINATION,
  DEFAULT_AUTH_RBAC,
  DEFAULT_BENCHMARK_DRIFT_QUALITY,
  DEFAULT_CYCLE_AI_QUALITY_AUDIT,
  DEFAULT_DATA_OPERATIONS_ARTIFACT_RUNNER,
  DEFAULT_LIVE_AI_INVOCATION_HEALTH,
  DEFAULT_LOCAL_WORKER,
  DEFAULT_MANUAL_SMOKE,
  DEFAULT_NEWS_AI_EVAL_QUALITY,
  DEFAULT_OPENAI_PROVIDER_HEALTH,
  DEFAULT_OUTCOME_MATURITY_WAIT_MONITOR,
  DEFAULT_PORTFOLIO_REVIEW_DECISION_FEEDBACK,
  DEFAULT_PORTFOLIO_REVIEW_DECISION_HISTORY,
  DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_ACTION_ROUTER,
  DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_CADENCE,
  DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_CALIBRATION,
  DEFAULT_PRODUCTION_API_SERVER,
  DEFAULT_PROFESSIONAL_ANALYSIS_DEPTH,
  DEFAULT_PROFESSIONAL_ANALYSIS_NEXT_ACTION,
  DEFAULT_PROFESSIONAL_ANALYSIS_QUALITY,
  DEFAULT_PROFESSIONAL_RECOMMENDATION_COVERAGE_AUDIT,
  DEFAULT_PROFESSIONAL_SOURCE_GAP_PRIORITIZATION,
  DEFAULT_PROFILE_SCHEDULER,
  DEFAULT_RECOMMENDATION_OUTCOME_CALIBRATION,
  DEFAULT_RECOMMENDATION_OUTCOME_DUE_ACTION_ROUTER,
  DEFAULT_RECOMMENDATION_OUTCOME_MATURITY,
  DEFAULT_RECOMMENDATION_WEIGHT_REVIEW_READINESS,
  automationStateLabel,
  buildGateTriageBuckets,
  buildSchedulerCadenceGroups,
  findPipelineRun,
  gateSeverityTone,
  gateTriageSummary,
  isEc2ProfileSchedulerInstalled,
  liveAiInvocationTitle,
  liveAiInvocationTone,
  newsAiEvalTone,
  openGateCopy,
  operationCopy,
  qualityAuditSampleGroups,
  qualityAuditTone,
  runStateLabel,
  tossMarketDataTitle,
  tossMarketDataTone,
} from "./_components/dataHealthModel";
export const dynamic = "force-dynamic";
export const metadata = { title: "데이터·자동화 상태" };

export default async function DataHealthPage() {
  const response = await getDataHealth();
  const data = response.data;
  const operationsViewModel = buildOperationsViewModel(data);
  const providerBudget = data.provider_budget;
  const productionApiServer = data.production_api_server ?? DEFAULT_PRODUCTION_API_SERVER;
  const authRbac = data.auth_rbac ?? DEFAULT_AUTH_RBAC;
  const alertDestination = data.alert_destination ?? DEFAULT_ALERT_DESTINATION;
  const artifactRunner = data.data_operations_artifact_runner ?? DEFAULT_DATA_OPERATIONS_ARTIFACT_RUNNER;
  const activeRecommendationPriceFreshness =
    data.active_recommendation_price_freshness ?? DEFAULT_ACTIVE_RECOMMENDATION_PRICE_FRESHNESS;
  const schedulerActivation = data.scheduler.activation;
  const profileScheduler = data.scheduler.profile_scheduler ?? DEFAULT_PROFILE_SCHEDULER;
  const ec2SchedulerInstalled = isEc2ProfileSchedulerInstalled(data.scheduler);
  const manualSmoke = data.manual_local_ingest_smoke ?? DEFAULT_MANUAL_SMOKE;
  const localWorker = data.local_ingest_worker ?? DEFAULT_LOCAL_WORKER;
  const qualityAudit = data.cycle_ai_quality_audit ?? DEFAULT_CYCLE_AI_QUALITY_AUDIT;
  const qualityAuditSamples = qualityAuditSampleGroups(qualityAudit);
  const newsAiEvalQuality = data.news_ai_eval_quality ?? DEFAULT_NEWS_AI_EVAL_QUALITY;
  const liveAiInvocationHealth = data.live_ai_invocation_health ?? DEFAULT_LIVE_AI_INVOCATION_HEALTH;
  const openAiProviderHealth = data.openai_provider_health ?? DEFAULT_OPENAI_PROVIDER_HEALTH;
  const benchmarkDriftQuality = data.benchmark_drift_quality ?? DEFAULT_BENCHMARK_DRIFT_QUALITY;
  const portfolioReviewHistory =
    data.portfolio_review_decision_history ?? DEFAULT_PORTFOLIO_REVIEW_DECISION_HISTORY;
  const portfolioReviewFeedback =
    data.portfolio_review_decision_feedback ?? DEFAULT_PORTFOLIO_REVIEW_DECISION_FEEDBACK;
  const portfolioReviewCalibration =
    data.portfolio_review_feedback_calibration ?? DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_CALIBRATION;
  const portfolioReviewCadence =
    data.portfolio_review_feedback_cadence ?? DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_CADENCE;
  const portfolioReviewActionRouter =
    data.portfolio_review_feedback_action_router ?? DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_ACTION_ROUTER;
  const benchmarkDriftDecisionBySymbol = new Map(
    benchmarkDriftQuality.outlier_decisions.map((decision) => [decision.symbol, decision]),
  );
  const outcomeCalibration =
    data.recommendation_outcome_calibration ?? DEFAULT_RECOMMENDATION_OUTCOME_CALIBRATION;
  const outcomeMaturity = data.recommendation_outcome_maturity ?? DEFAULT_RECOMMENDATION_OUTCOME_MATURITY;
  const outcomeDueActionRouter =
    data.recommendation_outcome_due_action_router ?? DEFAULT_RECOMMENDATION_OUTCOME_DUE_ACTION_ROUTER;
  const weightReviewReadiness =
    data.recommendation_weight_review_readiness ?? DEFAULT_RECOMMENDATION_WEIGHT_REVIEW_READINESS;
  const outcomeWaitMonitor =
    data.outcome_maturity_wait_monitor ?? DEFAULT_OUTCOME_MATURITY_WAIT_MONITOR;
  const professionalSourceGaps =
    data.professional_source_gap_prioritization ?? DEFAULT_PROFESSIONAL_SOURCE_GAP_PRIORITIZATION;
  const professionalQuality =
    data.professional_analysis_quality ?? DEFAULT_PROFESSIONAL_ANALYSIS_QUALITY;
  const professionalRecommendationAudit =
    data.professional_recommendation_coverage_audit ?? DEFAULT_PROFESSIONAL_RECOMMENDATION_COVERAGE_AUDIT;
  const professionalDepth =
    data.professional_analysis_depth ?? DEFAULT_PROFESSIONAL_ANALYSIS_DEPTH;
  const professionalNextAction =
    data.professional_analysis_next_action ?? DEFAULT_PROFESSIONAL_ANALYSIS_NEXT_ACTION;
  const openGateDetails = data.open_gate_details ?? [];
  const gateTriageBuckets = buildGateTriageBuckets(openGateDetails);
  const visibleGateTriageBuckets = gateTriageBuckets.filter((bucket) => bucket.gates.length > 0);
  const gateTriageStatus = gateTriageSummary(gateTriageBuckets, data.open_gates.length);
  const fixNowGateCount = gateTriageBuckets.find((bucket) => bucket.key === "fix-now")?.gates.length ?? 0;
  const dueNowGateCount = gateTriageBuckets.find((bucket) => bucket.key === "due-now")?.gates.length ?? 0;
  const managedWaitGateCount = gateTriageBuckets.find((bucket) => bucket.key === "managed-wait")?.gates.length ?? 0;
  const sourceLimitGateCount = gateTriageBuckets.find((bucket) => bucket.key === "source-limit")?.gates.length ?? 0;
  const investmentReviewGateCount =
    gateTriageBuckets.find((bucket) => bucket.key === "investment-review")?.gates.length ?? 0;
  const openGateChips: DataHealthRuntimeChip[] = openGateDetails.length > 0
    ? openGateDetails.map((gate) => ({
        key: gate.gate_id,
        label: gate.label,
        tone: gateSeverityTone(gate.severity),
      }))
    : data.open_gates.map((gate) => ({
        key: gate,
        label: operationCopy(koCode(gate)).replaceAll("_", " "),
        tone: "risk-medium",
      }));
  const marketPriceRun = findPipelineRun(data, "market-price-daily", "market_price_upsert");
  const newsRun = findPipelineRun(data, "news-rss-daily", "news_rss_upsert");
  const newsEnrichmentRun = findPipelineRun(
    data,
    "news-rss-enrichment-intraday",
    "news_rss_event_enrichment",
  );
  const aiRun = findPipelineRun(data, "event-intelligence-weekly", "event_intelligence_llm_extract");
  const decisionRun = findPipelineRun(data, "cycle-recommendation-weekly", "cycle_state_snapshot");
  const remediationRun = findPipelineRun(
    data,
    "portfolio-remediation-daily",
    "portfolio_remediation_daily_automation",
  );
  const crossAssetRun = findPipelineRun(data, "cross-asset-regime-daily", "cross_asset_regime_snapshot");
  const crossAssetIndicatorRun = findPipelineRun(
    data,
    "cross-asset-indicator-ingest-daily",
    "cross_asset_indicator_ingest",
  );
  const recommendationOutcomeRun = findPipelineRun(
    data,
    "recommendation-outcome-backfill-daily",
    "performance_outcome_schedule_bootstrap",
  );
  const tossMarketData = data.tossinvest_market_data;
  const budgetUsage =
    providerBudget.daily_budget > 0
      ? Math.round((providerBudget.used_request_count / providerBudget.daily_budget) * 100)
      : 0;
  const failedPipelines = data.pipeline_runs.filter((run) =>
    ["missing", "stale", "failed"].includes(run.health_status),
  ).length;
  const schedulerCadenceGroups = buildSchedulerCadenceGroups(profileScheduler.timers);
  const accessAttention =
    productionApiServer.attention_required || authRbac.attention_required || alertDestination.attention_required;
  const allTimersActive =
    profileScheduler.timer_count > 0 && profileScheduler.active_timer_count === profileScheduler.timer_count;
  const dataQualityReady =
    qualityAuditTone(qualityAudit) === "risk-low"
    && newsAiEvalTone(newsAiEvalQuality) === "risk-low"
    && liveAiInvocationTone(liveAiInvocationHealth) === "risk-low";
  const safeInvestmentBoundary =
    outcomeWaitMonitor.weight_review_blocked
    && !outcomeWaitMonitor.automatic_weight_change_allowed
    && !outcomeWaitMonitor.broker_submit_allowed;
  const commandCenterCards = buildDataHealthCommandCards({
    allTimersActive,
    dataQualityReady,
    dueNowGateCount,
    failedPipelines,
    fixNowGateCount,
    investmentReviewGateCount,
    liveAiInvocationHealth,
    managedWaitGateCount,
    newsAiEvalQuality,
    openGateCount: data.open_gates.length,
    outcomeWaitMonitor,
    professionalQuality,
    professionalSourceGaps,
    profileScheduler,
    qualityAudit,
    safeInvestmentBoundary,
    sourceLimitGateCount,
  });
  const detailDecisionCards = buildDataHealthDetailDecisionCards({
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
  });
  const automationDetailSection = buildDataHealthAutomationDetailSection({
    data,
    ec2SchedulerInstalled,
    localWorker,
    manualSmoke,
    profileScheduler,
    provider: providerBudget.provider,
    runs: {
      aiRun,
      decisionRun,
      marketPriceRun,
      newsEnrichmentRun,
      newsRun,
      remediationRun,
    },
    schedulerActivation,
  });
  const overviewCollectionCards = buildDataHealthOverviewCollectionCards({
    data,
    runs: {
      aiRun,
      decisionRun,
      marketPriceRun,
      newsEnrichmentRun,
      newsRun,
      remediationRun,
    },
    tossMarketData,
  });
  const dataHealthHeadline = buildDataHealthHeadline({
    failedPipelines,
    openGateCount: data.open_gates.length,
  });
  const dataHealthMetaItems = buildDataHealthMetaItems({
    openGateCount: data.open_gates.length,
    outcomeWaitMonitor,
    providerBudget,
    schedulerActivation,
  });
  const decisionFlowCards = buildDataHealthDecisionFlowCards({
    aiAttentionRequired: liveAiInvocationHealth.attention_required,
    aiInvocationLabel: liveAiInvocationTitle(liveAiInvocationHealth),
    crossAssetHealthOk: crossAssetRun?.health_status === "ok",
    crossAssetIndicatorRunLabel: runStateLabel(crossAssetIndicatorRun),
    crossAssetRunLabel: runStateLabel(crossAssetRun),
    dataQualityReady,
    decisionRunLabel: runStateLabel(decisionRun),
    latestPriceDateLabel: activeRecommendationPriceFreshness.global_latest_trade_date || "미확인",
    manualWeightReviewAllowed: outcomeWaitMonitor.manual_weight_review_allowed,
    marketPriceRunLabel: runStateLabel(marketPriceRun),
    newsRunLabel: runStateLabel(newsRun),
    nextRecommendationDueDateLabel: outcomeMaturity.next_due_date || "미확인",
    outcomeWeightReviewBlocked: outcomeWaitMonitor.weight_review_blocked,
    priceAttentionRequired: activeRecommendationPriceFreshness.attention_required,
    recommendationOutcomeRunLabel: runStateLabel(recommendationOutcomeRun),
    remediationRunLabel: runStateLabel(remediationRun),
    safeInvestmentBoundary,
    tossAttentionRequired: tossMarketData.sync.attention_required,
    tossBrokerSubmitAllowed: tossMarketData.sync.broker_submit_allowed,
    tossComparisonLabel: koCode(tossMarketData.provider_comparison.status),
    tossSyncLabel: koCode(tossMarketData.sync.status),
  });
  const dataGapCards = buildDataHealthDataGapCards({
    crossAssetHealthOk: crossAssetRun?.health_status === "ok",
    fundSourceGapCount: professionalSourceGaps.fund_source_gap_count,
    tossAttentionRequired: tossMarketData.sync.attention_required,
  });
  const triageOverviewBuckets: DataHealthTriageBucket[] = visibleGateTriageBuckets.map((bucket) => ({
    description: bucket.description,
    gates: bucket.gates.map((gate) => ({
      id: gate.gate_id,
      label: openGateCopy(gate.label),
      nextAction: openGateCopy(gate.next_action),
      statusLabel: openGateCopy(gate.status_label),
      statusTone: gateSeverityTone(gate.severity),
      summary: operationCopy(gate.summary),
    })),
    href: bucket.href,
    key: bucket.key,
    label: bucket.label,
    title: bucket.title,
    tone: bucket.tone,
  }));
  const runtimeDetailPanels = buildDataHealthRuntimeDetailPanels({
    activeRecommendationPriceFreshness,
    alertDestination,
    artifactRunner,
    authRbac,
    budgetUsage,
    data,
    openGateChips,
    openGateDetails,
    productionApiServer,
    providerBudget,
    schedulerActivation,
  });
  const executionHistoryRows = buildDataHealthExecutionHistoryRows(data);
  return (
    <div className="terminal-page decision-page">
      <OperationsConsoleHeader
        section="데이터 상태"
        title={operationsViewModel.statusLabel}
        description={`${operationsViewModel.summary}. ${operationsViewModel.nextAction}`}
        currentPath={"/data-health" as Route}
      />
      <PageDecisionMap
        density="compact"
        eyebrow="운영 화면 읽는 순서"
        title="장애, 데이터, AI, 자동 실행만 먼저 본다"
        description="세부 실행 기록은 뒤로 보내고, 투자 화면 신뢰도에 직접 영향을 주는 지점부터 확인합니다."
        steps={[
          {
            description: "열린 항목과 수집·분석 상태를 먼저 본다.",
            href: "#data-health-title",
            label: "상태",
            status: dataHealthHeadline,
            title: "전체 상태",
            tone: failedPipelines > 0 ? "block" : data.open_gates.length > 0 ? "watch" : "ready",
          },
          {
            description: "원천 데이터가 어느 투자 화면에 쓰이는지 확인합니다.",
            href: "#collection-status-title",
            label: "커버리지",
            status: `${overviewCollectionCards.length.toLocaleString("ko-KR")}개 영역`,
            title: "수집·분석 연결",
            tone: "ready",
          },
          {
            description: "중복, 오분류, 근거 없는 연결이 있는지 확인합니다.",
            href: "#quality-audit",
            label: "품질",
            status: koCode(qualityAudit.status),
            title: "품질 감사",
            tone: qualityAudit.status === "attention_required" ? "watch" : "ready",
          },
          {
            description: "실제 AI 호출, 무료 API 예산, 공급자 상태를 본다.",
            href: "#live-ai-invocation-health",
            label: "AI",
            status: liveAiInvocationHealth.attention_required ? "확인 필요" : "호출 상태 확인",
            title: "AI·공급자 상태",
            tone: liveAiInvocationHealth.attention_required ? "watch" : "ready",
          },
          {
            description: "다음 자동 실행 시각과 반복 실행 상태를 확인합니다.",
            href: "#scheduler-profile-title",
            label: "자동 실행",
            status: automationStateLabel(schedulerActivation),
            title: "스케줄러",
            tone: schedulerActivation.activation_allowed ? "ready" : "watch",
          },
        ]}
      />
      <DataHealthDecisionFlowStatus cards={decisionFlowCards} />
      <DataHealthDataGapScorecards cards={dataGapCards} />
      <DataHealthOverview
        asOfDate={data.as_of_date}
        collectionCards={overviewCollectionCards}
        commandCards={commandCenterCards}
        headline={dataHealthHeadline}
        metaItems={dataHealthMetaItems}
        triageBuckets={triageOverviewBuckets}
        triageStatus={gateTriageStatus}
      />

      <DataHealthTossBrokerSection
        cadenceCountLabel={`${Object.keys(tossMarketData.sync.collection_cadence).length.toLocaleString("ko-KR")}개`}
        candleCountLabel={`${tossMarketData.sync.candle_bar_count.toLocaleString("ko-KR")}개`}
        comparisonLookbackLabel={`${tossMarketData.provider_comparison.lookback_days}거래일 · 허용 ${tossMarketData.provider_comparison.max_diff_bps}bps`}
        comparisonStatusLabel={koCode(tossMarketData.provider_comparison.status)}
        orderBoundaryLabel={koCode(tossMarketData.sync.order_boundary)}
        orderSubmitLabel={tossMarketData.sync.broker_submit_allowed ? "증권사 주문 제출 가능" : "증권사 주문 제출 차단"}
        requestedSymbolCountLabel={`${tossMarketData.sync.requested_symbol_count.toLocaleString("ko-KR")}개`}
        syncStatusLabel={koCode(tossMarketData.sync.status)}
        syncStatusTone={tossMarketDataTone(tossMarketData)}
        title={tossMarketDataTitle(tossMarketData)}
      />

      <DataHealthQualityAuditSection
        qualityAudit={qualityAudit}
        qualityAuditSamples={qualityAuditSamples}
      />

      <DataHealthLiveAiInvocationSection liveAiInvocationHealth={liveAiInvocationHealth} />

      <DataHealthOpenAiProviderSection openAiProviderHealth={openAiProviderHealth} />

      <DataHealthNewsAiEvalQualitySection newsAiEvalQuality={newsAiEvalQuality} />

      <DataHealthDetailDecisionCardsSection cards={detailDecisionCards} />

      <DataHealthInvestmentQualityDetails data={data} />

      <DataHealthSchedulerCadenceSection
        ec2SchedulerInstalled={ec2SchedulerInstalled}
        groups={schedulerCadenceGroups}
      />

      <DataHealthAiFallbackWarning run={aiRun} />

      <DataHealthAutomationDetailSection {...automationDetailSection} />

      <DataHealthExecutionLogDetails
        executionHistoryRows={executionHistoryRows}
        runtimeDetailPanels={runtimeDetailPanels}
      />
    </div>
  );
}
