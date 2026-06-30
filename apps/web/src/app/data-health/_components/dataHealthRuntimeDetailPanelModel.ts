import type {
  DataHealthRuntimeChip,
  DataHealthRuntimeDetailPanelsProps,
} from "@/components/operations/DataHealthRuntimeDetailPanels";
import { koCode } from "@/lib/korean-labels";

import {
  automationStateLabel,
  evidenceLocationLabel,
  gateSeverityTone,
  openGateCopy,
  operationCopy,
  orderBoundaryCopy,
  schedulerApprovalGateLabel,
  schedulerInstallLabel,
  schedulerNextStepLabel,
} from "./dataHealthModel";
import type {
  ActiveRecommendationPriceFreshness,
  AlertDestination,
  AuthRbac,
  DataHealthData,
  DataOperationsArtifactRunner,
  OpenGateDetail,
  ProductionApiServer,
  SchedulerActivation,
} from "./dataHealthTypes";

type DataHealthRuntimeDetailPanelInput = {
  readonly activeRecommendationPriceFreshness: NonNullable<ActiveRecommendationPriceFreshness>;
  readonly alertDestination: NonNullable<AlertDestination>;
  readonly artifactRunner: NonNullable<DataOperationsArtifactRunner>;
  readonly authRbac: NonNullable<AuthRbac>;
  readonly budgetUsage: number;
  readonly data: DataHealthData;
  readonly openGateChips: readonly DataHealthRuntimeChip[];
  readonly openGateDetails: readonly OpenGateDetail[];
  readonly productionApiServer: NonNullable<ProductionApiServer>;
  readonly providerBudget: DataHealthData["provider_budget"];
  readonly schedulerActivation: SchedulerActivation;
};

export function buildDataHealthRuntimeDetailPanels({
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
}: DataHealthRuntimeDetailPanelInput): DataHealthRuntimeDetailPanelsProps {
  return {
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
    providerBudget: {
      budgetDateLabel: providerBudget.budget_date,
      latestRunLabel: providerBudget.latest_run?.started_at ?? "오늘 실행 없음",
      statusLabel: koCode(providerBudget.status),
      usagePercent: budgetUsage,
      usedRequestCountLabel: `${providerBudget.used_request_count.toLocaleString("ko-KR")}회`,
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
}
