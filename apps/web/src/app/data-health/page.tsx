import type { Route } from "next";
import {
  DataHealthAutomationDetailSection,
} from "@/components/operations/DataHealthAutomationDetailSection";
import type { DataHealthAutomationDetailSectionProps } from "@/components/operations/DataHealthAutomationDetailTypes";
import type { DataHealthExecutionHistoryRow } from "@/components/operations/DataHealthExecutionHistoryPanel";
import {
  DataHealthOverview,
  type DataHealthCollectionCard,
  type DataHealthTriageBucket,
} from "@/components/operations/DataHealthOverview";
import type {
  DataHealthRuntimeDetailPanelsProps,
  DataHealthRuntimeChip,
} from "@/components/operations/DataHealthRuntimeDetailPanels";
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
  type DataHealthDetailDecisionCard,
} from "./_components/DataHealthDetailDecisionCardsSection";
import { DataHealthExecutionLogDetails } from "./_components/DataHealthExecutionLogDetails";
import { DataHealthInvestmentQualityDetails } from "./_components/DataHealthInvestmentQualityDetails";
import { DataHealthLiveAiInvocationSection } from "./_components/DataHealthLiveAiInvocationSection";
import { DataHealthNewsAiEvalQualitySection } from "./_components/DataHealthNewsAiEvalQualitySection";
import { DataHealthOpenAiProviderSection } from "./_components/DataHealthOpenAiProviderSection";
import { DataHealthQualityAuditSection } from "./_components/DataHealthQualityAuditSection";
import { DataHealthSchedulerCadenceSection } from "./_components/DataHealthSchedulerCadenceSection";
import {
  buildDataHealthCommandCards,
  buildDataHealthHeadline,
  buildDataHealthMetaItems,
} from "./_components/dataHealthOverviewCardModel";
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
  actionRouterStatusClass,
  actionRouterTitle,
  automationStateLabel,
  benchmarkDriftQualityExplanation,
  benchmarkDriftQualityTitle,
  benchmarkDriftQualityTone,
  buildGateTriageBuckets,
  buildSchedulerCadenceGroups,
  cadenceLabel,
  cadenceStatusClass,
  calibrationStatusClass,
  errorLogLabel,
  evidenceLocationLabel,
  executionIdLabel,
  findPipelineRun,
  finishedAtLabel,
  formatPercent,
  gateSeverityTone,
  gateTriageSummary,
  isEc2ProfileSchedulerInstalled,
  liveAiInvocationExplanation,
  liveAiInvocationTitle,
  liveAiInvocationTone,
  localWorkerExplanation,
  localWorkerNextAction,
  localWorkerTitle,
  manualSmokeExplanation,
  manualSmokeNextAction,
  manualSmokeTitle,
  newsAiEvalExplanation,
  newsAiEvalTitle,
  newsAiEvalTone,
  openAiProviderExplanation,
  openAiProviderTitle,
  openAiProviderTone,
  openGateCopy,
  operationCopy,
  orderBoundaryCopy,
  outcomeCalibrationExplanation,
  outcomeCalibrationTitle,
  outcomeCalibrationTone,
  outcomeDueActionRouterTitle,
  professionalDepthItemTone,
  professionalDepthTitle,
  professionalDepthTone,
  professionalNextActionTone,
  professionalQualityTone,
  professionalRecommendationAuditTone,
  professionalSourceGapExplanation,
  professionalSourceGapTitle,
  professionalSourceGapTone,
  qualityAuditExplanation,
  qualityAuditSampleGroups,
  qualityAuditTitle,
  qualityAuditTone,
  runQualityExplanation,
  runStateLabel,
  schedulerApprovalGateLabel,
  schedulerInstallLabel,
  schedulerNextStepLabel,
  schedulerReadinessExplanation,
  schedulerReadinessTitle,
  statusRiskClass,
  summaryLocationLabel,
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
  const decisionCards: DataHealthDetailDecisionCard[] = [
    {
      label: "지금 판단",
      title:
        productionApiServer.attention_required
          ? "읽기 서버 보강 필요"
          : authRbac.attention_required
          ? "조회 권한 보강 필요"
          : alertDestination.attention_required
          ? "운영 알림 보강 필요"
          : failedPipelines > 0
          ? "수집 문제 먼저 해결"
          : data.overall_status === "healthy"
            ? "수집 상태 정상"
            : "주의 항목 있음",
      body:
        productionApiServer.attention_required
	          ? operationCopy(productionApiServer.next_action)
	          : authRbac.attention_required
	          ? operationCopy(authRbac.next_action)
	          : alertDestination.attention_required
	          ? operationCopy(alertDestination.next_action)
          : failedPipelines > 0
          ? "중단 또는 오래된 작업이 있어 추천·보유 판단보다 수집 복구가 먼저다."
          : "캔들, 뉴스, AI 분석, 추천 갱신이 현재 화면 기준으로 읽을 수 있는 상태다.",
      href: productionApiServer.attention_required || authRbac.attention_required || alertDestination.attention_required ? "#scheduler-detail" : "#execution-log",
      cta: productionApiServer.attention_required
        ? "읽기 서버 보기"
        : authRbac.attention_required
          ? "권한 경계 보기"
        : alertDestination.attention_required
          ? "알림 설정 보기"
          : "실행 이력 보기",
      tone: productionApiServer.attention_required
        ? "risk-high"
        : authRbac.attention_required
          ? "risk-high"
        : alertDestination.attention_required
          ? "risk-medium"
          : failedPipelines > 0
            ? "risk-high"
            : "risk-low",
    },
    {
      label: "자동화",
      title: artifactRunner.attention_required
        ? "실행 증거 보강 필요"
        : `${profileScheduler.active_timer_count}/${profileScheduler.timer_count}개 예약 실행`,
      body: artifactRunner.attention_required
        ? operationCopy(artifactRunner.next_action)
        : `실행 증거 저장기가 ${artifactRunner.latest_run_count}개 최신 실행 증거와 ${artifactRunner.artifact_policy_count}/${artifactRunner.job_count}개 저장 정책을 남기고 있다.`,
      href: "#scheduler-detail",
      cta: "스케줄 보기",
      tone: artifactRunner.attention_required
        ? "risk-medium"
        : profileScheduler.active_timer_count === profileScheduler.timer_count ? "risk-low" : "risk-medium",
    },
    {
      label: "무료 API 예산",
      title: `${providerBudget.remaining_request_count}/${providerBudget.daily_budget}회 남음`,
      body: "가격 데이터는 무료 호출 한도 안에서 보강한다. 예산이 부족하면 캔들 보강을 줄여야 한다.",
      href: "#provider-budget",
      cta: "예산 보기",
      tone: providerBudget.remaining_request_count > 0 ? "risk-low" : "risk-high",
    },
    {
      label: "추천 가격",
      title: activeRecommendationPriceFreshness.attention_required
        ? `${activeRecommendationPriceFreshness.stale_symbol_count + activeRecommendationPriceFreshness.missing_symbol_count}개 가격 보강 필요`
        : "추천 종목 가격 최신",
      body: activeRecommendationPriceFreshness.attention_required
        ? `추천에 쓰이는 종목 가격이 최신 가격일 ${activeRecommendationPriceFreshness.global_latest_trade_date || "미확인"}보다 뒤처져 있다. 가격 보강 전에는 성과·가상 매매 검증 해석 신뢰도가 낮아진다.`
        : `활성 추천 ${activeRecommendationPriceFreshness.active_symbol_count}개 종목 가격이 최신 가격일 ${activeRecommendationPriceFreshness.global_latest_trade_date || "미확인"} 기준으로 맞춰져 있다.`,
      href: "#active-recommendation-price-freshness",
      cta: "가격 최신성 보기",
      tone: activeRecommendationPriceFreshness.attention_required ? "risk-high" : "risk-low",
    },
    {
      label: "토스증권 데이터",
      title: tossMarketData.sync.status === "succeeded"
        ? `캔들 ${tossMarketData.sync.candle_bar_count.toLocaleString("ko-KR")}개`
        : koCode(tossMarketData.sync.status),
      body: `토스증권 데이터는 브로커 현실 확인용이다. 분석 기준 가격 대체 전 검증 상태는 ${koCode(tossMarketData.provider_comparison.status)}이고 실주문은 차단된다.`,
      href: "#toss-market-data",
      cta: "토스 데이터 보기",
      tone: tossMarketData.sync.attention_required ? "risk-medium" : "risk-low",
    },
    {
      label: "품질 감사",
      title: qualityAuditTitle(qualityAudit),
      body: qualityAuditExplanation(qualityAudit),
      href: "#quality-audit",
      cta: "오염 점검 보기",
      tone: qualityAuditTone(qualityAudit),
    },
    {
      label: "실제 AI 호출",
      title: liveAiInvocationTitle(liveAiInvocationHealth),
      body: liveAiInvocationExplanation(liveAiInvocationHealth),
      href: "#live-ai-invocation-health",
      cta: "실제 호출 보기",
      tone: liveAiInvocationTone(liveAiInvocationHealth),
    },
    {
      label: "OpenAI 잔액",
      title: openAiProviderTitle(openAiProviderHealth),
      body: openAiProviderExplanation(openAiProviderHealth),
      href: "#openai-provider-health",
      cta: "잔액·예비 경로 보기",
      tone: openAiProviderTone(openAiProviderHealth),
    },
    {
      label: "AI 기준 평가",
      title: newsAiEvalTitle(newsAiEvalQuality),
      body: newsAiEvalExplanation(newsAiEvalQuality),
      href: "#news-ai-eval-quality",
      cta: "평가 항목 보기",
      tone: newsAiEvalTone(newsAiEvalQuality),
    },
    {
      label: "벤치마크 괴리",
      title: benchmarkDriftQualityTitle(benchmarkDriftQuality),
      body: benchmarkDriftQualityExplanation(benchmarkDriftQuality),
      href: "#benchmark-drift-quality",
      cta: "벤치마크 품질 보기",
      tone: benchmarkDriftQualityTone(benchmarkDriftQuality),
    },
    {
      label: "포트폴리오 검토 이력",
      title:
        portfolioReviewHistory.status === "loaded"
          ? portfolioReviewHistory.attention_required
            ? `${portfolioReviewHistory.decision_count}개 결정 저장됨`
            : "검토 이력 관리 중"
          : "검토 결정 이력 없음",
      body:
        portfolioReviewHistory.status === "loaded"
          ? portfolioReviewHistory.attention_required
            ? `최신 ${portfolioReviewHistory.as_of_date} 기준으로 벤치마크 ${portfolioReviewHistory.benchmark_decision_count}개, 포지션 크기 ${portfolioReviewHistory.position_sizing_decision_count}개 결정을 감사 이력으로 남겼다.`
            : operationCopy(portfolioReviewHistory.managed_review_reason)
	          : "현재 화면의 검토 후보는 보이지만 저장된 검토 이력으로는 아직 남지 않았다.",
      href: "#portfolio-review-history",
      cta: "검토 이력 보기",
      tone: portfolioReviewHistory.attention_required ? "risk-medium" : "risk-low",
    },
    {
      label: "검토 사후평가",
      title:
        portfolioReviewFeedback.status === "loaded"
          ? `${portfolioReviewFeedback.validated_count}개 검증 · ${portfolioReviewFeedback.contradicted_count}개 반박`
          : "사후평가 없음",
      body:
        portfolioReviewFeedback.status === "loaded"
	          ? `저장된 검토 결정 ${portfolioReviewFeedback.decision_count}개를 후속 성과, 가상 매매 검증, 가격 변화와 대조했다.`
	          : "검토 결정 이력은 저장됐지만 아직 이후 성과와 대조한 사후평가 기록이 없다.",
      href: "#portfolio-review-feedback",
      cta: "사후평가 보기",
      tone:
        portfolioReviewFeedback.feedback_status === "has_contradictions"
          ? "risk-high"
          : portfolioReviewFeedback.feedback_status === "needs_more_data"
            ? "risk-medium"
            : "risk-low",
    },
    {
      label: "검토 신뢰도",
      title:
        portfolioReviewCalibration.status === "loaded"
          ? portfolioReviewCalibration.managed_wait
            ? "관리된 대기"
            : portfolioReviewCalibration.weight_review_blocked
              ? "추천 산식 변경 금지"
              : "성과 표본 충족"
          : "누적평가 없음",
      body:
        portfolioReviewCalibration.status === "loaded"
	          ? `성숙 표본 ${portfolioReviewCalibration.mature_decision_count}/${portfolioReviewCalibration.min_mature_decisions}개, 사후평가 ${portfolioReviewCalibration.feedback_run_count}/${portfolioReviewCalibration.min_feedback_runs}회. ${portfolioReviewCalibration.estimated_maturity_date ? `예상 성숙일은 ${portfolioReviewCalibration.estimated_maturity_date}이다.` : operationCopy(portfolioReviewCalibration.weight_review_block_reason)}`
	          : "단일 사후평가만으로 추천 산식 반영 비중을 바꾸지 않기 위해 누적평가가 필요하다.",
      href: "#portfolio-review-calibration",
      cta: "신뢰도 보기",
      tone: portfolioReviewCalibration.managed_wait
        ? "risk-low"
        : calibrationStatusClass(portfolioReviewCalibration.calibration_status),
    },
    {
      label: "검토 실행시점",
      title:
        portfolioReviewCadence.should_run_now
          ? "지금 실행 필요"
          : portfolioReviewCadence.should_wait
            ? "대기"
            : "상태 확인",
      body:
        portfolioReviewCadence.status === "loaded"
	          ? operationCopy(portfolioReviewCadence.reason)
          : "사후평가와 누적평가를 언제 다시 돌릴지 아직 계산되지 않았다.",
      href: "#portfolio-review-cadence",
      cta: "실행시점 보기",
      tone: cadenceStatusClass(portfolioReviewCadence.cadence_status),
    },
    {
      label: "검토 실행 라우터",
      title: actionRouterTitle(portfolioReviewActionRouter),
      body:
        portfolioReviewActionRouter.status === "loaded"
	          ? operationCopy(portfolioReviewActionRouter.reason)
	          : "실행 주기 판단을 실제 사후평가/누적평가 실행 또는 대기로 변환한 기록이 아직 없다.",
      href: "#portfolio-review-action-router",
      cta: "라우터 판단 보기",
      tone: actionRouterStatusClass(portfolioReviewActionRouter.action_status),
    },
    {
      label: "성과검증",
      title: outcomeCalibrationTitle(outcomeCalibration),
      body: outcomeCalibrationExplanation(outcomeCalibration),
      href: "#outcome-calibration",
      cta: "표본 상태 보기",
      tone: outcomeCalibrationTone(outcomeCalibration),
    },
    {
      label: "성과 실행 라우터",
      title: outcomeDueActionRouterTitle(outcomeDueActionRouter),
      body:
        outcomeDueActionRouter.status === "loaded"
	          ? operationCopy(outcomeDueActionRouter.reason)
	          : "성과 측정창 상태를 실제 누적평가 실행 또는 대기로 변환한 기록이 아직 없다.",
      href: "#outcome-calibration",
      cta: "라우터 보기",
      tone: actionRouterStatusClass(outcomeDueActionRouter.action_status),
    },
    {
      label: "전문 분석 소스",
      title: professionalSourceGapTitle(professionalSourceGaps),
      body: professionalSourceGapExplanation(professionalSourceGaps),
      href: "#professional-source-gaps",
      cta: "소스 공백 보기",
      tone: professionalSourceGapTone(professionalSourceGaps),
    },
    {
      label: "전문 분석 품질",
      title: professionalQuality.title,
      body: operationCopy(professionalQuality.summary),
      href: "#professional-analysis-quality",
      cta: "품질 판정 보기",
      tone: professionalQualityTone(professionalQuality),
    },
    {
      label: "추천별 전문 감사",
      title: professionalRecommendationAudit.title,
      body: operationCopy(professionalRecommendationAudit.summary),
      href: "#professional-recommendation-coverage-audit",
      cta: "추천별 감사 보기",
      tone: professionalRecommendationAuditTone(professionalRecommendationAudit),
    },
    {
      label: "전문 분석 다음 행동",
      title: professionalNextAction.title,
      body: operationCopy(professionalNextAction.summary),
      href: "#professional-next-action",
      cta: "다음 행동 보기",
      tone: professionalNextActionTone(professionalNextAction),
    },
    {
	      label: "전문 분석 깊이",
	      title: professionalDepthTitle(professionalDepth),
		      body: `활성 후보 ${professionalDepth.active_candidate_count}개 중 ${professionalDepth.complete_candidate_count}개가 필요한 전문 분석 근거를 채웠고, 평균 연결률은 ${formatPercent(professionalDepth.average_coverage_ratio)}이다.`,
	      href: "#professional-analysis-depth",
	      cta: "깊이 보기",
	      tone: professionalDepthTone(professionalDepth),
	    },
	  ];
	  const priorityDecisionLabels = new Set([
	    "지금 판단",
	    "자동화",
	    "무료 API 예산",
	    "추천 가격",
	    "품질 감사",
	    "AI 기준 평가",
	  ]);
  const detailDecisionCards = decisionCards.filter((card) => !priorityDecisionLabels.has(card.label));
	  const automationCards = [
    {
      title: "주식 캔들 수집",
      run: marketPriceRun,
      fallbackCadence: "일간 · 18:30",
      description: "무료 가격 데이터 제공자의 한도를 확인한 뒤 일봉 캔들을 서버에 저장한다.",
      detail: `최근 가격 관측일 ${data.freshness.find((item) => item.dataset === "market.daily_price_bar")?.latest_observation_date ?? "미확인"} · 제공자 ${koCode(providerBudget.provider)}`,
    },
    {
      title: "뉴스 수집",
      run: newsRun,
      fallbackCadence: "일간 · 08:30",
      description: "저장소 밖 RSS 설정의 무료 뉴스 피드를 읽고 원문과 뉴스 이벤트로 저장한다.",
      detail: "뉴스는 이벤트, 종목 상세, 분석 지도, 추천 근거 점검으로 연결된다.",
    },
    {
      title: "AI 분석",
      run: aiRun,
      fallbackCadence: "장중 · 2시간마다",
      description: "수집 문서를 구조화하고 AI 근거 기록을 남긴다. 중요 뉴스는 AI 배치 분석 후보로 처리하고, 뉴스 묶음은 무료 로컬 규칙 보조 증거로 남긴다.",
      detail: "AI는 근거를 정리하지만 매수·매도·주문 결론을 자동 실행하지 않는다.",
    },
  ];
  const newsAfterAnalysisSteps = [
    {
      index: "01",
      title: "뉴스 원문 수집",
      run: newsRun,
      owner: "news-rss-daily",
      output: "RSS/Atom 문서를 원문 저장소와 실행 기록에 저장한다.",
      next: "중복과 원천 링크를 남긴 뒤 이벤트 구조화 단계로 넘긴다.",
    },
    {
      index: "02",
      title: "이벤트 구조화",
      run: newsEnrichmentRun,
      owner: "news-rss-enrichment-intraday",
      output: "헤드라인과 본문을 종목·테마·영향 방향이 있는 뉴스 이벤트로 정리한다.",
      next: "동일 테마/종목 관계를 만들고 뉴스, 종목, 뉴스·AI 화면이 읽는다.",
    },
    {
      index: "03",
      title: "AI 근거 생성",
      run: aiRun,
      owner: "event-intelligence-weekly",
      output: "중요 뉴스만 AI 배치 분석으로 처리해 종목·테마·방향·근거 항목을 AI 분석 기록에 남긴다.",
      next: "검증을 통과한 근거만 표준 뉴스 영향으로 반영한다. 매수·매도·주문 결론은 여기서 만들지 않는다.",
    },
    {
      index: "04",
      title: "신호와 추천 항목 갱신",
      run: decisionRun,
      owner: "decision-daily",
      output: "가격, 테마 연결, 이벤트 강도, 사이클 상태를 합쳐 추천 항목과 투자 논리 입력을 만든다.",
      next: "결정 로직은 재현 가능한 점수 계산이다. AI 근거는 설명 가능한 보조 근거로 붙는다.",
    },
    {
      index: "05",
      title: "보유 상태와 운영 큐",
      run: remediationRun,
      owner: "portfolio-remediation-daily",
      output: "보유 투자 논리 유지 여부, 빈 가격/논리/성과 항목, 가상 거래 검증 문제를 큐로 만든다.",
      next: "추천 상세, 투자 논리, 보유 상태, 가상 매매 화면에서 본다.",
    },
  ];
  const collectionStatusCards = [
    {
      index: "01",
      title: "주식 캔들",
      run: marketPriceRun,
      purpose: "종목 가격과 차트, 모멘텀 지표의 원천이다.",
      check: `최근 가격일 ${
        data.freshness.find((item) => item.dataset === "market.daily_price_bar")?.latest_observation_date ?? "미확인"
      }`,
    },
    {
      index: "02",
      title: "뉴스 원문",
      run: newsRun,
      purpose: "수집된 뉴스와 원문 화면의 원천이다.",
      check: "수집 뉴스는 뉴스 화면에서 시간순으로 본다.",
    },
    {
      index: "03",
      title: "1차 분류 태깅",
      run: newsEnrichmentRun,
      purpose: "뉴스를 종목, 테마, 방향 태그로 1차 정리한다.",
      check: "AI 전 단계이므로 틀릴 수 있고, 이후 AI 분석과 검증이 보강한다.",
    },
    {
      index: "04",
      title: "AI 배치 분석",
      run: aiRun,
      purpose: "중요 뉴스를 구조화해 근거 항목을 만든다.",
      check: "화면을 열 때마다 AI를 새로 호출하지 않고 저장된 결과만 읽는다.",
    },
    {
      index: "05",
      title: "AI 결과 검증",
      run: aiRun,
      purpose: "낮은 신뢰도, 알 수 없는 종목/테마, 저신호 뉴스를 차단한다.",
      check: "차단 항목은 AI 차단 항목 화면에서 본다.",
    },
    {
      index: "06",
      title: "추천 신호",
      run: decisionRun,
      purpose: "가격, 뉴스, 사이클, 상위 흐름을 추천 점수로 합친다.",
      check: "추천은 주문이 아니라 읽어야 할 상세 근거다.",
    },
    {
      index: "07",
      title: "보유 상태",
      run: remediationRun,
      purpose: "투자 논리 공백, 성과 미측정, 보유 충돌을 운영 큐로 만든다.",
      check: "보유 상태와 가상 매매 검증으로 이어진다.",
    },
    {
      index: "08",
      title: "토스증권 브로커 데이터",
      run: findPipelineRun(data, "toss-candles-us-shadow-daily", "tossinvest_market_data_sync"),
      purpose: "실제 증권사 화면에서 볼 가격·호가·체결·주의사항을 본다.",
      check: `${koCode(tossMarketData.sync.status)} · ${tossMarketData.sync.requested_symbol_count.toLocaleString("ko-KR")}개 요청`,
    },
  ];
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
  const overviewCollectionCards: DataHealthCollectionCard[] = collectionStatusCards.map((card) => ({
    check: card.check,
    finishedAt: finishedAtLabel(card.run),
    index: card.index,
    purpose: card.purpose,
    statusLabel: runStateLabel(card.run),
    statusTone: statusRiskClass(card.run?.health_status ?? "missing"),
    title: card.title,
  }));
  const runtimeDetailPanels: DataHealthRuntimeDetailPanelsProps = {
    providerBudget: {
      budgetDateLabel: providerBudget.budget_date,
      latestRunLabel: providerBudget.latest_run?.started_at ?? "오늘 실행 없음",
      statusLabel: koCode(providerBudget.status),
      usagePercent: budgetUsage,
      usedRequestCountLabel: `${providerBudget.used_request_count.toLocaleString("ko-KR")}회`,
    },
    activeRecommendationPriceFreshness: {
      latestTradeDateLabel: activeRecommendationPriceFreshness.global_latest_trade_date || "미확인",
      nextActionLabel: operationCopy(activeRecommendationPriceFreshness.next_action),
      orderBoundaryLabel: orderBoundaryCopy(activeRecommendationPriceFreshness.order_boundary),
      staleSummaryLabel: `오래됨 ${activeRecommendationPriceFreshness.stale_symbol_count.toLocaleString("ko-KR")}개 · 없음 ${activeRecommendationPriceFreshness.missing_symbol_count.toLocaleString("ko-KR")}개`,
      staleSymbols: activeRecommendationPriceFreshness.stale_symbols.slice(0, 8).map((item) => ({
        activeRecommendationCountLabel: `연결 추천 ${item.active_recommendation_count.toLocaleString("ko-KR")}개`,
        daysBehindLabel: `최신 기준보다 ${item.days_behind_latest.toLocaleString("ko-KR")}일 뒤처짐`,
        href: item.detail_href || `/stocks/${item.symbol}`,
        latestTradeDateLabel: `최근 가격 ${item.latest_trade_date || "없음"}`,
        statusLabel: koCode(item.status),
        symbol: item.symbol,
      })),
      statusLabel: activeRecommendationPriceFreshness.attention_required ? "가격 보강 필요" : "최신성 확인",
      statusTone: activeRecommendationPriceFreshness.attention_required ? "risk-high" : "risk-low",
      symbolCoverageLabel: `${activeRecommendationPriceFreshness.fresh_symbol_count.toLocaleString("ko-KR")}/${activeRecommendationPriceFreshness.active_symbol_count.toLocaleString("ko-KR")}개 최신`,
    },
    openGates: {
      chips: openGateChips,
      freshnessRows: data.freshness.map((item) => ({
        datasetLabel: koCode(item.dataset),
        valueLabel: `${koCode(item.status)} · ${item.latest_observation_date}`,
      })),
      gates: openGateDetails.map((gate) => ({
        id: gate.gate_id,
        label: gate.label,
        nextActionLabel: openGateCopy(gate.next_action),
        orderBoundaryLabel: orderBoundaryCopy(gate.order_boundary),
        statusLabel: gate.status_label,
        statusTone: gateSeverityTone(gate.severity),
        summary: gate.summary,
        typeLabel: gate.category_label,
      })),
    },
    runtimeBoundary: {
      apiNextActionLabel: operationCopy(productionApiServer.next_action),
      apiReadinessLabel: productionApiServer.attention_required ? "보강 필요" : "운영 준비됨",
      artifactEvidenceLabel: artifactRunner.attention_required ? "보강 필요" : "운영 증거 있음",
      artifactLatestRootLabel: evidenceLocationLabel(artifactRunner.latest_artifact_root),
      artifactNextActionLabel: operationCopy(artifactRunner.next_action),
      artifactPolicyLabel: `${artifactRunner.artifact_policy_count.toLocaleString("ko-KR")}/${artifactRunner.job_count.toLocaleString("ko-KR")}개 · 최신 실행 ${artifactRunner.latest_run_count.toLocaleString("ko-KR")}개`,
      authNextActionLabel: operationCopy(authRbac.next_action),
      authReadinessLabel: authRbac.attention_required ? "보강 필요" : "읽기 전용 권한 준비",
      brokerOrderLabel: `쓰기 ${authRbac.write_methods_allowed ? "허용됨" : "차단됨"} · 주문 ${authRbac.broker_submit_allowed ? "허용됨" : "차단됨"} · ${orderBoundaryCopy(authRbac.order_boundary)}`,
      connectionLabel: `${koCode(productionApiServer.runtime_profile)} · ${koCode(productionApiServer.source_mode)} · ${koCode(productionApiServer.connection_boundary)}`,
      environmentLabel: koCode(data.scheduler.runtime_env_readiness),
      holidaySkipModeLabel: koCode(data.scheduler.holiday_skip_mode),
      notificationMethodLabel: `${koCode(alertDestination.mode)} · 목적지 ${alertDestination.target_configured ? "설정됨" : "미설정"} · 테스트 ${
        alertDestination.last_test_status === "passed" && alertDestination.test_recent ? "통과" : "미검증"
      }`,
      notificationNextActionLabel: operationCopy(alertDestination.next_action),
      notificationReadinessLabel: alertDestination.attention_required ? "보강 필요" : "외부 알림 검증됨",
      readProtectionLabel: `${koCode(productionApiServer.auth_mode)} · 읽기 토큰 ${
        productionApiServer.read_token_configured ? "설정됨" : "미설정"
      } · 허용 출처 ${productionApiServer.allowed_origin_configured ? "명시됨" : "미설정"}`,
      readScopeLabel: `${koCode(authRbac.read_role)} · 보호된 화면 ${authRbac.protected_paths.length.toLocaleString("ko-KR")}개 · 읽기 요청만 허용`,
      schedulerActivationAllowedLabel: schedulerActivation.activation_allowed ? "예" : "아니오",
      schedulerApprovalGateLabel: schedulerApprovalGateLabel(schedulerActivation.approval_gate),
      schedulerEnvironmentLabel: automationStateLabel(schedulerActivation),
      schedulerJobLabel: koCode(schedulerActivation.job_id),
      schedulerNextStepLabel: schedulerNextStepLabel(schedulerActivation),
      schedulerReadinessLabel: schedulerInstallLabel(data.scheduler.install_status),
    },
  };
  const executionHistoryRows: DataHealthExecutionHistoryRow[] = data.pipeline_runs.map((run) => ({
    cadenceLabel: koCode(run.cadence),
    domainLabel: koCode(run.domain),
    finishedAtLabel: run.finished_at,
    freshnessLabel: koCode(run.health_status),
    id: run.latest_run_id,
    latestRunLabel: executionIdLabel(run.latest_run_id),
    pipelineNameLabel: operationCopy(run.pipeline_name),
    statusLabel: koCode(run.latest_status),
    statusTone: statusRiskClass(run.latest_status),
  }));
  const automationDetailSection: DataHealthAutomationDetailSectionProps = {
    automationCards: automationCards.map((card) => ({
      cadenceLabel: cadenceLabel(card.run, card.fallbackCadence),
      description: card.description,
      detail: card.detail,
      finishedAtLabel: finishedAtLabel(card.run),
      stateLabel: runStateLabel(card.run),
      title: card.title,
    })),
    automationStatusLabel: automationStateLabel(schedulerActivation),
    localWorker: {
      cycleRows: localWorker.cycles.map((cycle) => ({
        artifactRunCountLabel: `${cycle.artifact_run_count}개 기록`,
        jobCountLabel: `${cycle.job_count}개 · 중단 ${cycle.failed_job_count}개`,
        smokeStatusLabel: koCode(cycle.smoke_status),
        startedAtLabel: cycle.started_at || "시각 없음",
        title: String(cycle.cycle_number),
      })),
      description: ec2SchedulerInstalled
        ? "이 기록은 서버 예약 실행기를 붙이기 전 로컬 MVP 단계의 점검 결과다. 현재 자동 실행 판단은 위의 서버 반복 실행기와 작업 실행 이력을 우선한다."
        : localWorkerExplanation(localWorker),
      eyebrow: ec2SchedulerInstalled ? "과거 로컬 워커 기록" : "최근 자동 실행 결과",
      factRows: [
        { label: "상태", value: koCode(localWorker.status) },
        { label: "실행 여부", value: localWorker.execute ? "실제 실행" : "미리보기" },
        { label: "생성 시각", value: localWorker.generated_at || "기록 없음" },
        {
          label: "완료 회차",
          value: `${localWorker.completed_cycle_count}/${localWorker.max_cycles || localWorker.completed_cycle_count}회`,
        },
        { label: "중단 회차", value: `${localWorker.failed_cycle_count}회` },
        { label: "오류 시 중단", value: localWorker.stop_on_failure ? "예" : "아니오" },
        {
          label: "대상 작업",
          value: localWorker.job_ids.length > 0
            ? localWorker.job_ids.map((jobId) => koCode(jobId)).join(" · ")
            : "연결된 작업 없음",
        },
        { label: "최신 수집 요약", value: summaryLocationLabel(localWorker.latest_smoke_output_path) },
        { label: "다음 조치", value: localWorkerNextAction(localWorker) },
      ],
      title: ec2SchedulerInstalled ? "현재 서버 자동화의 주 근거가 아니다" : localWorkerTitle(localWorker),
    },
    manualSmoke: {
      artifactRows: manualSmoke.artifact_runs.map((run) => ({
        errorLabel: errorLogLabel(run.stderr_path),
        exitCodeLabel: String(run.exit_code),
        jobLabel: koCode(run.job_id),
        pipelineLabel: operationCopy(run.pipeline_name),
        statusLabel: koCode(run.status),
      })),
      description: ec2SchedulerInstalled
        ? "이 기록은 수동으로 데이터 수집 경로를 검증했던 증거다. 현재 서버 운영 상태는 서버 반복 실행기와 최신 작업 실행 이력으로 판단한다."
        : manualSmokeExplanation(manualSmoke),
      eyebrow: ec2SchedulerInstalled ? "과거 수동 점검 증거" : "최근 수동 점검 증거",
      factRows: [
        { label: "상태", value: koCode(manualSmoke.status) },
        { label: "실행 여부", value: manualSmoke.execute ? "실제 실행" : "미리보기" },
        { label: "생성 시각", value: manualSmoke.generated_at || "기록 없음" },
        { label: "실행 환경 상태", value: manualSmoke.runtime_status ? koCode(manualSmoke.runtime_status) : "미확인" },
        {
          label: "대상 작업",
          value: manualSmoke.planned_job_ids.length > 0
            ? manualSmoke.planned_job_ids.map((jobId) => koCode(jobId)).join(" · ")
            : "연결된 작업 없음",
        },
        {
          label: "실행 기록",
          value: `${manualSmoke.artifact_runs.length}개 기록 · 중단 ${manualSmoke.failed_job_count}개`,
        },
        { label: "결과 위치", value: evidenceLocationLabel(manualSmoke.artifact_root) },
        { label: "다음 조치", value: manualSmokeNextAction(manualSmoke) },
      ],
      title: ec2SchedulerInstalled ? "자동 운영 전 수동 검증 기록" : manualSmokeTitle(manualSmoke),
    },
    newsAfterAnalysisSteps: newsAfterAnalysisSteps.map((step) => ({
      finishedAtLabel: finishedAtLabel(step.run),
      index: step.index,
      next: step.next,
      output: step.output,
      ownerLabel: koCode(step.owner),
      statusLabel: runStateLabel(step.run),
      title: step.title,
      warningLabel:
        step.run?.health_status === "degraded" || step.run?.latest_status === "succeeded_with_fallback"
          ? runQualityExplanation(step.run)
          : "",
    })),
    profileScheduler: {
      activeTimerSummaryLabel: `${profileScheduler.active_timer_count}/${profileScheduler.timer_count}개 예약 실행 활성`,
      timers: profileScheduler.timers.map((timer) => ({
        activeStateLabel: koCode(timer.active_state),
        lastResultLabel: koCode(timer.last_result || "unknown"),
        nextElapseLabel: timer.next_elapse || "미확인",
        profileLabel: koCode(timer.profile_id),
        scheduleLabel: timer.schedule || "스케줄 미확인",
      })),
    },
    schedulerDetail: {
      description: schedulerReadinessExplanation(data.scheduler),
      factRows: [
        { label: "승인 조건", value: schedulerApprovalGateLabel(schedulerActivation.approval_gate) },
        { label: "활성화 허용", value: schedulerActivation.activation_allowed ? "예" : "아니오" },
        { label: "반복 실행 상태", value: schedulerInstallLabel(schedulerActivation.scheduler_activation) },
        { label: "근거 생성 시각", value: schedulerActivation.generated_at || "미확인" },
        { label: "결과 위치", value: evidenceLocationLabel(data.scheduler.latest_artifact_root) },
        { label: "다음 조치", value: schedulerNextStepLabel(schedulerActivation) },
      ],
      title: schedulerReadinessTitle(data.scheduler),
    },
  };
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
