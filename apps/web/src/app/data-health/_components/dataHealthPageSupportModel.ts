import type { DataHealthRuntimeChip } from "@/components/operations/DataHealthRuntimeDetailPanels";
import type { DecisionMapStep } from "@/components/research/PageDecisionMap";
import { koCode } from "@/lib/korean-labels";

import {
  automationStateLabel,
  findPipelineRun,
  gateSeverityTone,
  liveAiInvocationTitle,
  openGateCopy,
  operationCopy,
  runStateLabel,
  tossMarketDataTitle,
  tossMarketDataTone,
} from "./dataHealthModel";
import type {
  ActiveRecommendationPriceFreshness,
  DataHealthData,
  GateTriageBucket,
  LiveAiInvocationHealth,
  OpenGateDetail,
  OutcomeMaturityWaitMonitor,
  PipelineRun,
  RecommendationOutcomeMaturity,
  SchedulerActivation,
  TossInvestMarketData,
} from "./dataHealthTypes";

export type DataHealthPageRuns = {
  readonly aiRun: PipelineRun | null;
  readonly crossAssetIndicatorRun: PipelineRun | null;
  readonly crossAssetRun: PipelineRun | null;
  readonly decisionRun: PipelineRun | null;
  readonly marketPriceRun: PipelineRun | null;
  readonly newsEnrichmentRun: PipelineRun | null;
  readonly newsRun: PipelineRun | null;
  readonly recommendationOutcomeRun: PipelineRun | null;
  readonly remediationRun: PipelineRun | null;
};

export type DataHealthTossBrokerSectionModel = {
  readonly cadenceCountLabel: string;
  readonly candleCountLabel: string;
  readonly comparisonLookbackLabel: string;
  readonly comparisonStatusLabel: string;
  readonly orderBoundaryLabel: string;
  readonly orderSubmitLabel: string;
  readonly requestedSymbolCountLabel: string;
  readonly syncStatusLabel: string;
  readonly syncStatusTone: "risk-low" | "risk-medium" | "risk-high";
  readonly title: string;
};

type DataHealthDecisionMapInput = {
  readonly data: DataHealthData;
  readonly activeRecommendationPriceFreshness: NonNullable<ActiveRecommendationPriceFreshness>;
  readonly dataHealthHeadline: string;
  readonly failedPipelines: number;
  readonly liveAiInvocationHealth: NonNullable<LiveAiInvocationHealth>;
  readonly outcomeMaturity: NonNullable<RecommendationOutcomeMaturity>;
  readonly overviewCollectionCount: number;
  readonly qualityAuditStatus: string;
  readonly schedulerActivation: SchedulerActivation;
};

export function buildDataHealthPageRuns(data: DataHealthData): DataHealthPageRuns {
  return {
    aiRun: findPipelineRun(data, "event-intelligence-weekly", "event_intelligence_llm_extract"),
    crossAssetIndicatorRun: findPipelineRun(
      data,
      "cross-asset-indicator-ingest-daily",
      "cross_asset_indicator_ingest",
    ),
    crossAssetRun: findPipelineRun(data, "cross-asset-regime-daily", "cross_asset_regime_snapshot"),
    decisionRun: findPipelineRun(data, "cycle-recommendation-weekly", "cycle_state_snapshot"),
    marketPriceRun: findPipelineRun(data, "market-price-daily", "market_price_upsert"),
    newsEnrichmentRun: findPipelineRun(
      data,
      "news-rss-enrichment-intraday",
      "news_rss_event_enrichment",
    ),
    newsRun: findPipelineRun(data, "news-rss-daily", "news_rss_upsert"),
    recommendationOutcomeRun: findPipelineRun(
      data,
      "recommendation-outcome-backfill-daily",
      "performance_outcome_schedule_bootstrap",
    ),
    remediationRun: findPipelineRun(
      data,
      "portfolio-remediation-daily",
      "portfolio_remediation_daily_automation",
    ),
  };
}

export function buildDataHealthOpenGateChips(
  data: DataHealthData,
  openGateDetails: readonly OpenGateDetail[],
): readonly DataHealthRuntimeChip[] {
  if (openGateDetails.length > 0) {
    return openGateDetails.map((gate) => ({
      key: gate.gate_id,
      label: gate.label,
      tone: gateSeverityTone(gate.severity),
    }));
  }
  return data.open_gates.map((gate) => ({
    key: gate,
    label: operationCopy(koCode(gate)).replaceAll("_", " "),
    tone: "risk-medium",
  }));
}

export function buildDataHealthTriageOverviewBuckets(
  visibleGateTriageBuckets: readonly GateTriageBucket[],
) {
  return visibleGateTriageBuckets.map((bucket) => ({
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
}

export function buildDataHealthDecisionMapSteps({
  data,
  activeRecommendationPriceFreshness,
  dataHealthHeadline,
  failedPipelines,
  liveAiInvocationHealth,
  outcomeMaturity,
  overviewCollectionCount,
  qualityAuditStatus,
  schedulerActivation,
}: DataHealthDecisionMapInput): readonly DecisionMapStep[] {
  return [
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
      status: `${overviewCollectionCount.toLocaleString("ko-KR")}개 영역`,
      title: "수집·분석 연결",
      tone: "ready",
    },
    {
      description: "중복, 오분류, 근거 없는 연결이 있는지 확인합니다.",
      href: "#quality-audit",
      label: "품질",
      status: koCode(qualityAuditStatus),
      title: "품질 감사",
      tone: qualityAuditStatus === "attention_required" ? "watch" : "ready",
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
  ];
}

export function buildDataHealthTossBrokerSection(
  tossMarketData: TossInvestMarketData,
): DataHealthTossBrokerSectionModel {
  return {
    cadenceCountLabel: `${Object.keys(tossMarketData.sync.collection_cadence).length.toLocaleString("ko-KR")}개`,
    candleCountLabel: `${tossMarketData.sync.candle_bar_count.toLocaleString("ko-KR")}개`,
    comparisonLookbackLabel: `${tossMarketData.provider_comparison.lookback_days}거래일 · 허용 ${tossMarketData.provider_comparison.max_diff_bps}bps`,
    comparisonStatusLabel: koCode(tossMarketData.provider_comparison.status),
    orderBoundaryLabel: koCode(tossMarketData.sync.order_boundary),
    orderSubmitLabel: tossMarketData.sync.broker_submit_allowed
      ? "증권사 주문 제출 가능"
      : "증권사 주문 제출 차단",
    requestedSymbolCountLabel: `${tossMarketData.sync.requested_symbol_count.toLocaleString("ko-KR")}개`,
    syncStatusLabel: koCode(tossMarketData.sync.status),
    syncStatusTone: tossMarketDataTone(tossMarketData),
    title: tossMarketDataTitle(tossMarketData),
  };
}
