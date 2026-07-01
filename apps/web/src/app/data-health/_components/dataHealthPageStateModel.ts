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
  buildGateTriageBuckets,
  buildSchedulerCadenceGroups,
  gateTriageSummary,
  isEc2ProfileSchedulerInstalled,
  liveAiInvocationTone,
  newsAiEvalTone,
  qualityAuditSampleGroups,
  qualityAuditTone,
} from "./dataHealthModel";
import { buildDataHealthPageRuns } from "./dataHealthPageSupportModel";
import type { DataHealthData } from "./dataHealthTypes";

export function buildDataHealthPageState(data: DataHealthData) {
  const providerBudget = data.provider_budget;
  const profileScheduler = data.scheduler.profile_scheduler ?? DEFAULT_PROFILE_SCHEDULER;
  const qualityAudit = data.cycle_ai_quality_audit ?? DEFAULT_CYCLE_AI_QUALITY_AUDIT;
  const newsAiEvalQuality = data.news_ai_eval_quality ?? DEFAULT_NEWS_AI_EVAL_QUALITY;
  const liveAiInvocationHealth = data.live_ai_invocation_health ?? DEFAULT_LIVE_AI_INVOCATION_HEALTH;
  const openGateDetails = data.open_gate_details ?? [];
  const gateTriageBuckets = buildGateTriageBuckets(openGateDetails);
  const runs = buildDataHealthPageRuns(data);
  const outcomeWaitMonitor =
    data.outcome_maturity_wait_monitor ?? DEFAULT_OUTCOME_MATURITY_WAIT_MONITOR;

  return {
    activeRecommendationPriceFreshness:
      data.active_recommendation_price_freshness ?? DEFAULT_ACTIVE_RECOMMENDATION_PRICE_FRESHNESS,
    alertDestination: data.alert_destination ?? DEFAULT_ALERT_DESTINATION,
    artifactRunner: data.data_operations_artifact_runner ?? DEFAULT_DATA_OPERATIONS_ARTIFACT_RUNNER,
    authRbac: data.auth_rbac ?? DEFAULT_AUTH_RBAC,
    benchmarkDriftQuality: data.benchmark_drift_quality ?? DEFAULT_BENCHMARK_DRIFT_QUALITY,
    budgetUsage: providerBudget.daily_budget > 0
      ? Math.round((providerBudget.used_request_count / providerBudget.daily_budget) * 100)
      : 0,
    dataQualityReady:
      qualityAuditTone(qualityAudit) === "risk-low"
      && newsAiEvalTone(newsAiEvalQuality) === "risk-low"
      && liveAiInvocationTone(liveAiInvocationHealth) === "risk-low",
    ec2SchedulerInstalled: isEc2ProfileSchedulerInstalled(data.scheduler),
    failedPipelines: data.pipeline_runs.filter((run) =>
      ["missing", "stale", "failed"].includes(run.health_status),
    ).length,
    gateTriageBuckets,
    gateTriageStatus: gateTriageSummary(gateTriageBuckets, data.open_gates.length),
    liveAiInvocationHealth,
    localWorker: data.local_ingest_worker ?? DEFAULT_LOCAL_WORKER,
    manualSmoke: data.manual_local_ingest_smoke ?? DEFAULT_MANUAL_SMOKE,
    newsAiEvalQuality,
    openAiProviderHealth: data.openai_provider_health ?? DEFAULT_OPENAI_PROVIDER_HEALTH,
    openGateDetails,
    outcomeCalibration: data.recommendation_outcome_calibration ?? DEFAULT_RECOMMENDATION_OUTCOME_CALIBRATION,
    outcomeDueActionRouter:
      data.recommendation_outcome_due_action_router ?? DEFAULT_RECOMMENDATION_OUTCOME_DUE_ACTION_ROUTER,
    outcomeMaturity: data.recommendation_outcome_maturity ?? DEFAULT_RECOMMENDATION_OUTCOME_MATURITY,
    outcomeWaitMonitor,
    portfolioReviewActionRouter:
      data.portfolio_review_feedback_action_router ?? DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_ACTION_ROUTER,
    portfolioReviewCadence:
      data.portfolio_review_feedback_cadence ?? DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_CADENCE,
    portfolioReviewCalibration:
      data.portfolio_review_feedback_calibration ?? DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_CALIBRATION,
    portfolioReviewFeedback:
      data.portfolio_review_decision_feedback ?? DEFAULT_PORTFOLIO_REVIEW_DECISION_FEEDBACK,
    portfolioReviewHistory:
      data.portfolio_review_decision_history ?? DEFAULT_PORTFOLIO_REVIEW_DECISION_HISTORY,
    productionApiServer: data.production_api_server ?? DEFAULT_PRODUCTION_API_SERVER,
    professionalDepth: data.professional_analysis_depth ?? DEFAULT_PROFESSIONAL_ANALYSIS_DEPTH,
    professionalNextAction:
      data.professional_analysis_next_action ?? DEFAULT_PROFESSIONAL_ANALYSIS_NEXT_ACTION,
    professionalQuality: data.professional_analysis_quality ?? DEFAULT_PROFESSIONAL_ANALYSIS_QUALITY,
    professionalRecommendationAudit:
      data.professional_recommendation_coverage_audit ?? DEFAULT_PROFESSIONAL_RECOMMENDATION_COVERAGE_AUDIT,
    professionalSourceGaps:
      data.professional_source_gap_prioritization ?? DEFAULT_PROFESSIONAL_SOURCE_GAP_PRIORITIZATION,
    profileScheduler,
    providerBudget,
    qualityAudit,
    qualityAuditSamples: qualityAuditSampleGroups(qualityAudit),
    runs,
    safeInvestmentBoundary:
      outcomeWaitMonitor.weight_review_blocked
      && !outcomeWaitMonitor.automatic_weight_change_allowed
      && !outcomeWaitMonitor.broker_submit_allowed,
    schedulerActivation: data.scheduler.activation,
    schedulerCadenceGroups: buildSchedulerCadenceGroups(profileScheduler.timers),
    tossMarketData: data.tossinvest_market_data,
    visibleGateTriageBuckets: gateTriageBuckets.filter((bucket) => bucket.gates.length > 0),
  };
}
