export type DataHealthRiskTone = "risk-low" | "risk-medium" | "risk-high";

export type DataHealthProviderBudgetPanel = {
  readonly budgetDateLabel: string;
  readonly latestRunLabel: string;
  readonly statusLabel: string;
  readonly usagePercent: number;
  readonly usedRequestCountLabel: string;
};

export type DataHealthStaleRecommendationSymbol = {
  readonly activeRecommendationCountLabel: string;
  readonly daysBehindLabel: string;
  readonly href: string;
  readonly latestTradeDateLabel: string;
  readonly statusLabel: string;
  readonly symbol: string;
};

export type DataHealthActiveRecommendationPriceFreshnessPanel = {
  readonly latestTradeDateLabel: string;
  readonly nextActionLabel: string;
  readonly orderBoundaryLabel: string;
  readonly staleSummaryLabel: string;
  readonly staleSymbols: readonly DataHealthStaleRecommendationSymbol[];
  readonly statusLabel: string;
  readonly statusTone: DataHealthRiskTone;
  readonly symbolCoverageLabel: string;
};

export type DataHealthOpenGateRuntimeCard = {
  readonly id: string;
  readonly label: string;
  readonly nextActionLabel: string;
  readonly orderBoundaryLabel: string;
  readonly statusLabel: string;
  readonly statusTone: DataHealthRiskTone;
  readonly summary: string;
  readonly typeLabel: string;
};

export type DataHealthRuntimeChip = {
  readonly key: string;
  readonly label: string;
  readonly tone: DataHealthRiskTone;
};

export type DataHealthFreshnessRow = {
  readonly datasetLabel: string;
  readonly valueLabel: string;
};

export type DataHealthOpenGateRuntimePanel = {
  readonly chips: readonly DataHealthRuntimeChip[];
  readonly freshnessRows: readonly DataHealthFreshnessRow[];
  readonly gates: readonly DataHealthOpenGateRuntimeCard[];
};

export type DataHealthRuntimeBoundaryPanel = {
  readonly apiNextActionLabel: string;
  readonly apiReadinessLabel: string;
  readonly artifactEvidenceLabel: string;
  readonly artifactLatestRootLabel: string;
  readonly artifactNextActionLabel: string;
  readonly artifactPolicyLabel: string;
  readonly authNextActionLabel: string;
  readonly authReadinessLabel: string;
  readonly brokerOrderLabel: string;
  readonly connectionLabel: string;
  readonly environmentLabel: string;
  readonly holidaySkipModeLabel: string;
  readonly notificationMethodLabel: string;
  readonly notificationNextActionLabel: string;
  readonly notificationReadinessLabel: string;
  readonly readProtectionLabel: string;
  readonly readScopeLabel: string;
  readonly schedulerActivationAllowedLabel: string;
  readonly schedulerApprovalGateLabel: string;
  readonly schedulerEnvironmentLabel: string;
  readonly schedulerJobLabel: string;
  readonly schedulerNextStepLabel: string;
  readonly schedulerReadinessLabel: string;
};

export type DataHealthRuntimeDetailPanelsProps = {
  readonly activeRecommendationPriceFreshness: DataHealthActiveRecommendationPriceFreshnessPanel;
  readonly openGates: DataHealthOpenGateRuntimePanel;
  readonly providerBudget: DataHealthProviderBudgetPanel;
  readonly runtimeBoundary: DataHealthRuntimeBoundaryPanel;
};
